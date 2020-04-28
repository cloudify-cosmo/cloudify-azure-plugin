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
from uuid import uuid4
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import utils
from azure_sdk.resources.resource_group import ResourceGroup


def get_unique_name(resource_group, name):
    if not name:
        for _ in range(0, 15):
            name = "{0}".format(uuid4())
            try:
                result = resource_group.get(name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except CloudError:  # if exception that means name is not used
                return name
    else:
        return name


@operation(resumable=True)
def create(ctx, **_):
    """Uses an existing, or creates a new, Resource Group"""
    # Create a resource (if necessary)
    azure_config = ctx.node.properties.get('azure_config')
    name = utils.get_resource_name(ctx)
    resource_group_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags')
    }
    resource_group = ResourceGroup(azure_config, ctx.logger)
    # generate name if not provided
    name = get_unique_name(resource_group, name)
    ctx.instance.runtime_properties['name'] = name
    try:
        result = resource_group.get(name)
        if ctx.node.properties.get('use_external_resource', False):
            ctx.logger.info("Using external resource")
        else:
            ctx.logger.info("Resource with name {0} exists".format(name))
            return
    except CloudError:
        if ctx.node.properties.get('use_external_resource', False):
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing resource_group '{0}'.".format(name))
        else:
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
    name = ctx.instance.runtime_properties.get('name')
    resource_group = ResourceGroup(azure_config, ctx.logger)
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
