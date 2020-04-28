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
from uuid import uuid4
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import utils
from azure_sdk.resources.network.subnet import Subnet


def get_unique_name(subnet, resource_group_name, vnet_name, name):
    if not name:
        for _ in range(0, 15):
            name = "{0}".format(uuid4())
            try:
                result = subnet.get(resource_group_name, vnet_name, name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except CloudError:  # if exception that means name is not used
                return name
    else:
        return name


@operation(resumable=True)
def create(ctx, **_):
    """Uses an existing, or creates a new, Subnet"""
    # Create a resource (if necessary)
    azure_config = ctx.node.properties.get('azure_config')
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    vnet_name = utils.get_virtual_network(ctx)
    subnet_params = {}
    subnet_params = \
        utils.handle_resource_config_params(subnet_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    subnet = Subnet(azure_config, ctx.logger)
    # generate name if not provided
    name = get_unique_name(subnet, resource_group_name, vnet_name, name)
    ctx.instance.runtime_properties['name'] = name
    # clean empty values from params
    subnet_params = \
        utils.cleanup_empty_params(subnet_params)
    try:
        result = subnet.get(resource_group_name, vnet_name, name)
        if ctx.node.properties.get('use_external_resource', False):
            ctx.logger.info("Using external resource")
        else:
            ctx.logger.info("Resource with name {0} exists".format(name))
            return
    except CloudError:
        if ctx.node.properties.get('use_external_resource', False):
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing subnet '{0}'.".format(name))
        else:
            try:
                result = \
                    subnet.create_or_update(resource_group_name,
                                            vnet_name,
                                            name,
                                            subnet_params)
            except CloudError as cr:
                raise cfy_exc.NonRecoverableError(
                    "create subnet '{0}' "
                    "failed with this error : {1}".format(name,
                                                          cr.message)
                    )

    ctx.instance.runtime_properties['resource_group'] = resource_group_name
    ctx.instance.runtime_properties['virtual_network'] = vnet_name
    ctx.instance.runtime_properties['resouce'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Subnet"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = ctx.node.properties.get('azure_config')
    resource_group_name = ctx.instance.runtime_properties.get('resource_group')
    vnet_name = ctx.instance.runtime_properties.get('virtual_network')
    name = ctx.instance.runtime_properties.get('name')
    subnet = Subnet(azure_config, ctx.logger)
    try:
        subnet.get(resource_group_name, vnet_name, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        subnet.delete(resource_group_name, vnet_name, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete subnet '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def attach_network_security_group(ctx, **_):
    """Attaches a Network Security Group (source) to the Subnet (target)"""
    nsg_id = ctx.source.instance.runtime_properties.get("resource_id", "")
    # Attach
    azure_config = ctx.target.node.properties['azure_config']
    resource_group_name = \
        ctx.target.instance.runtime_properties.get('resource_group')
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = {
        'network_security_group': {'id': nsg_id}
    }
    subnet = Subnet(azure_config, ctx.logger)
    try:
        subnet.create_or_update(resource_group_name,
                                vnet_name,
                                name,
                                subnet_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "attach_network_security_group to subnet '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def detach_network_security_group(ctx, **_):
    """Detaches a Network Security Group to the Subnet"""
    # Detach
    azure_config = ctx.target.node.properties['azure_config']
    resource_group_name = \
        ctx.target.instance.runtime_properties.get('resource_group')
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = {
        'network_security_group': None
    }
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
    azure_config = ctx.target.node.properties['azure_config']
    resource_group_name = \
        ctx.target.instance.runtime_properties.get('resource_group')
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = {
        'route_table': {
            'id': rtbl_id
        }
    }
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
    azure_config = ctx.target.node.properties['azure_config']
    resource_group_name = \
        ctx.target.instance.runtime_properties.get('resource_group')
    vnet_name = ctx.target.instance.runtime_properties.get('virtual_network')
    name = ctx.target.instance.runtime_properties.get('name')
    subnet_params = {
        'route_table': None
    }
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
