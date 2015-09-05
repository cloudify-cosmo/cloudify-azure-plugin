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
from requests import Request,Session,Response
import json
import constants
import sys
import os
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
    for property_key in constants.RESOURCE_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    vm_name=ctx.node.properties['vm_name']
    resource_group_name = vm_name+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials='Bearer '+ auth.get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
   
    resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group
    ctx.logger.info("Checking availability of resource_group: " + resource_group_name)

    if 1:
        try:
            ctx.logger.info("Creating new Resource group: " + resource_group_name)
            resource_group_params=json.dumps({"name":resource_group_name,"location": location})
            response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=headers)
            print response_rg.text
        except:
            ctx.logger.info("Resource Group " + resource_group_name + " could not be created")
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " has already been provisioned")
  

@operation
def delete_resource_group(**_):
    vm_name=ctx.node.properties['vm_name']
    resource_group_name = vm_name+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials='Bearer '+get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    if 1:
        try:
            ctx.logger.info("Deleting Resource Group: " + resource_group_name)
            resource_group_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version_resource_group
            response_rg = requests.delete(url=resource_group_url, headers=headers)
            print(response_rg.text)
        except:
            ctx.logger.info("Resource Group" +  resource_group_name + "could not be deleted." )
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group '%s' does not exist" + resource_group_name)

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
