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
import auth
import utils
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation

@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
        
    storage_account = _get_all_storage_account(
        utils.get_storage_account_name())
        
    if ctx.node.properties['use_external_resource'] and not storage_account:
        raise NonRecoverableError(
        'External resource, but the supplied '
        'storage account does not exist in the account.')
    if not ctx.node.properties['use_external_resource'] and storage_account:
        raise NonRecoverableError(
        'Not external resource, but the supplied '
        'storage account group exists in the account.')
    

@operation
def create_storage_account(**_):
    if ctx.node.properties['use_external_resource']
        if not resource_group:
            raise NonRecoverableError(
            'External resource, but the supplied '
            'storage account does not exist in the Azure account.')
            sys.exit(1)
        else
            ctx.instance.runtime_properties['existing_storage_account_name']
            return
    else
            location = ctx.node.properties['location']
            vm_name=ctx.node.properties['vm_name']
            RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
            storage_account_name = vm_name+'storageaccount'+RANDOM_SUFFIX_VALUE
            subscription_id = ctx.node.properties['subscription_id']
            
            credentials='Bearer '+auth.get_token_from_client_credentials()
            
            headers = {"Content-Type": "application/json", "Authorization": credentials}
            
            ctx.logger.info("Checking availability of storage account: " + storage_account_name)
            if 1:
                try:
                    ctx.logger.info("Creating new storage account: " + storage_account_name)
                    storage_account_url= constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
                    storage_account_params=json.dumps({"properties": {"accountType": constants.storage_account_type,}, "location": location})
                    response_sa = requests.put(url=storage_account_url, data=storage_account_params, headers=headers)
                    print response_sa.text
                    ctx.instance.runtime_properties['storage_account']=storage_account_name
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
    
    credentials='Bearer '+auth.get_token_from_client_credentials()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    ctx.logger.info("Deleting Storage Account"+storage_account_name)
    if 1:
        try:
            storage_account_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
            response_sa = requests.delete(url=storage_account_url,headers=headers)
            print response_sa.text

        except:
            ctx.logger.info("Storage Account " + storage_account_name + " could not be deleted.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + " does not exist.")



def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        
def _get_all_storage_account(storage_account_name):
    resource_group= ctx.node.properties['exsisting_resource_group_name']
    subscription_id=ctx.node.properties['subscription_id']
    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group+'/providers/Microsoft.Storage/storageAccounts?api-version='+constants.api_version
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    response_list = requests.get(url, headers = headers).json()
    print response_list['value']['name']
