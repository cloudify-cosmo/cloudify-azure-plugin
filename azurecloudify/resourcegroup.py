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
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        if constants.EXISTING_RESOURCE_GROUP_KEY in ctx.node.properties:
            existing_resource_group_name = ctx.node.properties[constants.EXISTING_RESOURCE_GROUP_KEY]
            if existing_resource_group_name:
                resource_group_exists = _get_resource_group_name(existing_resource_group_name)
                if not resource_group_exists:
                    raise NonRecoverableError("Resource group {} doesn't exist your Azure account".format(existing_resource_group_name))
            else:
                raise NonRecoverableError("The value of '{}' in the input, is empty".format(constants.EXISTING_RESOURCE_GROUP_KEY))
        else:
            raise NonRecoverableError("'{}' was specified, but '{}' doesn't exist in the input".format('use_external_resource',constants.EXISTING_RESOURCE_GROUP_KEY))

        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.node.properties[constants.EXISTING_RESOURCE_GROUP_KEY]
        return
    
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    random_suffix_value = utils.random_suffix_generator()
    resource_group_name = constants.RESOURCE_GROUP_PREFIX+random_suffix_value
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

    resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group
    ctx.logger.info("Checking availability of resource_group: {}".format(resource_group_name))

    try:
        ctx.logger.info("Creating a new Resource group: {}".format(resource_group_name))
        resource_group_params = json.dumps({"name":resource_group_name,"location": location})
        response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=headers)
        print response_rg.text
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = resource_group_name
    except:
        ctx.logger.info("Resource Group {} could not be created".format(resource_group_name))
        raise NonRecoverableError("Resource Group {} could not be created".format(resource_group_name))


@operation
def delete_resource_group(**_):
   
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

    utils.clear_runtime_properties()


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        

def _get_resource_group_name(resource_group_name):
    ctx.logger.info("In _get_resource_group_name looking for {}".format(resource_group_name))
    credentials = auth.get_auth_token()
    ctx.logger.info("In _get_resource_group_name credentials is {}".format(credentials))
    headers = {"Content-Type": "application/json", "Authorization": "{}".format(credentials)}
    subscription_id = ctx.node.properties['subscription_id']
    list_resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourcegroups?api-version='+constants.api_version
    response_get_resource_group = requests.get(url=list_resource_group_url, headers=headers)
    ctx.logger.info("response_get_resource_group.text {} ".format(response_get_resource_group.text))
    if resource_group_name in response_get_resource_group.text:
        return True
    else:
        return False

