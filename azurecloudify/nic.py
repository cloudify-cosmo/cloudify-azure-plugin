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
 
 
@operation
def creation_validation(**_):
    for property_key in constants.NIC_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
        

@operation
#nic:
def create_nic(**_):
    for property_key in constants.NIC_REQUIRED_PROPERTIES:
       _validate_node_properties(property_key, ctx.node.properties)
    vm_name=ctx.node.properties['vm_name']
    nic_name = vm_name+'_nic'
    public_ip_name=vm_name+'_pip'
    resource_group_name = vm_name+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    vnet_name = vm_name+'_vnet'
    
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
        except:
          ctx.logger.info("network interface card " + nic_name + "could not be created.")
          sys.exit(1)
    else:
     ctx.logger.info("network interface card" + nic_name + "has already been provisioned by another user.")
    

@operation
def delete_nic(**_):
    vm_name=ctx.node.properties['vm_name']
    nic_name = vm_name+'_nic'
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials='Bearer '+ auth.get_token_from_client_credentials()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
   
    resource_group_name = vm_name+'_resource_group'
    if 1:
       
        try:
           ctx.logger.info("Deleting NIC")
           nic_url="https://management.azure.com/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
           response_nic = requests.delete(url=nic_url,headers=headers)
           print(response_nic.text)
        except:
           ctx.logger.info("Network Interface Card " + nic_name + " could not be deleted.")
           sys.exit(1)
    else:
        ctx.logger.info("Network Interface Card " + nic_name + " does not exist.")
   


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))

