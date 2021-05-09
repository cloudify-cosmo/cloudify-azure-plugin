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

from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, utils)
from cloudify_azure.decorators import with_azure_resource
from azure_sdk.resources.app_service.web_app import WebApp


@operation(resumable=True)
@with_azure_resource(WebApp)
def create(ctx, resource_group, name, app_config, **kwargs):
    azure_config = utils.get_client_config(ctx.node.properties)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_APP_SERVICE)
    web_app = WebApp(azure_config, ctx.logger, api_version)

    try:
        result = \
             web_app.create_or_update(resource_group, name, app_config)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create web_app '{0} failed with this error : "
            "{1}".format(name, cr.message)
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
    web_app = WebApp(azure_config, ctx.logger, api_version)
    try:
        web_app.get(resource_group, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        web_app.delete(resource_group, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete web_app '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
