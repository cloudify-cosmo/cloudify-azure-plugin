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
import sys
import os
from cloudify.exceptions import NonRecoverableError
from azure import WindowsAzureConflictError
from azure import WindowsAzureMissingResourceError
from cloudify import ctx
from cloudify.decorators import operation

@operation
def resource_group_creation_validation(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if resource_group_name in resource_group_name in [resource_group_name for rg in _list_all_resource_groups()]:
        ctx.logger.info("Resource group: " + resource_group_name + " successfully created.")
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " creation validation failed.")
        sys.exit(1)
 

@operation
def create_resource_group(**_):
    for property_key in constants.RESOURCE_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)

    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version
    ctx.logger.info("Checking availability of resource_group: " + resource_group_name)

    if resource_group_name not in [resource_group_name for rg in _list_all_resource_groups()]:
        try:
            ctx.logger.info("Creating new Resource group: " + resource_group_name)
            resource_group_params=json.dumps({"name":resource_group_name,"location": location})
            response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=_generate_credentials())
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
    if resource_group_name in [resource_group_name for rg in _list_all_resource_group()]:
        try:
            ctx.logger.info("Deleting Resource Group: " + resource_group_name)
            resource_group_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version
            response_rg = requests.delete(url=resource_group_url, headers=_generate_credentials())
            print(response_rg.text)
        except WindowsAzureMissingResourceError:
            ctx.logger.info("Resource Group" +  resource_group_name + "could not be deleted." )
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group '%s' does not exist" + resource_group_name)


def _list_all_resource_groups(**_):
    subscription_id = ctx.node.properties['subscription_id']
    list_resource_groups_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourcegroups?api-version='+constants.api_version
    list_rg=requests.get(url=list_resource_groups_url, headers=_generate_credentials())
    print list_rg.text
    #rg_list= extract from json file
    #return rg_list


def _generate_credentials(**_):
    client_id=ctx.node.properties('client_id')
    tenant_id=ctx.node.properties('tenant_id')
    username=ctx.node.properties('username')
    password=ctx.node.properties('password')
    url='https://login.microsoftonline.com/'+tenant_id+'/oauth2/token'
    headers ={"Content-Type":"application/x-www-form-urlencoded"}
    body = "grant_type=password&username="+username+"&password="+password+"&client_id="+client_id+"&resource=https://management.core.windows.net/"
    req = Request(method="POST",url=url,data=body)
    req_prepped = req.prepare()
    s = Session()
    res = Response()
    res = s.send(req_prepped)
    s=res.content
    end_of_leader = s.index('access_token":"') + len('access_token":"')
    start_of_trailer = s.index('"', end_of_leader)
    token=s[end_of_leader:start_of_trailer]
    print(token)
    credentials = "Bearer " + token
    head = {"Content-Type": "application/json", "Authorization": credentials}
    return head



def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
