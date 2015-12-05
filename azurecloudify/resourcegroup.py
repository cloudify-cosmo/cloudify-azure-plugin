########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
import requests
import json
import constants
import utils
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import auth
import azurerequests


@operation
def creation_validation(**_):
    for property_key in constants.RESOURCE_GROUP_REQUIRED_PROPERTIES:
        utils.validate_node_properties(property_key, ctx.node.properties)


@operation
def create_resource_group(**_):
    resource_group_name = utils.set_resource_name(_get_resource_group_name, 'Resource group',
                                                  constants.RESOURCE_GROUP_KEY, constants.EXISTING_RESOURCE_GROUP_KEY,
                                                  constants.RESOURCE_GROUP_PREFIX)
    if resource_group_name is None:
        # Using an existing resource group, so don't create anything
        return constants.ACCEPTED_STATUS_CODE

    headers, location, subscription_id = auth.get_credentials()

    resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group

    ctx.logger.info("Creating a new Resource group: {}".format(resource_group_name))
    resource_group_params = json.dumps({"name": resource_group_name, "location": location})
    response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=headers)
    ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = resource_group_name
    return response_rg.status_code


@operation
def verify_provision(start_retry_interval, **kwargs):

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the resource group ({0}) to be provisioned'.format(resource_group_name),
            retry_after=start_retry_interval)


@operation
def delete_resource_group(start_retry_interval=30, **kwargs):
    status_code = delete_current_resource_group(start_retry_interval, **kwargs)
    utils.clear_runtime_properties()
    return status_code


def delete_current_resource_group(start_retry_interval=30, **kwargs):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing resource group was used, so there's no need to delete")
        return constants.ACCEPTED_STATUS_CODE

    ctx.instance.runtime_properties[constants.RESOURCE_NOT_DELETED] = True
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    try:
        ctx.logger.info("Deleting Resource Group: {0}".format(resource_group_name))
        resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group
        response_rg = requests.delete(url=resource_group_url, headers=headers)
        return azurerequests.check_delete_response(response_rg, start_retry_interval,
                                                   'delete_current_resource_group', resource_group_name,
                                                   'resource_group_name')

    except:
        ctx.logger.info("Resource Group {0} could not be deleted.".format(resource_group_name))
    return constants.FAILURE_CODE


def _get_resource_group_name(resource_group_name):
    ctx.logger.info("In _get_resource_group_name looking for {0}".format(resource_group_name))
    credentials = 'Bearer ' + auth.get_auth_token()
    ctx.logger.info("In _get_resource_group_name credentials is {0}".format(credentials))
    headers, location, subscription_id = auth.get_credentials()
    list_resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourcegroups?api-version='+constants.api_version_resource_group
    response_get_resource_group = requests.get(url=list_resource_group_url, headers=headers)
    ctx.logger.info("response_get_resource_group.text {0} ".format(response_get_resource_group.text))
    if resource_group_name in response_get_resource_group.text:
        return True
    else:
        return False


def get_provisioning_state(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.logger.info("Searching for resource group {0}".format(resource_group_name))
    headers, location, subscription_id = auth.get_credentials()

    resource_group_url = "{0}/subscriptions/{1}/resourceGroups/{2}?api-version={3}".format(constants.azure_url, subscription_id, resource_group_name, constants.api_version_resource_group)
    return azurerequests.get_provisioning_state(headers, resource_group_name, resource_group_url)


