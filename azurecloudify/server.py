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
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation

#virtualmachine:

@operation
def creation_validation(**_):
    for property_key in constants.VM_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_vm(**_):

    for property_key in constants.VM_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
        
    vm_name = ctx.node.properties['vm_name'] 
    resource_group_name = vm_name+'_resource_group'
    storage_account_name = vm_name+'storageaccount'
    location = ctx.node.properties['location']
    vnet_name = vm_name+'_vnet'
    nic_name = vm_name+'_nic'
    
    credentials='Bearer '+get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Checking availability of virtual network: " + vm_name)
    if 1:
        try:
            ctx.logger.info("Creating new virtual machine: " + vm_name)
            virtual_machine_params=json.dumps(
            {
                "id":"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Compute/virtualMachines/"+vm_name,
                "name":vm_name,
                "type":"Microsoft.Compute/virtualMachines",
                "location":location,
                "properties": {
                    "hardwareProfile": {
                        "vmSize": ctx.node.properties['vm_size']
                    },
                    "osProfile": {
                        "computername": vm_name,
                        "adminUsername": constants.admin_username,
                        "linuxConfiguration": {
                            "disablePasswordAuthentication": "true",
                            "ssh": {
                                "publicKeys": [
                                    {
                                        "path": "/home/"+constants.admin_username+"/.ssh/authorized_keys",
                                        "keyData": constants.key_data}
                                ]
                            }
                        }
                    },
                    "storageProfile": {
                        "imageReference": {
                            "publisher": constants.image_reference_publisher,
                            "offer": constants.image_reference_offer,
                            "sku" : constants.image_reference_sku,
                            "version":constants.vm_version
                        },
                        "osDisk" : {
                            "name": constants.os_disk_name,
                            "vhd": {
                                "uri": "http://"+storage_account_name+".blob.core.windows.net/vhds/osdisk.vhd"
                            },
                            "caching": "ReadWrite",
                            "createOption": "FromImage"
                        }
                    },
                    "networkProfile": {
                        "networkInterfaces": [
                            {
                                "id": "/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Network/networkInterfaces/"+nic_name
                            }
                        ]                        }
                    }
                })
            virtual_machine_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
            response_vm = requests.put(url=virtual_machine_url, data=virtual_machine_params, headers=headers)
            print(response_vm.text)
        except:
          ctx.logger.info("Virtual Machine " + vm_name + "could not be created.")
          sys.exit(1)
    else:
     ctx.logger.info("Virtual Machine" + vm_name + "has already been provisioned by another user.")

        
#start_vm
@operation
def start_vm(**_):
    subscription_id = ctx.node.properties['subscription_id']
    vm_name = ctx.node.properties['vm_name']
    
    credentials='Bearer '+get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    resource_group_name = vm_name+'_resource_group'
    start_vm_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_start_vm=requests.post(start_vm_url,headers=headers)
    print (response_start_vm.text)
    
    
#stop_vm
@operation
def stop_vm(**_):
    subscription_id = ctx.node.properties['subscription_id']
    vm_name = ctx.node.properties['vm_name']
    
    credentials='Bearer '+get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    resource_group_name = vm_name+'_resource_group'
    stop_vm_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_stop_vm=requests.post(stop_vm_url,headers=headers)
    print (response_stop_vm.text)


@operation
def delete_virtual_machine(**_):
    vm_name = ctx.node.properties['vm_name']
    resource_group_name = vm_name+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials='Bearer '+get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    ctx.logger.info("Checking availability of virtual network: " + vm_name)
    if 1:
        try:
            ctx.logger.info("Deleting the virtual machine: " + vm_name)
            vm_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
            response_vm = requests.delete(url=vm_url,headers=headers)
            print(response_vm.text)

        except:
            ctx.logger.info("Virtual Machine " + vm_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Machine " + vm_name + " does not exist.")

"""
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
    credentials = "Bearer " + token
    head = {"Content-Type": "application/json", "Authorization": credentials}
    return head
"""

def get_token_from_client_credentials(**_):
 
    client_id = ctx.node.properties['client_id']
    client_secret = ctx.node.properties['password']
    tenant_id = ctx.node.properties['tenant_id']
    endpoints = 'https://login.microsoftonline.com/'+tenant_id+'/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': constants.resource,
    }
    response = requests.post(endpoints, data=payload).json()
    token=response['access_token']
    print(token)
    return token
    


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
