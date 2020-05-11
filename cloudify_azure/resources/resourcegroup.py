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
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.resource_group import ResourceGroup


@operation(resumable=True)
@decorators.with_generate_name(ResourceGroup)
@decorators.with_azure_resource(ResourceGroup)
def create(ctx, **_):
    """Uses an existing, or creates a new, Resource Group"""
    azure_config = ctx.node.properties.get('azure_config')
    if not azure_config.get("subscription_id"):
        azure_config = ctx.node.properties.get('client_config')
    else:
        ctx.logger.warn("azure_config is deprecated please use client_config, "
                        "in later version it will be removed")
    name = utils.get_resource_name(ctx)
    resource_group_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags')
    }
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_RESOURCES)
    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    try:
        result = \
            resource_group.create_or_update(
                name,
                resource_group_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create resource_group '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )

    ctx.instance.runtime_properties['resouce'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Resource Group"""
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = ctx.node.properties.get('azure_config')
    if not azure_config.get("subscription_id"):
        azure_config = ctx.node.properties.get('client_config')
    else:
        ctx.logger.warn("azure_config is deprecated please use client_config, "
                        "in later version it will be removed")
    name = utils.get_resource_name(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_RESOURCES)
    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    try:
        resource_group.get(name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        resource_group.delete(name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete resource_group '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
