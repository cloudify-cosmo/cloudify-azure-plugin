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
    resources.network.Subnet
    ~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Subnet interface
"""
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.network.subnet import Subnet


@operation(resumable=True)
@decorators.with_generate_name(Subnet)
@decorators.with_azure_resource(Subnet)
def create(ctx, **_):
    """Uses an existing, or creates a new, Subnet"""
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    vnet_name = utils.get_virtual_network(ctx)
    subnet_params = {}
    subnet_params = \
        utils.handle_resource_config_params(subnet_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    subnet = Subnet(azure_config, ctx.logger, api_version)
    # clean empty values from params
    subnet_params = \
        utils.cleanup_empty_params(subnet_params)
    result = utils.handle_create(
        subnet, resource_group_name, name, vnet_name, subnet_params)
    ctx.instance.runtime_properties['virtual_network'] = vnet_name
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Subnet"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    vnet_name = ctx.instance.runtime_properties.get('virtual_network')
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    subnet = Subnet(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, subnet, resource_group_name, name, vnet_name)


@operation(resumable=True)
def attach_network_security_group(ctx, **_):
    """Attaches a Network Security Group (source) to the Subnet (target)"""
    nsg_id = ctx.source.instance.runtime_properties.get("resource_id", "")
    # Attach
    azure_config = utils.get_client_config(ctx.target.node.properties)
    resource_group_name = utils.get_resource_group(ctx.target)
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = \
        utils.handle_resource_config_params({},
                                            ctx.target.node.properties.get(
                                                'resource_config', {}))
    subnet_params.update({
        'network_security_group': {'id': nsg_id}
    })
    subnet = Subnet(azure_config, ctx.logger)
    utils.handle_create(
        subnet, resource_group_name, name, vnet_name, subnet_params)


@operation(resumable=True)
def detach_network_security_group(ctx, **_):
    """Detaches a Network Security Group to the Subnet"""
    # Detach
    azure_config = utils.get_client_config(ctx.target.node.properties)
    resource_group_name = utils.get_resource_group(ctx.target)
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = \
        utils.handle_resource_config_params({},
                                            ctx.target.node.properties.get(
                                                'resource_config', {}))
    subnet_params.update({
        'network_security_group': None
    })
    subnet = Subnet(azure_config, ctx.logger)
    try:
        subnet.create_or_update(resource_group_name,
                                vnet_name,
                                name,
                                subnet_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "detach_network_security_group from subnet '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def attach_route_table(ctx, **_):
    """Attaches a Route Table (source) to the Subnet (target)"""
    rtbl_id = ctx.source.instance.runtime_properties.get("resource_id", "")
    # Attach
    azure_config = utils.get_client_config(ctx.target.node.properties)
    resource_group_name = utils.get_resource_group(ctx.target)
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = \
        utils.handle_resource_config_params({},
                                            ctx.target.node.properties.get(
                                                'resource_config', {}))
    subnet_params.update({
        'route_table': {
            'id': rtbl_id
        }
    })
    subnet = Subnet(azure_config, ctx.logger)
    try:
        subnet.create_or_update(resource_group_name,
                                vnet_name,
                                name,
                                subnet_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "attach_route_table to subnet '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def detach_route_table(ctx, **_):
    """Detaches a Route Table to the Subnet"""
    # Detach
    azure_config = utils.get_client_config(ctx.target.node.properties)
    resource_group_name = utils.get_resource_group(ctx.target)
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = \
        utils.handle_resource_config_params({},
                                            ctx.target.node.properties.get(
                                                'resource_config', {}))
    subnet_params.update({
        'route_table': None
    })
    subnet = Subnet(azure_config, ctx.logger)
    try:
        subnet.create_or_update(resource_group_name,
                                vnet_name,
                                name,
                                subnet_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "detach_route_table from subnet '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
