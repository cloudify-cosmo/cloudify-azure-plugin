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
from uuid import uuid4
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import utils
from azure_sdk.resources.network.network_security_group \
    import NetworkSecurityGroup


def get_unique_name(network_security_group, resource_group_name, name):
    if not name:
        for _ in range(0, 15):
            name = "{0}".format(uuid4())
            try:
                result = network_security_group.get(resource_group_name, name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except CloudError:  # if exception that means name is not used
                return name
    else:
        return name


@operation(resumable=True)
def create(ctx, **_):
    """Uses an existing, or creates a new, Network Security Group"""
    # Create a resource (if necessary)
    azure_config = ctx.node.properties.get('azure_config')
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
    network_security_group = NetworkSecurityGroup(azure_config, ctx.logger)
    # generate name if not provided
    name = get_unique_name(network_security_group, resource_group_name, name)
    ctx.instance.runtime_properties['name'] = name
    # clean empty values from params
    nsg_params = \
        utils.cleanup_empty_params(nsg_params)
    try:
        result = network_security_group.get(resource_group_name, name)
        if ctx.node.properties.get('use_external_resource', False):
            ctx.logger.info("Using external resource")
        else:
            ctx.logger.info("Resource with name {0} exists".format(name))
            return
    except CloudError:
        if ctx.node.properties.get('use_external_resource', False):
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing network_security_group '{0}'.".format(
                    name))
        else:
            try:
                result = \
                    network_security_group.create_or_update(
                        resource_group_name,
                        name,
                        nsg_params)
            except CloudError as cr:
                raise cfy_exc.NonRecoverableError(
                    "create network_security_group '{0}' "
                    "failed with this error : {1}".format(name,
                                                          cr.message)
                    )

    ctx.instance.runtime_properties['resource_group'] = resource_group_name
    ctx.instance.runtime_properties['resouce'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Network Security Group"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = ctx.node.properties.get('azure_config')
    resource_group_name = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    network_security_group = NetworkSecurityGroup(azure_config, ctx.logger)
    try:
        network_security_group.get(resource_group_name, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        network_security_group.delete(resource_group_name, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete network_security_group '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
