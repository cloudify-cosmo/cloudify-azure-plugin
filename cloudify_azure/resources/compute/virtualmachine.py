# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
'''
    resources.compute.VirtualMachine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Virtual Machine interface
'''

import base64
import json
# Deep object copying
from copy import deepcopy
# Random string
from uuid import uuid4
# Node properties and logger
from cloudify import compute
from cloudify import ctx
# Exception handling
from cloudify.exceptions import NonRecoverableError
# Life-cycle operation decorator
from cloudify.decorators import operation
# Base resource class
from cloudify_azure.resources.base import Resource
# Logger, API version
from cloudify_azure import (constants, utils)
# Relationship interfaces
from cloudify_azure.resources.network.networkinterfacecard \
    import NetworkInterfaceCard
from cloudify_azure.resources.network.publicipaddress \
    import PublicIPAddress
from cloudify_azure.resources.compute.availabilityset \
    import AvailabilitySet
from cloudify_azure.resources.compute.virtualmachineextension \
    import VirtualMachineExtension

PS_OPEN = '<powershell>'
PS_CLOSE = '</powershell>'


class VirtualMachine(Resource):
    '''
        Microsoft Azure Virtual Machine interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 api_version=constants.API_VER_COMPUTE,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        Resource.__init__(
            self,
            'Virtual Machine',
            '/{0}/{1}/{2}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Compute',
                'virtualMachines'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


def build_osdisk_profile(usr_osdisk=None):
    '''
        Creates a storageProfile::osDisk object for use when
        creating a Virtual Machine

    :param dict usr_osdisk: User-override data
    :returns: storageProfile::osDisk object
    :rtype: dict
    '''
    osdisk = dict()
    if isinstance(usr_osdisk, dict):
        osdisk = deepcopy(usr_osdisk)
    # Generate disk name if one wasn't provided
    osdisk['name'] = osdisk.get('name') or utils.get_resource_name()
    # If no disk URI was specified, generate one
    if not osdisk.get('vhd', dict()).get('uri'):
        osdisk['vhd'] = {
            'uri': 'http://{0}.{1}/vhds/{2}.vhd'.format(
                utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA),
                'blob.' + ctx.node.properties['storage_endpoint'],
                osdisk.get('name'))
        }
    # Fill in the blanks if the user didn't specify
    osdisk['caching'] = osdisk.get('caching', 'ReadWrite')
    osdisk['createOption'] = osdisk.get('createOption', 'FromImage')
    return osdisk


def build_datadisks_profile(usr_datadisks):
    '''
        Creates a list of storageProfile::dataDisk objects for use when
        creating a Virtual Machine

    :param dict usr_datadisks: User data
    :returns: List of storageProfile::dataDisk objects
    :rtype: list
    '''
    datadisks = list()
    if not usr_datadisks:
        return list()
    for idx, usr_datadisk in enumerate(usr_datadisks):
        datadisk = deepcopy(usr_datadisk)
        # Generate disk name if one wasn't provided
        datadisk['name'] = datadisk.get('name') or \
            '{0}-{1}'.format(utils.get_resource_name(), idx)
        # If no disk URI was specified, generate one
        if not datadisk.get('vhd', dict()).get('uri'):
            datadisk['vhd'] = {
                'uri': 'http://{0}.{1}/vhds/{2}.vhd'.format(
                    utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA),
                    'blob.' + ctx.node.properties['storage_endpoint'],
                    datadisk.get('name'))
            }
        # Fill in the blanks if the user didn't specify
        datadisk['lun'] = datadisk.get('lun', idx)
        datadisk['createOption'] = datadisk.get('createOption', 'Empty')
        datadisks.append(datadisk)
    return datadisks


def build_network_profile():
    '''
        Creates a networkProfile object complete with
        a list of networkInterface objects

    :returns: networkProfile object
    :rtype: dict
    '''
    network_interfaces = list()
    net_rels = utils.get_relationships_by_type(
        ctx.instance.relationships,
        constants.REL_CONNECTED_TO_NIC)
    ctx.logger.debug('net_rels: {0}'.format(
        [net_rel.target.node.id for net_rel in net_rels]))
    for net_rel in net_rels:
        # Get the NIC resource ID
        network_interface = utils.get_full_id_reference(
            NetworkInterfaceCard,
            _ctx=net_rel.target)
        # If more than one NIC is attached, set the Primary property
        if len(net_rels) > 1:
            network_interface['properties'] = {
                'primary': net_rel.target.node.properties.get('primary')
            }
        network_interfaces.append(network_interface)
    # Check for a primary interface if multiple NICs are used
    if len(network_interfaces) > 1:
        if not len([
                x for x in network_interfaces
                if x['properties']['primary']]):
            raise NonRecoverableError(
                'Exactly one "primary" network interface must be specified '
                'if multiple NetworkInterfaceCard nodes are used')
    return {
        'networkInterfaces': network_interfaces
    }


def vm_name_generator():
    '''Generates a unique VM resource name'''
    return str(uuid4())


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
    return '\n'.join(split_string[script_start+1:script_end])


def _handle_userdata(existing_userdata):

    if existing_userdata is None:
        existing_userdata = ''
    elif isinstance(existing_userdata, dict) or \
            isinstance(existing_userdata, list):
        existing_userdata = json.dumps(existing_userdata)
    elif not isinstance(existing_userdata, basestring):
        existing_userdata = str(existing_userdata)

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
            '#ps1_sysnative\n{0}\n{1}\n{2}\n{3}\n'.format(
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


@operation
def create(args=None, **_):
    '''Uses an existing, or creates a new, Virtual Machine'''
    # Generate a resource name (if needed)
    utils.generate_resource_name(
        VirtualMachine(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_COMPUTE)),
        generator=vm_name_generator)
    res_cfg = utils.get_resource_config(args=args) or dict()
    # Build storage profile
    osdisk = build_osdisk_profile(
        res_cfg.get('storageProfile', dict()).get('osDisk', dict()))
    datadisks = build_datadisks_profile(
        res_cfg.get('storageProfile', dict()).get('dataDisks', list()))
    storage_profile = {
        'osDisk': osdisk,
        'dataDisks': datadisks
    }
    # Build the network profile
    network_profile = build_network_profile()
    # Build the OS profile
    os_family = ctx.node.properties.get('os_family', '').lower()
    os_profile = dict()
    # Set defaults for Windows installs to enable WinRM listener
    if os_family == 'windows' and \
            not res_cfg.get('osProfile', dict()).get('windowsConfiguration'):
        os_profile = {
            'windowsConfiguration': {
                # This is required for extension scripts to work
                'provisionVMAgent': True,
                'winRM': {
                    'listeners': [{
                        'protocol': 'Http',
                        'certificateUrl': None
                    }]
                }
            },
            'linuxConfiguration': None
        }
    elif not res_cfg.get('osProfile', dict()).get('linuxConfiguration'):
        os_profile = {
            'linuxConfiguration': {
                'disablePasswordAuthentication': False
            },
            'windowsConfiguration': None
        }
    # Set the computerName if it's not set already
    os_profile['computerName'] = \
        res_cfg.get(
            'osProfile', dict()
        ).get('computerName', utils.get_resource_name())

    resource_create_payload = \
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'plan': ctx.node.properties.get('plan'),
            'properties': utils.dict_update(
                utils.get_resource_config(args=args),
                {
                    'availabilitySet': utils.get_rel_id_reference(
                        AvailabilitySet,
                        constants.REL_CONNECTED_TO_AS),
                    'networkProfile': network_profile,
                    'storageProfile': storage_profile,
                    'osProfile': os_profile
                }
            )
        }
    # support userdata from args.
    os_profile = resource_create_payload['properties']['osProfile']
    userdata = _handle_userdata(os_profile.get('customData'))
    if userdata:
        os_profile['customData'] = base64.b64encode(userdata.encode())
    # Remove customData from osProfile if empty to avoid 400 Error.
    elif 'customData' in resource_create_payload['properties']['osProfile']:
        del resource_create_payload['properties']['osProfile']['customData']
    # Create a resource (if necessary)
    utils.task_resource_create(VirtualMachine(
        api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_COMPUTE)),
        resource_create_payload)


@operation
def configure(command_to_execute, file_uris, type_handler_version='v2.0', **_):
    '''Configures the resource'''
    os_family = ctx.node.properties.get('os_family', '').lower()
    if os_family == 'windows':
        utils.task_resource_create(
            VirtualMachineExtension(
                virtual_machine=utils.get_resource_name(),
                api_version=ctx.node.properties.get('api_version',
                                                    constants.API_VER_COMPUTE)
            ),
            {
                'location': ctx.node.properties.get('location'),
                'tags': ctx.node.properties.get('tags'),
                'properties': {
                    'publisher': 'Microsoft.Compute',
                    'type': 'CustomScriptExtension',
                    'typeHandlerVersion': type_handler_version,
                    'settings': {
                        'fileUris': file_uris,
                        'commandToExecute': command_to_execute
                    }
                }
            })

    virtual_machine_name = ctx.instance.runtime_properties.get('name')
    virtual_machine_iface = \
        VirtualMachine(
            api_version=ctx.node.properties.get(
                'api_version',
                constants.API_VER_COMPUTE)).get(
                    name=virtual_machine_name)

    # Write the IP address to runtime properties for the agent
    # Get a reference to the NIC
    rel_nics = utils.get_relationships_by_type(
        ctx.instance.relationships,
        constants.REL_CONNECTED_TO_NIC)

    # No NIC? Exit and hope the user doesn't plan to install an agent
    if not rel_nics:
        return

    for rel_nic in rel_nics:
        # Get the NIC data from the API directly (because of IPConfiguration)
        nic_iface = NetworkInterfaceCard(
            _ctx=rel_nic.target,
            api_version=rel_nic.target.node.properties.get(
                'api_version',
                constants.API_VER_NETWORK))
        nic_name = utils.get_resource_name(rel_nic.target)
        nic_data = nic_iface.get(nic_name)
        nic_virtual_machine_id = nic_data.get(
            'properties', dict()).get(
                'virtualMachine', dict()).get('id')

        if virtual_machine_name not in nic_virtual_machine_id:
            nic_data['properties'] = \
                utils.dict_update(
                    nic_data.get('properties', {}),
                    {
                        'virtualMachine': {
                            'id': virtual_machine_iface.get('id')
                        }
                    }
                )
            utils.task_resource_update(
                nic_iface, nic_data, _ctx=rel_nic.target)
            nic_data = nic_iface.get(nic_name)
            if virtual_machine_name not in nic_data.get(
                    'properties', dict()).get(
                        'virtualMachine', dict()).get('id', str()):
                return ctx.operation.retry(
                    message='Waiting for NIC {0} to '
                            'attach to VM {1}..'
                            .format(nic_name,
                                    virtual_machine_name),
                    retry_after=10)

        # Iterate over each IPConfiguration entry
        creds = utils.get_credentials(_ctx=ctx)
        for ip_cfg in nic_data.get(
                'properties', dict()).get(
                    'ipConfigurations', list()):

            # Get the Private IP Address endpoint
            ctx.instance.runtime_properties['ip'] = \
                ip_cfg.get('properties', dict()).get('privateIPAddress')

            # Get the Public IP Address endpoint
            pubip_id = ip_cfg.get(
                'properties', dict()).get(
                    'publicIPAddress', dict()).get('id')
            if isinstance(pubip_id, basestring):
                # use the ID to get the data on the public ip
                pubip = PublicIPAddress(
                    _ctx=rel_nic.target,
                    api_version=rel_nic.target.node.properties.get(
                        'api_version',
                        constants.API_VER_NETWORK))
                pubip.endpoint = '{0}{1}'.format(
                    creds.endpoints_resource_manager, pubip_id)
                pubip_data = pubip.get()
                if isinstance(pubip_data, dict):
                    public_ip = \
                        pubip_data.get('properties', dict()).get('ipAddress')
                    # Maintained for backwards compatibility.
                    ctx.instance.runtime_properties['public_ip'] = \
                        public_ip
                    # For consistency with other plugins.
                    ctx.instance.runtime_properties['public_ip_address'] = \
                        public_ip
                    # We should also consider that maybe there will be many
                    # public ip addresses.
                    public_ip_addresses = \
                        ctx.instance.runtime_properties.get(
                            'public_ip_address', [])
                    if public_ip not in public_ip_addresses:
                        public_ip_addresses.append(public_ip)
                    ctx.instance.runtime_properties['public_ip_address'] = \
                        public_ip_addresses

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


@operation
def delete(**_):
    '''Deletes a Virtual Machine'''
    # Delete the resource
    utils.task_resource_delete(
        VirtualMachine(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_COMPUTE)))
    for prop in ['public_ip', 'public_ip_address', 'ip',
                 'name', 'async_op', 'public_ip_address']:
        try:
            del ctx.instance.runtime_properties[prop]
        except KeyError:
            pass


@operation
def attach_data_disk(lun, **_):
    '''Attaches a data disk'''
    vm_iface = VirtualMachine(_ctx=ctx.source,
                              api_version=ctx.source.node.properties.get(
                                    'api_version', constants.API_VER_COMPUTE))
    vm_state = vm_iface.get(name=utils.get_resource_name(_ctx=ctx.source))
    data_disks = vm_state.get(
        'properties', dict()).get(
            'storageProfile', dict()).get(
                'dataDisks', list())
    # Get the createOption
    create_opt = 'Empty'
    if ctx.target.node.properties.get('use_external_resource', False):
        create_opt = 'Attach'
    # Add the disk to the list
    data_disks.append({
        'name': utils.get_resource_name(_ctx=ctx.target),
        'lun': lun,
        'diskSizeGB': ctx.target.instance.runtime_properties['diskSizeGB'],
        'vhd': {
            'uri': ctx.target.instance.runtime_properties['uri']
        },
        'createOption': create_opt,
        'caching': 'None'
    })
    ctx.logger.info('async_op: {0}'.format(
        ctx.source.instance.runtime_properties.get('async_op')))
    # Update the VM
    utils.task_resource_update(
        VirtualMachine(_ctx=ctx.source,
                       api_version=ctx.source.node.properties.get(
                            'api_version', constants.API_VER_COMPUTE)),
        {
            'location': ctx.source.node.properties.get('location'),
            'properties': {
                'storageProfile': {
                    'dataDisks': data_disks
                }
            }
        },
        force=True,
        _ctx=ctx.source
    )


@operation
def detach_data_disk(**_):
    '''Detaches a data disk'''
    vm_iface = VirtualMachine(_ctx=ctx.source,
                              api_version=ctx.source.node.properties.get(
                                'api_version', constants.API_VER_COMPUTE))
    vm_state = vm_iface.get(name=utils.get_resource_name(_ctx=ctx.source))
    data_disks = [
        x for x in vm_state.get(
            'properties', dict()).get(
                'storageProfile', dict()).get(
                    'dataDisks', list())
        if x.get('vhd', dict()).get('uri') !=
        ctx.target.instance.runtime_properties['uri']
    ]
    ctx.logger.info('async_op: {0}'.format(
        ctx.source.instance.runtime_properties.get('async_op')))
    # Update the VM
    utils.task_resource_update(
        VirtualMachine(_ctx=ctx.source,
                       api_version=ctx.source.node.properties.get(
                            'api_version', constants.API_VER_COMPUTE)),
        {
            'location': ctx.source.node.properties.get('location'),
            'properties': {
                'storageProfile': {
                    'dataDisks': data_disks
                }
            }
        },
        force=True,
        _ctx=ctx.source
    )
