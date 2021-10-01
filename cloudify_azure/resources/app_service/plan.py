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

from cloudify.decorators import operation

from cloudify_azure import (constants, utils)
from cloudify_azure.decorators import with_azure_resource
from azure_sdk.resources.app_service.plan import ServicePlan


@operation(resumable=True)
@with_azure_resource(ServicePlan)
def create(ctx, resource_group, name, plan_details, **kwargs):
    azure_config = utils.get_client_config(ctx.node.properties)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_APP_SERVICE)
    plan = ServicePlan(azure_config, ctx.logger, api_version)
    result = utils.handle_create(
        plan,
        resource_group,
        name,
        additional_params=plan_details)
    utils.save_common_info_in_runtime_properties(resource_group,
                                                 name,
                                                 result)


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_APP_SERVICE)
    plan = ServicePlan(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, plan, resource_group, name)
