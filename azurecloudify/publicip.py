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
from resourcegroup import *
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation 
import auth

RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
public_ip_name=ctx.node.properties['public_ip_name']+]+RANDOM_SUFFIX_VALUE

@operation
def creation_validation(**_):
    for property_key in constants.PUBLIC_IP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)

    public_ip =  _get_public_ip_name(utils.get_public_ip_name())

    if ctx.node.properties['use_external_resource'] and not public_ip:
    	raise NonRecoverableError(
    	'External resource, but the supplied '
    	'public ip does not exist in the account.')
    if not ctx.node.properties['use_external_resource'] and resource_group:
    	raise NonRecoverableError(
    	'Not external resource, but the supplied '
    	'public ip exists in the account.')


      
@operation
def create_public_ip(**_):
    if ctx.node.properties['use_external_resource'] 
        if not public_ip:
	    	raise NonRecoverableError(
		'External resource, but the supplied '
		'public ip does not exist in the account.')
		sys.exit(1)
        else
        	ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY] = ctx.node.properties['existing_public_ip_name']
    else  
    
    subscription_id = ctx.node.properties['subscription_id']
    location = ctx.node.properties['location']
    resource_group_name =resourcegroup.resource_group_name
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
        ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]=public_ip_name
            
            
            
    except:
        ctx.logger.info("Public IP" + public_ip_name + "could not be created.")
        sys.exit(1)
    

    

def delete_public_ip(**_):
    
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = resourcegroup.resource_group_name
    
    credentials='Bearer '+ auth.get_token_from_client_credentials()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    try:
        ctx.logger.info("Deleting Public IP")
        public_ip_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/ publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
        response_pip = requests.delete(url=public_ip_url,headers=headers)
        print(response_pip.text)
        
    except:
        ctx.logger.info("Public IP " + public_ip_name + " could not be deleted.")
        sys.exit(1)
        
    
def _get_public_ip_name():

    headers={"Content-Type": "application/json", "Authorization": credentials}
    subscription_id=ctx.node.properties['subscription_id']
    resource_group_name=resourcegroup.resource_group_name
    list_pip_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses?api-version='+constants.api_version
    response_list_pip=requests.get(url=list_pip_url,headers=headers)
    print(response_list_pip.text)   
    # extract the list of resource group names
    list_of_pip=[]
    if resource_group_name in list_of_pip:
	 return public_ip_name
    else:
	 ctx.logger.info("Public IP %s does not exist"+ public_ip_name)
	 return None

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
