# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
    resources.compute.VirtualMachine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Virtual Machine interface
"""
import json
import base64

from uuid import uuid4
from copy import deepcopy
from msrestazure.azure_exceptions import CloudError

from cloudify import ctx as ctx_from_imports
from cloudify import compute
from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from cloudify_azure.resources.compute.virtualmachine.virtualmachine_utils \
    import check_if_configuration_changed
from cloudify_azure.resources.network.publicipaddress import PUBLIC_IP_PROPERTY
from azure_sdk.resources.network.public_ip_address import PublicIPAddress
from azure_sdk.resources.compute.virtual_machine import VirtualMachine
from azure_sdk.resources.compute.virtual_machine_extension \
    import VirtualMachineExtension
from azure_sdk.resources.network.network_interface_card import \
    NetworkInterfaceCard
from azure.mgmt.compute.models import (
    NetworkProfile,
    NetworkInterfaceReference)

PS_OPEN = '<powershell>'
PS_CLOSE = '</powershell>'


def build_osdisk_profile(ctx, usr_osdisk=None):
    """
        Creates a storageProfile::osDisk object for use when
        creating a Virtual Machine

    :param dict usr_osdisk: User-override data
    :returns: storageProfile::osDisk object
    :rtype: dict
    """
    osdisk = dict()
    if isinstance(usr_osdisk, dict):
        osdisk = deepcopy(usr_osdisk)
    # Generate disk name if one wasn't provided
    osdisk['name'] = osdisk.get('name') or utils.get_resource_name(ctx)
    # If no disk URI was specified, generate one
    # Unless this is a managedDisk.
    if not osdisk.get('vhd', dict()).get('uri') and \
            'managedDisk' not in osdisk:
        osdisk['vhd'] = {
            'uri': 'http://{0}.{1}/vhds/{2}.vhd'.format(
                utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA,
                                        _ctx=ctx),
                'blob.' + ctx.node.properties.get('storage_endpoint', ""),
                osdisk.get('name'))
        }
    # Fill in the blanks if the user didn't specify
    osdisk['caching'] = osdisk.get('caching', 'ReadWrite')
    osdisk['create_option'] = osdisk.get('createOption', 'FromImage')
    return osdisk


def build_datadisks_profile(ctx, usr_datadisks):
    """
        Creates a list of storageProfile::dataDisk objects for use when
        creating a Virtual Machine

    :param dict usr_datadisks: User data
    :returns: List of storageProfile::dataDisk objects
    :rtype: list
    """
    datadisks = list()
    if not usr_datadisks:
        return list()
    for idx, usr_datadisk in enumerate(usr_datadisks):
        datadisk = deepcopy(usr_datadisk)
        # Generate disk name if one wasn't provided
        datadisk['name'] = datadisk.get('name') or \
            '{0}-{1}'.format(utils.get_resource_name(ctx), idx)
        # If no disk URI was specified, generate one
        if not datadisk.get('vhd', dict()).get('uri'):
            datadisk['vhd'] = {
                'uri': 'http://{0}.{1}/vhds/{2}.vhd'.format(
                    utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA,
                                            _ctx=ctx),
                    'blob.' + ctx.node.properties.get('storage_endpoint', ""),
                    datadisk.get('name'))
            }
        # Fill in the blanks if the user didn't specify
        datadisk['lun'] = datadisk.get('lun', idx)
        datadisk['create_option'] = datadisk.get('createOption', 'Empty')
        datadisks.append(datadisk)
    return datadisks


def build_network_profile(ctx):
    """
        Creates a networkProfile object complete with
        a list of networkInterface objects

    :returns: networkProfile object
    :rtype: dict
    """
    network_interfaces = list()
    net_rels = utils.get_relationships_by_type(
        ctx.instance.relationships,
        constants.REL_CONNECTED_TO_NIC)
    ctx.logger.debug('net_rels: {0}'.format(
        [net_rel.target.node.id for net_rel in net_rels]))
    for net_rel in net_rels:
        # Get the NIC resource ID
        nic_id = net_rel.target.instance.runtime_properties.get("resource_id")
        primary = net_rel.target.node.properties.get('primary', False)
        network_interface = NetworkInterfaceReference(
            id=nic_id,
            primary=primary)
        if primary:
            network_interfaces.insert(0, network_interface)
        else:
            network_interfaces.append(network_interface)
    return NetworkProfile(network_interfaces=network_interfaces)


def extract_powershell_content(string_with_powershell):
    """We want to filter user data for powershell scripts.
    However, AWS EC2 allows only one segment that is Powershell.
    So we have to concat separate Powershell scripts into one.
    First we separate all Powershell scripts without their tags.
    Later we will add the tags back.
    """

    split_string = string_with_powershell.splitlines()

    if not split_string:
        return ''

    if split_string[0] == '#ps1_sysnative' or \
            split_string[0] == '#ps1_x86':
        split_string.pop(0)

    if PS_OPEN not in split_string:
        script_start = -1  # Because we join at +1.
    else:
        script_start = split_string.index(PS_OPEN)

    if PS_CLOSE not in split_string:
        script_end = len(split_string)
    else:
        script_end = split_string.index(PS_CLOSE)

    # Return everything between Powershell back as a string.
    return '\r\n'.join(split_string[script_start + 1:script_end])


def _handle_userdata(ctx, existing_userdata):

    if existing_userdata is None:
        existing_userdata = ''
    elif isinstance(existing_userdata, dict) or \
            isinstance(existing_userdata, list):
        existing_userdata = json.dumps(existing_userdata)
    else:
        existing_userdata = '{0}'.format(existing_userdata)

    install_agent_userdata = ctx.agent.init_script()
    os_family = ctx.node.properties['os_family']

    if not existing_userdata and not install_agent_userdata:
        return

    # Windows instances require no more than one
    # Powershell script, which must be surrounded by
    # Powershell tags.
    if install_agent_userdata and os_family == 'windows':

        # Get the powershell content from install_agent_userdata
        install_agent_userdata = \
            extract_powershell_content(install_agent_userdata)

        # Get the powershell content from existing_userdata
        # (If it exists.)
        existing_userdata_powershell = \
            extract_powershell_content(existing_userdata)

        # Combine the powershell content from two sources.
        install_agent_userdata = \
            '#ps1_sysnative\r\n{0}\r\n{1}\r\n{2}\r\n{3}\r\n'.format(
                PS_OPEN,
                existing_userdata_powershell,
                install_agent_userdata,
                PS_CLOSE)

        # Additional work on the existing_userdata.
        # Remove duplicate Powershell content.
        # Get rid of unnecessary newlines.
        existing_userdata = \
            existing_userdata.replace(
                existing_userdata_powershell,
                '').replace(
                    PS_OPEN,
                    '').replace(
                        PS_CLOSE,
                        '').strip()

    if not existing_userdata or existing_userdata.isspace():
        final_userdata = install_agent_userdata
    elif not install_agent_userdata:
        final_userdata = existing_userdata
    else:
        final_userdata = compute.create_multi_mimetype_userdata(
            [existing_userdata, install_agent_userdata])

    return final_userdata


def _create_or_update(ctx, args=None):
    """Uses an existing, or creates a new, Virtual Machine"""
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    virtual_machine = VirtualMachine(azure_config, ctx.logger, api_version)
    resource_create_payload = _get_vm_create_or_update_payload(ctx, args, name)
    _create_update_resource(resource_group_name,
                            name,
                            virtual_machine,
                            resource_create_payload)


def _get_vm_create_or_update_payload(ctx, args, name):
    res_cfg = ctx.node.properties.get("resource_config", {})
    spot_instance = res_cfg.pop("spot_instance", None)
    # Build storage profile
    osdisk = build_osdisk_profile(ctx, res_cfg.get(
        'storageProfile', dict()).get('osDisk', dict()))
    datadisks = build_datadisks_profile(ctx, res_cfg.get(
        'storageProfile', dict()).get('dataDisks', list()))
    storage_profile = {
        'os_disk': osdisk,
        'data_disks': datadisks
    }
    # Build the network profile
    network_profile = build_network_profile(ctx)
    # Build the OS profile
    os_family = ctx.node.properties.get('os_family', '').lower()
    os_profile = dict()
    # Set defaults for Windows installs to enable WinRM listener
    if os_family == 'windows' and \
            not res_cfg.get('osProfile', dict()).get('windowsConfiguration'):
        os_profile = {
            'windows_configuration': {
                # This is required for extension scripts to work
                'provision_vm_agent': True,
                'win_rm': {
                    'listeners': [{
                        'protocol': 'Http',
                        'certificate_url': None
                    }]
                }
            },
            'linux_configuration': None
        }
    elif not res_cfg.get('osProfile', dict()).get('linuxConfiguration'):
        os_profile = {
            'linux_configuration': {
                'disable_password_authentication': False
            },
            'windows_configuration': None
        }
    # Set the computerName if it's not set already
    os_profile['computer_name'] = \
        res_cfg.get('osProfile', dict()).get('computerName', name)

    availability_set = None
    rel_type = constants.REL_CONNECTED_TO_AS
    for rel in ctx.instance.relationships:
        if isinstance(rel_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_type):
                availability_set = {
                    'id': rel.target.instance.runtime_properties.get(
                        "resource_id")
                }
        else:
            if rel_type in rel.type_hierarchy:
                availability_set = {
                    'id': rel.target.instance.runtime_properties.get(
                        "resource_id")
                }
    resource_create_payload = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
        'plan': ctx.node.properties.get('plan'),
        'availabilitySet': availability_set,
        'networkProfile': network_profile,
        'storageProfile': storage_profile,
        'osProfile': os_profile
    }
    # check if spot_instance
    if spot_instance and spot_instance.get("is_spot_instance"):
        # this is just an indacator not part of the api
        spot_instance.pop("is_spot_instance")
        #  handle the params
        resource_create_payload = \
            utils.dict_update(resource_create_payload, spot_instance)
    resource_create_payload = \
        utils.handle_resource_config_params(resource_create_payload,
                                            utils.get_resource_config(
                                                _ctx=ctx,
                                                args=args))
    # support userdata from args.
    os_profile = resource_create_payload['os_profile']
    userdata = _handle_userdata(ctx, os_profile.get('custom_data'))
    if userdata:
        ctx.logger.warn(
            'Azure customData implementation is dependent on '
            'Virtual Machine image support.')
        resource_create_payload['os_profile']['custom_data'] = \
            base64.b64encode(userdata.encode('utf-8')).decode('utf-8')
    # Remove custom_data from os_profile if empty to avoid Errors.
    elif 'custom_data' in resource_create_payload['os_profile']:
        del resource_create_payload['os_profile']['custom_data']

    return resource_create_payload


def _create_update_resource(resource_group_name,
                            name,
                            vm_iface,
                            resource_create_payload):
    result = utils.handle_create(
        vm_iface,
        resource_group_name,
        name,
        additional_params=resource_create_payload)
    utils.save_common_info_in_runtime_properties(resource_group_name,
                                                 name,
                                                 result)


@operation(resumable=True)
@decorators.with_generate_name(VirtualMachine)
@decorators.with_azure_resource(VirtualMachine)
def create(ctx, args=None, **_):
    """Uses an existing, or creates a new, Virtual Machine"""
    _create_or_update(ctx, args)


@operation(resumable=True)
def configure(ctx, args=None, **_):
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    virtual_machine = VirtualMachine(azure_config, ctx.logger, api_version)
    payload = _get_vm_create_or_update_payload(ctx, args, name)
    ctx.logger.debug("create_payload: \n {payload}".format(payload=payload))
    current_vm = ctx.instance.runtime_properties["resource"]
    if check_if_configuration_changed(ctx, payload, current_vm):
        ctx.logger.info("configuration changed!!")
        _create_update_resource(resource_group_name,
                                name,
                                virtual_machine,
                                payload)


@operation(resumable=True)
def start(ctx, command_to_execute, file_uris, type_handler_version='1.8', **_):
    """Configures the resource"""
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    vm_name = utils.get_resource_name(ctx)
    os_family = ctx.node.properties.get('os_family', '').lower()
    if os_family == 'windows':
        vm_extension = VirtualMachineExtension(azure_config, ctx.logger)
        vm_extension_name = "{0}".format(uuid4())
        vm_extension_params = {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'publisher': 'Microsoft.Compute',
            'virtual_machine_extension_type': 'CustomScriptExtension',
            'type_handler_version': type_handler_version,
            'settings': {
                'fileUris': file_uris,
                'commandToExecute': command_to_execute
            }
        }
        # ctx.logger.info("sending {0}".format(vm_extension_params))
        try:
            result = \
                vm_extension.create_or_update(resource_group_name,
                                              vm_name, vm_extension_name,
                                              vm_extension_params)
        except CloudError as cr:
            raise cfy_exc.NonRecoverableError(
                "configure virtual_machine '{0}' "
                "failed with this error : {1}".format(vm_name, cr.message))

        ctx.instance.runtime_properties['resource_extension'] = result
        ctx.instance.runtime_properties['resource_extension_id'] = \
            result.get("id", "")
        ctx.instance.runtime_properties['extension_name'] = vm_extension_name

    # Write the IP address to runtime properties for the agent
    # Get a reference to the NIC
    rel_nics = utils.get_relationships_by_type(
        ctx.instance.relationships,
        constants.REL_CONNECTED_TO_NIC)
    ctx.logger.debug('net_rels: {0}'.format(
        [net_rel.target.node.id for net_rel in rel_nics]))

    # No NIC? Exit and hope the user doesn't plan to install an agent
    if rel_nics:
        vm_id = ctx.instance.runtime_properties.get("resource_id")

        public_ip_addresses = []
        for rel_nic in rel_nics:
            # Get the NIC data from the API directly
            # (because of IPConfiguration)
            nic_azure_config = utils.get_client_config(
                rel_nic.target.node.properties)
            nic_resource_group = utils.get_resource_group(rel_nic.target)
            nic_name = utils.get_resource_name(rel_nic.target)
            nic_iface = NetworkInterfaceCard(nic_azure_config, ctx.logger)
            nic_data = nic_iface.get(nic_resource_group, nic_name)
            nic_vm_id = nic_data.get('virtual_machine', {}).get('id')

            if not nic_vm_id:
                if not vm_id:
                    nic_data['virtual_machine'] = {
                        'id': utils.get_resource_id_from_name(
                            azure_config.get('subscription_id'),
                            resource_group_name,
                            'Microsoft.Compute',
                            'virtualMachines',
                            vm_name
                        )
                    }
                elif vm_id not in nic_vm_id:
                    nic_data['virtual_machine'] = {
                        'id': vm_id
                    }
                ctx.logger.info('nic_data {nic_data}'.format(
                    nic_data=nic_data))
                nic_data = nic_iface.create_or_update(nic_resource_group,
                                                      nic_name,
                                                      nic_data)
            # Iterate over each IPConfiguration entry
            for ip_cfg in nic_data.get('ip_configurations', list()):

                # Get the Private IP Address endpoint
                private_ip = ip_cfg.get('private_ip_address')
                ctx.instance.runtime_properties['ip'] = private_ip
                public_ip = ip_cfg.get('public_ip_address', {}).get(
                    'ip_address')
                if not public_ip:
                    azure_config = utils.get_client_config(ctx.node.properties)
                    resource_group_name = utils.get_resource_group(ctx)
                    pip = PublicIPAddress(azure_config, ctx.logger)
                    pip_cfg = ip_cfg.get('public_ip_address')
                    if pip_cfg:
                        pip_name = pip_cfg.get('id').rsplit('/', 1)[1]
                        public_ip_data = pip.get(resource_group_name, pip_name)
                        public_ip = public_ip_data.get("ip_address")
                if not public_ip:
                    # skip the public ip from this ip configuration
                    # as it is None
                    continue

                ctx.instance.runtime_properties['public_ip'] = public_ip
                # For consistency with other plugins.
                ctx.instance.runtime_properties[PUBLIC_IP_PROPERTY] = public_ip
                # We should also consider that maybe there will be many
                # public ip addresses.
                if public_ip not in public_ip_addresses:
                    public_ip_addresses.append(public_ip)
                ctx.instance.runtime_properties['public_ip_addresses'] = \
                    public_ip_addresses

    # if no public_ip default to private_ip
    public_ip = ctx.instance.runtime_properties.get('public_ip')
    if not public_ip:
        public_ip = ctx.instance.runtime_properties.get('ip')
        ctx.instance.runtime_properties['public_ip'] = public_ip

    # See if the user wants to use the public IP as primary IP
    if ctx.node.properties.get('use_public_ip') and \
            ctx.instance.runtime_properties.get('public_ip'):
        ctx.instance.runtime_properties['ip'] = \
            ctx.instance.runtime_properties.get('public_ip')
    ctx.logger.info('OUTPUT {0}.{1} = "{2}"'.format(
        ctx.instance.id,
        'ip',
        ctx.instance.runtime_properties.get('ip')))
    ctx.logger.info('OUTPUT {0}.{1} = "{2}"'.format(
        ctx.instance.id,
        'public_ip',
        ctx.instance.runtime_properties.get('public_ip')))

    # Start the VM
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    virtual_machine = VirtualMachine(azure_config, ctx.logger, api_version)
    if not get_instance_status(virtual_machine,
                               resource_group_name,
                               vm_name) == 'PowerState/running':
        virtual_machine.start(resource_group_name, vm_name)
        raise cfy_exc.OperationRetry('Waiting for PowerState/running status.')


def get_instance_status(virtual_machine, resource_group_name, vm_name):
    try:
        response = virtual_machine.get_instance_view(resource_group_name,
                                                     vm_name)
        return response['instance_view']['statuses'][-1]['code']
    except (KeyError, AttributeError) as e:
        ctx_from_imports.logger.info(str(e))
        raise cfy_exc.OperationRetry(
            'Improper status returned for Virtual Machine. {}'.format(str(e)))
    except CloudError:
        return


@operation(resumable=True)
def stop(ctx, **_):
    """Stops a Virtual Machine"""
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    virtual_machine = VirtualMachine(azure_config, ctx.logger, api_version)
    get_instance_status(
        virtual_machine, resource_group_name, name)
    # TODO: Stop the VM if it is already running.
    virtual_machine = VirtualMachine(azure_config, ctx.logger, api_version)
    status = get_instance_status(
        virtual_machine, resource_group_name, name)
    ctx.logger.info('VM {} status {}'.format(name, status))
    if status in ['PowerState/deallocated',
                  'PowerState/stopped'] or not status:
        ctx.logger.info('VM {} is in state {} (stopped)'.format(name, status))
        return
    elif status == 'PowerState/running':
        utils.handle_task(
            virtual_machine,
            resource_group_name,
            name,
            resource_task='power_off')
    raise cfy_exc.OperationRetry(
        'Waiting for {} PowerState/deallocated status.'.format(name))


@operation(resumable=True)
@decorators.with_azure_resource(VirtualMachine)
def delete(ctx, **_):
    """Deletes a Virtual Machine"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    virtual_machine = VirtualMachine(azure_config, ctx.logger, api_version)
    utils.handle_delete(
        ctx, virtual_machine, resource_group_name, name)
    get_instance_status(
        virtual_machine, resource_group_name, name)


@operation(resumable=True)
def attach_data_disk(ctx, lun, **_):
    """Attaches a data disk"""
    azure_config = utils.get_client_config(ctx.source.node.properties)
    api_version = \
        ctx.source.node.properties.get('api_version',
                                       constants.API_VER_COMPUTE)
    resource_group_name = utils.get_resource_group(ctx.source)
    name = ctx.source.instance.runtime_properties.get("name")
    vm_iface = VirtualMachine(azure_config, ctx.logger, api_version)
    vm_state = vm_iface.get(resource_group_name, name)
    data_disks = vm_state.get('storage_profile', dict()).get(
        'data_disks', list())
    # Get the createOption
    create_opt = 'Empty'
    if ctx.target.node.properties.get('use_external_resource', False):
        create_opt = 'Attach'
    # Add the disk to the list
    data_disks.append({
        'name': utils.get_resource_name(_ctx=ctx.target),
        'lun': lun,
        'disk_size_gb': ctx.target.instance.runtime_properties['diskSizeGB'],
        'vhd': {
            'uri': ctx.target.instance.runtime_properties['uri']
        },
        'create_option': create_opt,
        'caching': 'None'
    })
    # Update the VM
    vm_params = {
        'location': ctx.source.node.properties.get('location'),
        'storage_profile': {
            'data_disks': data_disks
        }
    }
    try:
        vm_iface.create_or_update(resource_group_name, name, vm_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "attach disk to virtual_machine '{0}' "
            "failed with this error : {1}".format(name, cr.message))


@operation(resumable=True)
def detach_data_disk(ctx, **_):
    """Detaches a data disk"""
    azure_config = utils.get_client_config(ctx.source.node.properties)
    api_version = \
        ctx.source.node.properties.get('api_version',
                                       constants.API_VER_COMPUTE)
    resource_group_name = utils.get_resource_group(ctx.source)
    name = ctx.source.instance.runtime_properties.get("name")
    vm_iface = VirtualMachine(azure_config, ctx.logger, api_version)
    vm_state = vm_iface.get(resource_group_name, name)
    data_disks = [
        x for x in vm_state.get('storage_profile', dict()).get(
            'data_disks', list())
        if x.get('vhd',
                 dict()
                 ).get('uri') != ctx.target.instance.runtime_properties['uri']]

    # Update the VM
    vm_params = {
        'location': ctx.source.node.properties.get('location'),
        'storage_profile': {
            'data_disks': data_disks
        }
    }
    try:
        vm_iface.create_or_update(resource_group_name, name, vm_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "detach disk from virtual_machine '{0}' "
            "failed with this error : {1}".format(name, cr.message))
