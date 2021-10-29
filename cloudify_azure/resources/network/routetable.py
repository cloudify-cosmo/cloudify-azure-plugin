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
    resources.network.RouteTable
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Route Table interface
"""

from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.network.route_table import RouteTable


@operation(resumable=True)
@decorators.with_generate_name(RouteTable)
@decorators.with_azure_resource(RouteTable)
def create(ctx, **_):
    """Uses an existing, or creates a new, Route Table"""
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    rtbl_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
    }
    rtbl_params = \
        utils.handle_resource_config_params(rtbl_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    route_table = RouteTable(azure_config, ctx.logger, api_version)
    # clean empty values from params
    rtbl_params = \
        utils.cleanup_empty_params(rtbl_params)
    result = utils.handle_create(
        route_table, resource_group_name, name, additional_params=rtbl_params)
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
@decorators.with_azure_resource(RouteTable)
def delete(ctx, **_):
    """Deletes a Route Table"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    route_table = RouteTable(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, route_table, resource_group_name, name)
