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


@operation
def creation_validation(**_):
    for property_key in constants.RESOURCE_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_resource_group(**_):
    resource_group_name = utils.set_resource_name(_get_resource_group_name, 'Resource group',
                      constants.RESOURCE_GROUP_KEY, constants.EXISTING_RESOURCE_GROUP_KEY,
                      constants.RESOURCE_GROUP_PREFIX)
    if resource_group_name is None:
        # Using an existing resource group, so don't create anything
        return

    headers, location, subscription_id = auth.get_credentials()

    resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group

    try:
        ctx.logger.info("Creating a new Resource group: {}".format(resource_group_name))
        resource_group_params = json.dumps({"name": resource_group_name, "location": location})
        response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=headers)
        if response_rg.text:
            ctx.logger.info("create_resource_group {0} response_rg.text is {1}".format(resource_group_name, response_rg.text))
            if utils.request_failed("{0}:{1}".format('create_resource_group', resource_group_name), response_rg):
                raise NonRecoverableError("Resource group {0} could not be created".format(resource_group_name))

        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = resource_group_name
    except:
        ctx.logger.info("Resource Group {0} could not be created".format(resource_group_name))
        raise NonRecoverableError("Resource Group {0} could not be created".format(resource_group_name))


@operation
def delete_resource_group(**_):
    delete_current_resource_group()
    utils.clear_runtime_properties()


def delete_current_resource_group(**_):
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        ctx.logger.info("An existing resource group was used, so there's no need to delete")
        return

    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    credentials = 'Bearer '+auth.get_auth_token()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
        
    try:
        ctx.logger.info("Deleting Resource Group: {}".format(resource_group_name))
        resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group
        response_rg = requests.delete(url=resource_group_url, headers=headers)
        print(response_rg.text)
    except:
        ctx.logger.info("Resource Group {} could not be deleted.".format(resource_group_name))


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        

def _get_resource_group_name(resource_group_name):
    ctx.logger.info("In _get_resource_group_name looking for {0}".format(resource_group_name))
    credentials = 'Bearer ' + auth.get_auth_token()
    ctx.logger.info("In _get_resource_group_name credentials is {0}".format(credentials))
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    subscription_id = ctx.node.properties['subscription_id']
    list_resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourcegroups?api-version='+constants.api_version_resource_group
    response_get_resource_group = requests.get(url=list_resource_group_url, headers=headers)
    ctx.logger.info("response_get_resource_group.text {0} ".format(response_get_resource_group.text))
    if resource_group_name in response_get_resource_group.text:
        return True
    else:
        return False

