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
    resources.compute.AvailabilitySet
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Availability Set interface
"""
from uuid import uuid4

from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, utils)
from azure_sdk.resources.compute.availability_set import AvailabilitySet


def get_unique_name(availability_set, resource_group_name, name):
    if not name:
        for _ in range(0, 15):
            name = "{0}".format(uuid4())
            try:
                result = availability_set.get(resource_group_name, name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except CloudError:  # if exception that means name is not used
                return name
    else:
        return name


@operation(resumable=True)
def create(ctx, **_):
    """Uses an existing, or creates a new, Availability Set"""
    azure_config = ctx.node.properties.get('azure_config')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    resource_config = ctx.node.properties.get('resource_config')
    availability_set_conf = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
    }
    availability_set_conf = \
        utils.handle_resource_config_params(availability_set_conf,
                                            resource_config)
    availability_set = AvailabilitySet(azure_config, ctx.logger, api_version)
    # generate name if not provided
    name = get_unique_name(availability_set, resource_group_name, name)
    ctx.instance.runtime_properties['name'] = name
    # clean empty values from params
    availability_set_conf = utils.cleanup_empty_params(availability_set_conf)
    try:
        result = availability_set.get(resource_group_name, name)
        if ctx.node.properties.get('use_external_resource', False):
            ctx.logger.info("Using external resource")
        else:
            ctx.logger.info("Resource with name {0} exists".format(name))
            return
    except CloudError:
        if ctx.node.properties.get('use_external_resource', False):
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing availability_set '{0}'.".format(name))
        else:
            try:
                result = \
                    availability_set.create_or_update(resource_group_name,
                                                      name,
                                                      availability_set_conf)
            except CloudError as cr:
                raise cfy_exc.NonRecoverableError(
                    "create availability_set '{0}' "
                    "failed with this error : {1}".format(name,
                                                          cr.message)
                    )

    ctx.instance.runtime_properties['resource_group'] = resource_group_name
    ctx.instance.runtime_properties['resouce'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Availability Set"""
    if ctx.node.properties.get('use_external_resource', False):
        return
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    azure_config = ctx.node.properties.get('azure_config')
    resource_group_name = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    availability_set = AvailabilitySet(azure_config, ctx.logger, api_version)
    try:
        availability_set.get(resource_group_name, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        availability_set.delete(resource_group_name, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete availability_set '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
