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
import utils
import sys
from cloudify.exceptions import NonRecoverableError
from azure import WindowsAzureConflictError
from azure import WindowsAzureMissingResourceError
from cloudify import ctx
from cloudify.decorators import operation
    
@operation
def nic_creation_validation(**_):
    nic_name = ctx.node.properties['vm_name']+'_nic'
    if nic_name in [nic_name for nic in _list_all_nics()]:
        ctx.logger.info("Network Ierface Card: " + nic_name + " successfully created.")
    else:
        ctx.logger.info("Network Interface Card" + nic_name + " creation validation failed..")
        sys.exit(1)


@operation
#nic:
def create_nic():
    nic_name = ctx.node.properties['vm_name']+'_nic'
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
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
    response_nic = requests.put(url=nic_url, data=nic_params, headers=constants.headers)
    print(response_nic.text)
   

@operation
def delete_nic(**_):
    nic_name = ctx.node.properties['vm_name']+'_nic'
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if nic_name in [nic_name for pip in _list_all_nics()]:
        try:
            ctx.logger.info("Deleting NIC")
            nic_url="https://management.azure.com/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
            response_nic = requests.delete(url=nic_url,headers=constants.headers)
            print(response_nic.text)
        except WindowsAzureMissingResourceError:
            ctx.logger.info("Network Interface Card " + nic_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Network Interface Card " + nic_name + " does not exist.")

    
def _list_all_nics(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_nics_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkInterfaces?api-version='+constants.api_version
    list_nic = requests.get(url=list_nics_url, headers = constants.headers)
    print list_nic.text

    #nic_list= #extract nic_name
    #return nic_list

