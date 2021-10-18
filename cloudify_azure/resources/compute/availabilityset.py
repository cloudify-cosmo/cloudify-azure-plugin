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

from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.compute.availability_set import AvailabilitySet


@operation(resumable=True)
@decorators.with_generate_name(AvailabilitySet)
@decorators.with_azure_resource(AvailabilitySet)
def create(ctx, **_):
    """Uses an existing, or creates a new, Availability Set"""
    azure_config = utils.get_client_config(ctx.node.properties)
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
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    availability_set = AvailabilitySet(azure_config, ctx.logger, api_version)
    # clean empty values from params
    availability_set_conf = utils.cleanup_empty_params(availability_set_conf)
    result = utils.handle_create(
        availability_set,
        resource_group_name,
        name,
        additional_params=availability_set_conf)
    utils.save_common_info_in_runtime_properties(resource_group_name,
                                                 name,
                                                 result)


@operation(resumable=True)
@decorators.with_azure_resource(AvailabilitySet)
def delete(ctx, **_):
    """Deletes a Availability Set"""
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = utils.get_resource_name(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_COMPUTE)
    availability_set = AvailabilitySet(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, availability_set, resource_group_name, name)
