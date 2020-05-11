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
import json

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.resource.resources.models import DeploymentMode

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from cloudify_azure._compat import (urlopen, urlparse, text_type)
from azure_sdk.resources.deployment import Deployment
from azure_sdk.resources.resource_group import ResourceGroup


def is_url(string):
    parse_info = urlparse('{0}'.format(string))
    return parse_info.scheme and (parse_info.netloc or parse_info.path)


def format_params(params):
    if not isinstance(params, dict):
        return params
    for k, v in params.items():
        params[k] = {"value": v}
    return params


def get_template(ctx, properties):
    template = properties.get('template')
    if template:
        template = template if not isinstance(template, bytes) \
            else template.decode('utf-8')
        if isinstance(template, text_type):
            ctx.logger.info("Template provided as a string in blueprint")
            ctx.logger.debug("Template string: %s", template)
            template = json.loads(template)
        elif not isinstance(template, dict):
            raise cfy_exc.NonRecoverableError(
                "Provided template is neither a string nor a dict "
                "(type: {0}, value: {1})".format(
                    type(template), repr(template)))
    else:
        template = properties.get('template_file')
        if template is None:
            raise cfy_exc.NonRecoverableError(
                "Deployment template not provided. Please specify "
                "either 'template' or 'template_file'."
            )
        ctx.logger.info("Template file provided: %s", template)
        if is_url(template):
            f = urlopen(template)
            try:
                template = json.load(f)
            finally:
                f.close()
        else:
            template = ctx.get_resource(template)
            template = json.loads(template)
    return template


@operation(resumable=True)
@decorators.with_generate_name(ResourceGroup)
@decorators.with_azure_resource(ResourceGroup)
def create(ctx, **kwargs):

    azure_config = ctx.node.properties.get('azure_config')
    if not azure_config.get("subscription_id"):
        azure_config = ctx.node.properties.get('client_config')
    else:
        ctx.logger.warn("azure_config is deprecated please use client_config, "
                        "in later version it will be removed")
    name = utils.get_resource_name(ctx)
    resource_group_params = {
        'location': ctx.node.properties.get('location'),
    }
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_RESOURCES)
    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    try:
        resource_group.create_or_update(name, resource_group_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create deployment resource_group '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )

    # load template
    properties = {}
    properties.update(ctx.node.properties)
    properties.update(kwargs)
    template = get_template(ctx, properties)
    ctx.logger.debug("Parsed template: %s", json.dumps(template, indent=4))

    deployment = Deployment(azure_config, ctx.logger, api_version)
    deployment_params = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': format_params(properties.get('params', {}))
    }

    try:
        result = \
            deployment.create_or_update(name, name, deployment_params,
                                        properties.get('timeout'))
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create deployment '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )

    ctx.instance.runtime_properties['resouce'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")
    ctx.instance.runtime_properties['outputs'] = \
        result.get("properties", {}).get("outputs")


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = ctx.node.properties.get('azure_config')
    if not azure_config.get("subscription_id"):
        azure_config = ctx.node.properties.get('client_config')
    else:
        ctx.logger.warn("azure_config is deprecated please use client_config, "
                        "in later version it will be removed")
    name = utils.get_resource_name(ctx)
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
            "delete deployment resource_group '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
