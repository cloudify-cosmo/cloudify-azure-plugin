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
    resources.compute.VirtualMachineExtensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Virtual Machine Extension interface
'''

# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
# Logger, API version
from cloudify_azure import (constants, utils)


class VirtualMachineExtension(Resource):
    '''
        Microsoft Azure Virtual Machine Extension interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string virtual_machine: Name of the parent Virtual Machine
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 virtual_machine=None,
                 api_version=constants.API_VER_COMPUTE,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        virtual_machine = virtual_machine or \
            utils.get_rel_node_name(constants.REL_VMX_CONTAINED_IN_VM)
        Resource.__init__(
            self,
            'Virtual Machine Extension',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Compute',
                'virtualMachines/{0}'.format(virtual_machine),
                'extensions'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


@operation
def create(resource_config, **_):
    '''Uses an existing, or creates a new, Virtual Machine Extension'''
    # Work around for the reserved "type" name
    props = resource_config
    if 'ext_type' in props:
        props['type'] = props['ext_type']
        del props['ext_type']
    # Create a resource (if necessary)
    utils.task_resource_create(
        VirtualMachineExtension(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_COMPUTE)),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': props
        })


@operation
def delete(**_):
    '''Deletes a Virtual Machine Extension'''
    # Delete the resource
    utils.task_resource_delete(
        VirtualMachineExtension(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_COMPUTE)))
