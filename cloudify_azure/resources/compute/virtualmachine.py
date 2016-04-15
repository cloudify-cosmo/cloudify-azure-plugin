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

# Deep object copying
from copy import deepcopy
# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
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
    osdisk['name'] = osdisk.get('name') or \
        '{0}_osdisk'.format(ctx.node.properties.get('name'))
    # If no disk URI was specified, generate one
    if not osdisk.get('vhd', dict()).get('uri'):
        osdisk['vhd'] = {
            'uri': 'http://{0}.{1}/vhds/{2}.vhd'.format(
                utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA),
                'blob.core.windows.net',
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
            '{0}_datadisk_{1}'.format(ctx.node.properties.get('name'), idx)
        # If no disk URI was specified, generate one
        if not datadisk.get('vhd', dict()).get('uri'):
            datadisk['vhd'] = {
                'uri': 'http://{0}.{1}/vhds/{2}.vhd'.format(
                    utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA),
                    'blob.core.windows.net',
                    datadisk.get('name'))
            }
        # Fill in the blanks if the user didn't specify
        datadisk['lun'] = datadisk.get('lun', idx)
        datadisk['createOption'] = datadisk.get('createOption', 'Empty')
        datadisks.append(datadisk)
    return datadisks


@operation
def create(**_):
    '''Uses an existing, or creates a new, Virtual Machine'''
    res_cfg = utils.get_resource_config()
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
    network_profile = {
        'networkInterfaces': utils.get_rel_id_references(
            NetworkInterfaceCard,
            constants.REL_CONNECTED_TO_NIC
        )
    }
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

    # Create a resource (if necessary)
    utils.task_resource_create(
        VirtualMachine(),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': utils.dict_update(
                utils.get_resource_config(),
                {
                    'availabilitySet': utils.get_rel_id_reference(
                        AvailabilitySet,
                        constants.REL_CONNECTED_TO_AS),
                    'networkProfile': network_profile,
                    'storageProfile': storage_profile,
                    'osProfile': os_profile
                }
            )
        })


@operation
def configure(command_to_execute, file_uris, **_):
    '''Configures the resource'''
    os_family = ctx.node.properties.get('os_family', '').lower()
    if os_family == 'windows':
        # By default, this should enable WinRM HTTP (unencrypted)
        # This entire function can be overridden from the plugin
        utils.task_resource_create(
            VirtualMachineExtension(
                virtual_machine=ctx.node.properties.get('name')
            ),
            {
                'location': ctx.node.properties.get('location'),
                'tags': ctx.node.properties.get('tags'),
                'properties': {
                    'publisher': 'Microsoft.Compute',
                    'type': 'CustomScriptExtension',
                    'typeHandlerVersion': '1.4',
                    'settings': {
                        'fileUris': file_uris,
                        'commandToExecute': command_to_execute
                    }
                }
            })

    # Write the IP address to runtime properties for the agent
    # Get a reference to the NIC
    rel_nic = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONNECTED_TO_NIC)
    # No NIC? Exit and hope the user doesn't plan to install an agent
    if not rel_nic:
        return
    # Get the NIC data from the API directly (because of IPConfiguration)
    nic = NetworkInterfaceCard(_ctx=rel_nic.target)
    nic_data = nic.get(rel_nic.target.node.properties.get('name'))
    # Iterate over each IPConfiguration entry
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
            pubip = PublicIPAddress(_ctx=rel_nic.target)
            pubip.endpoint = '{0}{1}'.format(
                constants.CONN_API_ENDPOINT, pubip_id)
            pubip_data = pubip.get()
            if isinstance(pubip_data, dict):
                ctx.instance.runtime_properties['public_ip'] = \
                    pubip_data.get('properties', dict()).get('ipAddress')
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
        VirtualMachine())
