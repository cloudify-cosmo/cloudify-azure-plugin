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
def nic_creation_validation(**_):
    nic_name = ctx.node.properties['vm_name']+'_nic'
    if nic_name in [nic_name for nic in _list_all_nics()]:
        ctx.logger.info("Network Ierface Card: " + nic_name + " successfully created.")
    else:
        ctx.logger.info("Network Interface Card" + nic_name + " creation validation failed..")
        sys.exit(1)


@operation
#nic:
def create_nic(**_):
    for property_key in constants.NIC_REQUIRED_PROPERTIES:
       _validate_node_properties(property_key, ctx.node.properties)
    nic_name = ctx.node.properties['vm_name']+'_nic'
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
    ctx.logger.info("Checking availability of network interface card: " + nic_name)
    if nic_name not in [nic_name for nic in _list_all_virtual_machines()]:
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
            response_nic = requests.put(url=nic_url, data=nic_params, headers=_generate_credentials())
            print(response_nic.text)
        except WindowsAzureConflictError:
          ctx.logger.info("network interface card " + nic_name + "could not be created.")
          sys.exit(1)
    else:
     ctx.logger.info("network interface card" + nic_name + "has already been provisioned by another user.")
   

@operation
def delete_nic(**_):
    nic_name = ctx.node.properties['vm_name']+'_nic'
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if nic_name in [nic_name for pip in _list_all_nics()]:
        try:
            ctx.logger.info("Deleting NIC")
            nic_url="https://management.azure.com/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
            response_nic = requests.delete(url=nic_url,headers=_generate_credentials())
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
    list_nic = requests.get(url=list_nics_url, headers = _generate_credentials())
    print list_nic.text

    #nic_list= #extract nic_name
    #return nic_list
    

def _generate_credentials(**_):
    client_id=ctx.node.properties('client_id')
    tenant_id=ctx.node.properties('tenant_id')
    username=ctx.node.properties('username')
    password=ctx.node.properties('password')
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

