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
import utils
import azurerequests
from resourcegroup import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation


@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        utils.validate_node_properties(property_key, ctx.node.properties)


@operation
def create_availability_set(**_):
    utils.set_runtime_properties_from_file()
    availability_set_name = utils.set_resource_name(_get_availability_set_name, 'Availabilty set',
                      constants.AVAILABILITY_SET_KEY, constants.EXISTING_AVAILABILITY_SET_KEY,
                      constants.AVAILABILITY_SET_PREFIX)
    if availability_set_name is None:
        # Using an existing storage account, so don't create anything
        return constants.ACCEPTED_STATUS_CODE

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    if constants.AVAILABILITY_SET_KEY not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[constants.AVAILABILITY_SET_KEY] = availability_set_name

    ctx.logger.info("Creating a new availability set: {0}".format(availability_set_name))
    availability_set_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/availabilitySets/'+availability_set_name+'?api-version='
    availability_set_params = json.dumps({ 
           "name": availability_set_name, 
           "type": "Microsoft.Compute/availabilitySets", 
           "location": location
        })
    status_code = utils.create_resource(headers, availability_set_name, availability_set_params, availability_set_url, 'Availability set')
    ctx.logger.info("{0} is {1}".format(constants.AVAILABILITY_SET_KEY, availability_set_name))
    return status_code
    
"""    
@operation
def create_availability_set(**_):
    utils.set_runtime_properties_from_file()
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
        })

        response_as = requests.put(url=availability_set_url, data=availability_set_params, headers=headers)
        if response_as.text:
            ctx.logger.info("create_availability_set {0} response_as.text is {1}".format(availability_set_name, response_as.text))
            if utils.request_failed("{0}:{1}".format('create_availability_set', availability_set_name), response_as):
                raise NonRecoverableError("create_availabilty_set {0} could not be created".format(availability_set_name))
        ctx.instance.runtime_properties[constants.AVAILABILTY_SET_KEY] = availability_set_name
    except:
        ctx.logger.info("Availabilty set {0} could not be created".format(availability_set_name))
        raise NonRecoverableError("Availabilty Set {} could not be created".format(availability_set_name))
            
"""
           
@operation
def set_dependent_resources_names(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY])
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] 
        

@operation
def delete_availability_set(**_):
    delete_current_availability_set()
    utils.clear_runtime_properties()
    

def delete_current_availability_set(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing availabilty set was used, so there's no need to delete")
        return
    
    availability_set_name = ctx.instance.runtime_properties[constants.AVAILABILTY_SET_KEY]
    headers, location, subscription_id = auth.get_credentials()
    try:
        ctx.logger.info("Deleting Availabilty set: {0}".format(availability_set_name))
        resource_group_name = "modify later"
        delete_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/availabilitySets/'+availability_set_name+'?api-version=2015-05-01-preview'
        response_as = requests.delete(url=delete_url, headers=headers)
        print(response_as.text)
    except:
        ctx.logger.info("Availability set {0} could not be deleted.".format(availability_set_name))
        
    
def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        

def _get_availability_set_name(availability_set_name):  
    ctx.logger.info("In _get_availability_set_name looking for {0} ".format(availability_set_name))
    headers, location, subscription_id = auth.get_credentials()

    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in availability set runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))

    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/availabilitySets?api-version='+constants.api_version

    response_list = requests.get(url, headers=headers)
    ctx.logger.info("availability set response_list.text {0} ".format(response_list.text))
    if availability_set_name in response_list.text:
        return True
    else:
        ctx.logger.info("Availability Set {0} does not exist".format(availability_set_name))
        return False
