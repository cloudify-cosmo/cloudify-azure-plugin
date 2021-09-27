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
    resources.compute.VirtualMachineExtensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Virtual Machine Extension interface
"""

from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.compute.virtual_machine_extension \
    import VirtualMachineExtension


@operation(resumable=True)
@decorators.with_generate_name(VirtualMachineExtension)
@decorators.with_azure_resource(VirtualMachineExtension)
def create(ctx, resource_config, **_):
    """Uses an existing, or creates a new, Virtual Machine Extension"""
    # Create a resource (if necessary)
    ctx.logger.warn(
        'Azure customData implementation is dependent on '
        'Virtual Machine image support.')
    azure_config = ctx.node.properties.get('azure_config')
    if not azure_config.get("subscription_id"):
        azure_config = ctx.node.properties.get('client_config')
    else:
        ctx.logger.warn("azure_config is deprecated please use client_config, "
                        "in later version it will be removed")
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    vm_name = ctx.node.properties['virtual_machine_name']
    vm_extension_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
        'publisher': resource_config.get('publisher'),
        'virtual_machine_extension_type': resource_config.get('ext_type'),
        'type_handler_version': resource_config.get('typeHandlerVersion'),
        'settings': resource_config.get('settings'),
    }
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    vm_extension = VirtualMachineExtension(azure_config, ctx.logger,
                                           api_version)
    # clean empty values from params
    vm_extension_params = \
        utils.cleanup_empty_params(vm_extension_params)
    result = utils.handle_create(
        vm_extension,
        resource_group_name,
        name,
        vm_name,
        vm_extension_params)
    ctx.instance.runtime_properties['resource_group'] = resource_group_name
    ctx.instance.runtime_properties['virtual_machine'] = vm_name
    ctx.instance.runtime_properties['resource'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Virtual Machine Extension"""
    # Delete the resource
    azure_config = ctx.node.properties.get('azure_config')
    if not azure_config.get("subscription_id"):
        azure_config = ctx.node.properties.get('client_config')
    else:
        ctx.logger.warn("azure_config is deprecated please use client_config, "
                        "in later version it will be removed")
    resource_group_name = utils.get_resource_group(ctx)
    vm_name = ctx.instance.runtime_properties.get('virtual_machine')
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    vm_extension = VirtualMachineExtension(azure_config, ctx.logger,
                                           api_version)
    utils.handle_delete(ctx, vm_extension, resource_group_name, name, vm_name)
