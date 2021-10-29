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
    resources.network.NetworkSecurityGroup
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Network Security Group interface
"""

from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.network.network_security_group \
    import NetworkSecurityGroup


@operation(resumable=True)
@decorators.with_generate_name(NetworkSecurityGroup)
@decorators.with_azure_resource(NetworkSecurityGroup)
def create(ctx, **_):
    """Uses an existing, or creates a new, Network Security Group"""
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    nsg_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
    }
    nsg_params = \
        utils.handle_resource_config_params(nsg_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_security_group = NetworkSecurityGroup(azure_config, ctx.logger,
                                                  api_version)
    # clean empty values from params
    nsg_params = \
        utils.cleanup_empty_params(nsg_params)
    result = utils.handle_create(
        network_security_group,
        resource_group_name,
        name,
        additional_params=nsg_params)
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
@decorators.with_azure_resource(NetworkSecurityGroup)
def delete(ctx, **_):
    """Deletes a Network Security Group"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_security_group = NetworkSecurityGroup(azure_config, ctx.logger,
                                                  api_version)
    utils.handle_delete(ctx, network_security_group, resource_group_name, name)
