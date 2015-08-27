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
def vnet_creation_validation(**_):
    vnet_name=ctx.node.properties['vm_name']+'_vnet'
    if vnet_name in [vnet_name for vnet in _list_all_vnets()]:
        ctx.logger.info("Virtual Network: " + vnet_name + " successfully created.")
    else:
        ctx.logger.info("Virtual Network " + vnet_name + " creation validation failed.")
        sys.exit(1)
 

@operation
#vnet:
def create_vnet(**_):
    for property_key in constants.VNET_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
    ctx.logger.info("Checking availability of virtual network: " + vnet_name)

    if vnet_name not in [vnet_name for vnet in _list_all_vnets()]:
        try:
            ctx.logger.info("Creating new virtual network: " + vnet_name)
    
            vnet_params=json.dumps({"name":vnet_name, "location": location,"properties": {"addressSpace": {"addressPrefixes": constants.vnet_address_prefixes},"subnets": [{"name": constants.subnet_name, "properties": {"addressPrefix": constants.address_prefix}}]}})
            response_vnet = requests.put(url=vnet_url, data=vnet_params, headers=_generate_credentials())
            print response_vnet.text
        except WindowsAzureConflictError:
            ctx.logger.info("Virtual Network " + vnet_name + "could not be created.")
            sys.exit(1)
    else:
        ctx.logger.info("Virtual Network" + vnet_name + "has already been provisioned by another user.")
 

@operation
def delete_vnet(**_):
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Checking availability of virtual network: " + vnet_name)
    if vnet_name  in [vnet_name for vnet in _list_all_virtual_networks()]:
        try:
            ctx.logger.info("Deleting the virtual network: " + vnet_name)
            vnet_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
            response_vnet = requests.delete(url=vnet_url,headers=_generate_credentials())
            print response_vnet.text

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Virtual Network " + vnet_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Network " + vnet_name + " does not exist.")


def _list_all_vnets(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_vnets_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version
    list_vnet = requests.get(url=list_vnets_url, headers = _generate_credentials())
    print list_vnet.text

    #vnet_list= #extract vnet_name
    #return vnet_list


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
    print(token)
    credentials = "Bearer " + token
    head = {"Content-Type": "application/json", "Authorization": credentials}
    return head



def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
