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
    resources.network.Route
    ~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Route interface
"""

from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.network.route import Route


@operation(resumable=True)
@decorators.with_generate_name(Route)
@decorators.with_azure_resource(Route)
def create(ctx, **_):
    """Uses an existing, or creates a new, Route"""
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    route_table_name = utils.get_route_table(ctx)
    route_params = {}
    route_params = \
        utils.handle_resource_config_params(route_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    route = Route(azure_config, ctx.logger, api_version)
    # clean empty values from params
    route_params = \
        utils.cleanup_empty_params(route_params)
    result = utils.handle_create(
        route, resource_group_name, name, route_table_name, route_params)

    ctx.instance.runtime_properties['route_table'] = route_table_name
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
@decorators.with_azure_resource(Route)
def delete(ctx, **_):
    """Deletes a Route"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    route_table_name = ctx.instance.runtime_properties.get('route_table')
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    route = Route(azure_config, ctx.logger, api_version)
    utils.handle_delete(
        ctx, route, resource_group_name, name, route_table_name)
