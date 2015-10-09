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
from resourcegroup import *
import utils
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation



@operation
def creation_validation(**_):
    for property_key in constants.VNET_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    
    vnet_exists = _get_vnet_name()
    if ctx.node.properties['use_external_resource'] and not vnet_exists:
        raise NonRecoverableError(
        'External resource, but the supplied '
        'vnet does not exist in the account.')
    
    if not ctx.node.properties['use_external_resource'] and vnet_exists:
        raise NonRecoverableError(
        'Not external resource, but the supplied '
        'vnet exists in the account.')

@operation
def create_vnet(**_):
    if ctx.node.properties['use_external_resource']
        ctx.instance.runtime_properties[constants.VNET_KEY]=ctx.node.properties['existing_vnet_name']
    else
        resource_group_name = ctx.instance.runtime_properties['resource_group']
        location = ctx.node.properties['location']
        subscription_id = ctx.node.properties['subscription_id']
        credentials='Bearer '+ auth.get_token_from_client_credentials()
        headers = {"Content-Type": "application/json", "Authorization": credentials}
        RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
        vnet_name = contants.VNET_GROUP_PREFIX+RANDOM_SUFFIX_VALUE
        vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
        ctx.logger.info("Checking availability of virtual network: " + vnet_name)
    
        if 1:
            try:
                ctx.logger.info("Creating new virtual network: " + vnet_name)
        
                vnet_params=json.dumps({"name":vnet_name, "location": location,"properties": {"addressSpace": {"addressPrefixes": constants.vnet_address_prefixes},"subnets": [{"name": constants.subnet_name, "properties": {"addressPrefix": constants.address_prefix}}]}})
                response_vnet = requests.put(url=vnet_url, data=vnet_params, headers=headers)
                print response_vnet.text
                ctx.instance.runtime_properties['vnet']=vnet_name
            except:
                ctx.logger.info("Virtual Network " + vnet_name + "could not be created.")
                sys.exit(1)
        else:
            ctx.logger.info("Virtual Network" + vnet_name + "has already been provisioned by another user.")
    
    @operation
    def delete_vnet(**_):
        
        resource_group_name = ctx.instance.runtime_properties['resource_group']
        subscription_id = ctx.node.properties['subscription_id']
        credentials='Bearer '+ auth.get_token_from_client_credentials()
        headers = {"Content-Type": "application/json", "Authorization": credentials}
        
        ctx.logger.info("Checking availability of virtual network: " + vnet_name)
        if 1:
            try:
                ctx.logger.info("Deleting the virtual network: " + vnet_name)
                vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
                response_vnet = requests.delete(url=vnet_url,headers=headers)
                print response_vnet.text
            except:
                ctx.logger.info("Virtual Network " + vnet_name + " could not be deleted.")
            sys.exit(1)
        else:
            ctx.logger.info("Virtual Network " + vnet_name + " does not exist.")


@operation
def set_dependent_resources_names(azure_config,**kwargs):
   ctx.source.instance.runtime_properties['resource_group'] = ctx.target.instance.runtime_properties['resource_group']
   ctx.source.instance.runtime_properties['storage_account'] = ctx.target.instance.runtime_properties['storage_account']
   
def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        
def _get_vnet_name():
    vnet_name= ctx.node.properties['existing_vnet_name']
    resource_group_name = ctx.instance.runtime_properties['resource_group']
    credentials=auth.get_token_from_client_credentials()
    subscription_id=ctx.node.properties['subscription_id']
    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    response_list = requests.get(url, headers = headers)
    if vnet_name in response_list.text:
        return True
    else:
        ctx.logger.info("Virtual Network %s does not exist"+ vnet_name)
        return False
