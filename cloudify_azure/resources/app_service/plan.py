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

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation
from msrestazure.azure_exceptions import CloudError

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

    try:
        result = \
            plan.create_or_update(resource_group, name, plan_details)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create plan '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
                    )
    ctx.instance.runtime_properties['resource_group'] = resource_group
    ctx.instance.runtime_properties['resource'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")
    ctx.instance.runtime_properties['name'] = name


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
    try:
        plan.get(resource_group, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        plan.delete(resource_group, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete plan '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
