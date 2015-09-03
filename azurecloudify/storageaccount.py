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

@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)

@operation
def create_storage_account(**_):
    location = ctx.node.properties['location']
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
       _validate_node_properties(property_key, ctx.node.properties)
    vm_name=ctx.node.properties['vm_name']
    storage_account_name = vm_name+'storageaccount'
    resource_group_name = vm_name+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    credentials=get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    ctx.logger.info("Checking availability of storage account: " + storage_account_name)
    if 1:
        try:
            ctx.logger.info("Creating new storage account: " + storage_account_name)
            storage_account_url= constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
            storage_account_params=json.dumps({"properties": {"accountType": constants.storage_account_type,}, "location": location})
            response_sa = requests.put(url=storage_account_url, data=storage_account_params, headers=headers)
            print response_sa.text
        except:
            ctx.logger.info("Storage Account " + storage_account_name + "could not be created.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + "has already been provisioned by another user.")


@operation
def delete_storage_account(**_):
    vm_name=ctx.node.properties['vm_name']
    storage_account_name = vm_name+'storageaccount'
    resource_group_name = vm_name+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    credentials=get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    ctx.logger.info("Deleting Storage Account"+storage_account_name)
    if 1:
        try:
            storage_account_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
            response_sa = requests.delete(url=storage_account_url,headers=headers)
            print response_sa.text

        except:
            ctx.logger.info("Storage Account " + storage_account_name + " could not be deleted.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + " does not exist.")


"""
def _generate_credentials(**_):
    client_id=ctx.node.properties['client_id']
    tenant_id=ctx.node.properties['tenant_id']
    username=ctx.node.properties['username']
    password=ctx.node.properties['password']
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
    credentials = "Bearer " + token
    head = {"Content-Type": "application/json", "Authorization": credentials}
    return head
"""
def get_token_from_client_credentials():
 
    client_id = ctx.node.properties['client_id']
    client_secret = ctx.node.properties['password']
    tenant_id = ctx.node.properties['tenant_id']
    endpoints = 'https://login.microsoftonline.com/'+tenant_id+'/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': constants.resource,
    }
    response = requests.post(endpoints, data=payload).json()
    return response['access_token']

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
