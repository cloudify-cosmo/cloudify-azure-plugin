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
import sys
from cloudify.exceptions import NonRecoverableError
from azure import WindowsAzureConflictError
from azure import WindowsAzureMissingResourceError
from cloudify import ctx
from cloudify.decorators import operation

@operation
def resource_group_creation_validation(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if resource_group_name in resource_group_name in [resource_group_name for rg in utils.list_all_resource_groups()]:
        ctx.logger.info("Resource group: " + resource_group_name + " successfully created.")
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " creation validation failed.")
        sys.exit(1)
 

@operation
#resourcegroup:
def create_resource_group(**_):
    for property_key in constants.RESOURCE_GROUP_REQ_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)

    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version
    ctx.logger.info("Checking availability of resource_group: " + resource_group_name)

    if resource_group_name not in [resource_group_name for rg in utils.list_all_resource_groups()]:
        try:
            ctx.logger.info("Creating new Resource group: " + resource_group_name)
            resource_group_params=json.dumps({"name":resource_group_name,"location": location})
            response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=constants.headers)
            print response_rg.text
        except WindowsAzureConflictError:
            ctx.logger.info("Resource Group " + resource_group_name + " could not be created")
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " has already been provisioned")
  

@operation
def delete_resource_group(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    if resource_group_name in [resource_group_name for rg in utils.list_all_resource_group()]:
        try:
            ctx.logger.info("Deleting Resource Group: " + resource_group_name)
            resource_group_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version
            response_rg = requests.delete(url=resource_group_url, headers=constants.headers)
            print(response_rg.text)
        except WindowsAzureMissingResourceError:
            ctx.logger.info("Resource Group" +  resource_group_name + "could not be deleted." )
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group '%s' does not exist" + resource_group_name)


def _list_all_resource_groups(**_):
    subscription_id = ctx.node.properties['subscription_id']
    list_resource_groups_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourcegroups?api-version='+constants.api_version
    list_rg=requests.get(url=list_resource_groups_url, headers=constants.headers)
    print list_rg.text
    #rg_list= extract from json file
    #return rg_list
