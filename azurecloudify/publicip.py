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
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation 
import auth

@operation
def creation_validation(**_):
    for property_key in constants.PUBLIC_IP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)

      
@operation
def create_public_ip(**_):
    for property_key in constants.PUBLIC_IP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    vm_name=ctx.node.properties['vm_name']
    public_ip_name=vm_name+'_pip'
    subscription_id = ctx.node.properties['subscription_id']
    location = ctx.node.properties['location']
    resource_group_name = vm_name+'_resource_group'
    public_ip_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
    
    credentials='Bearer '+ auth.get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
   
    
    try:
        ctx.logger.info("Creating new public ip : " + public_ip_name)
        public_ip_params=json.dumps({
                "location": location,
                "name": public_ip_name,
                "properties": {
                    "publicIPAllocationMethod": "Dynamic",
                    "idleTimeoutInMinutes": 4,
                }
            }
        )
        response_pip = requests.put(url=public_ip_url, data=public_ip_params, headers=headers)
        print response_pip.text
            
            
            
    except:
        ctx.logger.info("Public IP" + public_ip_name + "could not be created.")
        sys.exit(1)
    

    

def delete_public_ip(**_):
    vm_name=ctx.node.properties['vm_name']
    public_ip_name = vm_name+'_pip'
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = vm_name+'_resource_group'
    
    credentials='Bearer '+ auth.get_token_from_client_credentials()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    try:
        ctx.logger.info("Deleting Public IP")
        public_ip_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/ publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
        response_pip = requests.delete(url=public_ip_url,headers=headers)
        print(response_pip.text)
    except:
        ctx.logger.info("Public IP " + public_ip_name + " could not be deleted.")
        sys.exit(1)
        
    

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
