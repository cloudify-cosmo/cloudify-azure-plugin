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
    resources.ResourceGroup
    ~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Resource Group interface
"""
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.resource_group import ResourceGroup


@operation(resumable=True)
@decorators.with_generate_name(ResourceGroup)
@decorators.with_azure_resource(ResourceGroup)
def create(ctx, **_):
    """Uses an existing, or creates a new, Resource Group"""
    ctx.logger.info('Not Props: {}'.format(ctx.node.properties))
    azure_config = utils.get_client_config(ctx.node.properties)
    ctx.logger.info('Azure Config: {}'.format(azure_config))
    name = utils.get_resource_name(ctx)
    resource_group_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags')
    }
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_RESOURCES)
    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    result = utils.handle_create(
        resource_group, name, additional_params=resource_group_params)
    ctx.instance.runtime_properties['resource'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
@decorators.with_azure_resource(ResourceGroup)
def delete(ctx, **_):
    """Deletes a Resource Group"""
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_RESOURCES)
    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, resource_group, name)
