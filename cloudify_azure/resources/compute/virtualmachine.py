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
    cloudify_azure.resources.compute.virtualmachine
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Virtual Machine interface
'''

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


@operation
def create(**_):
    '''Uses an existing, or creates a new, Virtual Machine'''
    # Build storage profile
    storage_profile = {
        'osDisk': {
            'name': 'osdisk',
            'vhd': {
                'uri': 'http://{0}.{1}/vhds/osdisk.vhd'.format(
                    utils.get_rel_node_name(constants.REL_CONNECTED_TO_SA),
                    'blob.core.windows.net')
            },
            'caching': 'ReadWrite',
            'createOption': 'FromImage'
        }
    }
    # Build the network profile
    network_profile = {
        'networkInterfaces': utils.get_rel_id_references(
            NetworkInterfaceCard,
            constants.REL_VM_CONNECTED_TO_NIC
        )
    }
    # Build the OS profile
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
        }
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
def configure(ps_entry, ps_urls, **_):
    '''Configures the resource'''
    # Use a Virtual Machine Extension to enable WinRM HTTP (unencrypted)
    # This entire function can be overridden from the plugin
    command_to_exec = 'powershell -ExecutionPolicy Unrestricted ' \
                      '-file {0}'.format(ps_entry)
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
                    'fileUris': ps_urls,
                    'commandToExecute': command_to_exec
                }
            }
        })


@operation
def delete(**_):
    '''Deletes a Virtual Machine'''
    # Delete the resource
    utils.task_resource_delete(
        VirtualMachine())
