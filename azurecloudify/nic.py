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
from publicip import *
from vnet import *
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation
 

 
@operation
def creation_validation(**_):
    for property_key in constants.NIC_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    
        
    nic_name_exists = _get_nic_name()
    
    if ctx.node.properties['use_external_resource'] and not nic_name_exists:
        raise NonRecoverableError(
        'External resource, but the supplied '
        'nic does not exist in the account.')
        
    if not ctx.node.properties['use_external_resource'] and nic_name_exists:
        raise NonRecoverableError(
        'Not external resource, but the supplied '
        'nic exists in the account.')
        

@operation
#nic:
 def create_nic(**_):
    if ctx.node.properties['use_external_resource']:
        ctx.instance.runtime_properties[constants.NIC_KEY]=ctx.node.properties['existing_nic_name']
    else:
        public_ip_name=ctx.instance.runtime_properties['publicip']
        resource_group_name = ctx.instance.runtime_properties['resource_group']
        location = ctx.node.properties['location']
        subscription_id = ctx.node.properties['subscription_id']
        vnet_name = vnet.vnet_name
        RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
        nic_name = constants.NIC_PREFIX+RANDOM_SUFFIX_VALUE
        credentials= 'Bearer ' + auth.get_token_from_client_credentials()
        headers = {"Content-Type": "application/json", "Authorization": credentials}
        
        ctx.logger.info("Checking availability of network interface card: " + nic_name)
     
        if 1:
            try:
              ctx.logger.info("Creating new network interface card: " + nic_name)
              nic_params=json.dumps({
                                "location":location,
                                "properties":{
                                    "ipConfigurations":[
                                        {
                                            "name":constants.ip_config_name,
                                            "properties":{
                                                "subnet":{
                                                    "id":"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Network/virtualNetworks/"+vnet_name+"/subnets/"+constants.subnet_name
                                                },
                                                "privateIPAllocationMethod":"Dynamic",
                                                "publicIPAddress":{
                                                        "id":"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Network/publicIPAddresses/"+public_ip_name
                                            }
                                            }
                                        }
                                    ],
                                }
                            })
              nic_url=constants.azure_url+"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
              response_nic = requests.put(url=nic_url, data=nic_params, headers=headers)
              print(response_nic.text)
              ctx.instance.runtime_properties['nic']=nic_name
              
              ctx.logger.info("response_nic : " + response_nic.text)
              response_nic_json = response_nic.json()
              nic_root_properties = response_nic_json[u'properties']
              ctx.logger.info("nic_root_properties : " + str(nic_root_properties))
              ip_configurations = nic_root_properties[u'ipConfigurations'][0]
              ctx.logger.info("nic ip_configurations0 : " + str(ip_configurations))
              curr_properties = ip_configurations[u'properties']
              ctx.logger.info("nic curr_properties : " + str(curr_properties))		  
              private_ip_address = curr_properties[u'privateIPAddress']
              ctx.logger.info("nic private_ip_address : " + str(private_ip_address))
              ctx.instance.runtime_properties['private_ip']= str(private_ip_address)
            except:
              ctx.logger.info("network interface card " + nic_name + "could not be created.")
              sys.exit(1)
        else:
            ctx.logger.info("network interface card" + nic_name + "has already been provisioned by another user.")
        

@operation
def delete_nic(**_):
    
    subscription_id = ctx.node.properties['subscription_id']
    credentials='Bearer '+ auth.get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    resource_group_name = ctx.instance.runtime_properties['resource_group']
    nic_name=ctx.instance.runtime_properties['nic_name']
    if 1:
       
        try:
           ctx.logger.info("Deleting NIC")
           nic_url=constants.azure_url+"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
           response_nic = requests.delete(url=nic_url,headers=headers)
           print(response_nic.text)
        except:
           ctx.logger.info("Network Interface Card " + nic_name + " could not be deleted.")
           sys.exit(1)
    else:
        ctx.logger.info("Network Interface Card " + nic_name + " does not exist.")
   

@operation
def set_dependent_resources_names(azure_config,**kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.source.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = ctx.target.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    ctx.source.instance.runtime_properties[constants.VNET_KEY] = ctx.target.instance.runtime_properties[constants.VNET_KEY]
    if 'publicip' in ctx.target.instance.runtime_properties:
       ctx.source.instance.runtime_properties[constants.PUBLIC_IP_KEY] = ctx.target.instance.runtime_properties[constants.PUBLIC_IP_KEY]

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        
 def _get_nic_name():
    nic_name=ctx.node.properties['existing_nic_name']
    resource_group_name= ctx.instance.runtime_properties['resource_group']
    credentials=auth.get_token_from_client_credentials()
    headers={"Content-Type": "application/json", "Authorization": credentials}
    subscription_id=ctx.node.properties['subscription_id']
    nic_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkInterfaces?api-version='+constants.api_version
    response_get_nic_name=requests.get(url=nic_url,headers=headers)
    if nic_name in response_get_nic_name.text:
        return True
    else:
        return False

