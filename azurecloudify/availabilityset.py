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
import auth
import os
from resourcegroup import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation

@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_availability_set(**_):
    availability_set_name = ''
    if availability_set_name is None:
        return
    
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    if constants.AVAILABILITY_SET_KEY in ctx.instance.runtime_properties:
        availability_set_name = ctx.instance.runtime_properties[constants.AVAILABILITY_SET_KEY]
    else:
        random_suffix_value = utils.random_suffix_generator()
        availability_set_name = constants.AVAILABILITY_SET_PREFIX+random_suffix_value
        
    availability_set_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/availabilitySets/'+availability_set_name+'?api-version='
    
    try:    
        ctx.logger.info("Creating new availability set: {0}".format(availability_set_name))
        availability_set_params = json.dumps({ 
           "name": availability_set_name, 
           "type": "Microsoft.Compute/availabilitySets", 
           "location": location
        }
    )
    response_as = requests.put(url=availability_set_url, data=availability_set_params, headers=headers) 
    if response_as.text:
        ctx.logger.info("create_availability_set {0} response_as.text is {1}".format(availability_set_name, response_as.text))
        if utils.request_failed("{0}:{1}".format('create_availability_set', availabilty_set_name), response_as)
            raise NonRecoverableError("create_availabilty_set {0} could not be created".format(availability_set_name))
        ctx.instance.runtime_properties[constants.AVAILABILTY_SET_KEY] = availabilty_set_name
    except:
        ctx.logger.info("Availabilty set {0} could not be created".format(availabilty_set_name))
        raise NonRecoverableError("Availabilty Set {} could not be created".format(availabilty_set_name))
            
           
@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] 
        

@operation
def delete_availability_set(**_):
    delete_current_availability_set()
    utils.clear_runtime_properties()
    
    

def delete_current_availability_set(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing availabilty set was used, so there's no need to delete")
        return
    
    availabilty_set_name = ctx.instance.runtime_properties[constants.AVAILABILTY_SET_KEY]
    headers, location, subscription_id = auth.get_credentials()
    try:
        ctx.logger.info("Deleting Availabilty set: {0}".format(availabilty_set_name))
        delete_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/availabilitySets/'+availability_set_name+'?api-version=2015-05-01-preview'
        response_as = requests.delete(url=delete_url, headers=headers)
        print(response_as.text)
    except:
        ctx.logger.info("Availability set {0} could not be deleted.".format(availabilty_set_name))
        
    
def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        
        
        
def _get_availabilty_set_name(availability_set_name):  
    
