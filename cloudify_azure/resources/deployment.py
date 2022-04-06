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
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.resource.resources.models import DeploymentMode

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from cloudify_azure._compat import (urlopen, urlparse, text_type)
from azure_sdk.resources.deployment import Deployment
from azure_sdk.resources.resource_group import ResourceGroup

STATE = 'state'
IS_DRIFTED = 'is_drifted'


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
def update(ctx, *params, **kwargs):
    resource_group_name, deployment_name, api_version = \
        get_resource_group_name_deployment_name_and_api_version(ctx)

    deployment = Deployment.get(resource_group_name, deployment_name)

    if deployment:
        utils.handle_task(resource=deployment,
                          resource_group_name=resource_group_name,
                          name=deployment_name,
                          resource_task='create_or_update',
                          additional_params=params,
                          **kwargs)
    else:
        raise cfy_exc.NonRecoverableError(
            "ARM Deployment {} not found. "
            "Unable to update.".format(deployment_name))


@operation(resumable=True)
@decorators.with_generate_name(Deployment)
@decorators.with_azure_resource(Deployment)
def create(ctx, **kwargs):
    azure_config = utils.get_client_config(ctx.node.properties)
    deployment_name, resource_group_name, api_version = \
        get_resource_group_name_deployment_name_and_api_version(ctx)
    resource_group_params = {
        'location': ctx.node.properties.get('location'),
    }
    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    try:
        if resource_group.get(resource_group_name):
            ctx.instance.runtime_properties['__CREATED_RESOURCE_GROUP'] = False
    except ResourceNotFoundError:
        ctx.logger.info('ERROR WAS RAISED!!!!!')
        result = utils.handle_create(resource_group,
                                     resource_group_name,
                                     additional_params=resource_group_params)
        if result:
            ctx.instance.runtime_properties['__CREATED_RESOURCE_GROUP'] = True

    # load template
    properties, params = get_properties_and_formated_params(ctx, **kwargs)
    template = get_template(ctx, properties)
    ctx.logger.debug("Parsed template: %s", json.dumps(template, indent=4))
    deployment = Deployment(azure_config, ctx.logger, api_version)
    deployment_params = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': params
    }

    try:
        result = \
            deployment.create_or_update(
                resource_group_name,
                deployment_name,
                deployment_params,
                properties.get('timeout'))
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create deployment '{0}' "
            "failed with this error : {1}".format(deployment_name, cr.message))

    ctx.instance.runtime_properties['template'] = template
    ctx.instance.runtime_properties['resource'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get('id', '')
    ctx.instance.runtime_properties['outputs'] = \
        result.get('properties', {}).get('outputs')


@operation(resumable=True)
@decorators.with_azure_resource(Deployment)
def delete(ctx, **_):
    if ctx.node.properties.get('use_external_resource', False):
        return
    deployment_name, resource_group_name, api_version = \
        get_resource_group_name_deployment_name_and_api_version(ctx)
    azure_config = utils.get_client_config(ctx.node.properties)
    if ctx.instance.runtime_properties['__CREATED_RESOURCE_GROUP']:
        resource_group = ResourceGroup(azure_config, ctx.logger)
        utils.handle_delete(ctx, resource_group, resource_group_name)
    else:
        deployment = Deployment(azure_config, ctx.logger)
        try:
            deployment.delete(resource_group_name, deployment_name)
            ctx.logger.debug("if the resource group was not deleted. "
                             "some resource might have not been deleted, "
                             "they need to be deleted manually.")
        except ResourceNotFoundError:
            ctx.logger.debug("Resource group '{0}' or deployment '{1}' "
                             "could not be found"
                             .format(resource_group_name, deployment_name))


@operation(resumable=True)
def pull(ctx, **kwargs):
    azure_config = utils.get_client_config(ctx.node.properties)
    deployment_name, resource_group_name, api_version = \
        get_resource_group_name_deployment_name_and_api_version(ctx)

    resource_group = ResourceGroup(azure_config, ctx.logger, api_version)
    try:
        resource_group.get(resource_group_name)
    except CloudError:
        ctx.logger.info("Resource group {rg_name} does not exist. State will "
                        "be empty.".format(rg_name=resource_group_name))
        ctx.instance.runtime_properties[STATE] = []
        ctx.instance.runtime_properties[IS_DRIFTED] = True
        return

    # Get the resources list that crated during the template run.
    initial_resources = ctx.instance.runtime_properties.get(
        'resource', {}).get('properties', {}).get('output_resources', [])
    ctx.logger.debug("initial_resources: {}".format(initial_resources))
    actual_resources = resource_group.list_resources(resource_group_name)

    deployment = Deployment(azure_config, ctx.logger)
    properties, params = get_properties_and_formated_params(ctx, **kwargs)
    template = ctx.instance.runtime_properties.get('template') or get_template(
        ctx, properties)
    # some resources are nested like subnets so they do not appear in
    # actual_resources. We will search them using the what-if result.

    what_if_res = execute_what_if(deployment,
                                  resource_group_name,
                                  deployment_name,
                                  template,
                                  params)
    calculate_state(ctx, initial_resources, actual_resources, what_if_res)


def get_properties_and_formated_params(ctx, **kwargs):
    properties = {}
    properties.update(ctx.node.properties)
    properties.update(kwargs)
    params = format_params(properties.get('params', {}))
    return properties, params


def get_resource_group_name_deployment_name_and_api_version(ctx):
    # deployment_name = ctx.node.properties.get('name')
    # resource_group_name = utils.get_resource_name(ctx)
    deployment_name = utils.get_resource_name(ctx)
    resource_group_name = ctx.node.properties.get(
         'resource_group_name', deployment_name)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_RESOURCES)
    return deployment_name, resource_group_name, api_version


def execute_what_if(deployment,
                    resource_group_name,
                    deployment_name,
                    template,
                    params):
    what_if_properties = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': params
    }
    try:
        return deployment.what_if(resource_group_name,
                                  deployment_name,
                                  what_if_properties)
    except CloudError:
        raise cfy_exc.NonRecoverableError(
            "What if operation on deployment {dep_name} failed. Can't "
            "calculate accurate state.".format(dep_name=deployment_name))


def calculate_state(ctx, initial_resources, actual_resources, what_if_res):
    """
    Create a list of live resources of the deployment.
    Save this list in the state runtime property.
    :param initial_resources: list of resources id`s created by the deployment.
    :param actual_resources: list of resources id`s that exists in resource
    group.
    :param: result of what-if operation in order to indicate resources that
    not appear in actual_resources.
    """
    state = []
    initial_ids = [resource['id'] for resource in initial_resources]
    actual_ids = [resource['id'] for resource in actual_resources]
    for resource_id in initial_ids:
        if resource_id not in actual_ids and not\
                check_if_resource_alive_in_what_if_result(resource_id,
                                                          what_if_res):
            ctx.logger.debug("Resource {resource} not exists, deployment is "
                             "drifted.".format(resource=resource_id))
            continue
        state.append(resource_id)

    ctx.instance.runtime_properties[STATE] = state
    ctx.instance.runtime_properties[IS_DRIFTED] = \
        False if state == initial_ids else True


def check_if_resource_alive_in_what_if_result(resource_id, what_if_result):
    """
    Given resource id and what-if operation result,
    check if the resource is alive using the what-if operation result.
    The change types of the what-if operation described here:

    https://docs.microsoft.com/en-us/azure/azure-resource-manager/templates/
    template-deploy-what-if?tabs=azure-powershell#change-types

    """
    status = what_if_result.get('status')
    if status != 'Succeeded':
        raise cfy_exc.NonRecoverableError(
            "Can't detect resource {resource_id} status from what_if "
            "operation result because the status of what if operation result "
            "is {status}.".format(resource_id=resource_id, status=status))

    for change in what_if_result.get('changes', []):
        if resource_id == change.get('resource_id') and change.get(
                'change_type') != 'Create':
            # Resource is alive.
            return True

    return False
