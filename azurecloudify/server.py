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
import utils
import os
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation




#virtualmachine:

@operation
def creation_validation(**_):
    for property_key in constants.VM_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


    vm_name_exists = _get_vm_name()
    if ctx.node.properties['use_external_resource'] and not vm_name_exists:
    raise NonRecoverableError(
    'External resource, but the supplied '
    'vm does not exist in the account.')
    if not ctx.node.properties['use_external_resource'] and vm_name_exists:
    raise NonRecoverableError(
    'Not external resource, but the supplied '
    'vm exists in the account.')

@operation
def create_vm(**_):

    RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
    vm_name = ctx.node.properties['vm_name']+RANDOM_SUFFIX_VALUE
    resource_group_name = ctx.instance.runtime_properties['resource_group']
    storage_account_name = ctx.instance.runtime_properties['storage_account']
    location = ctx.node.properties['location']
    vnet_name = ctx.instance.runtime_properties['vnet']
    nic_name = ctx.instance.runtime_properties['nic']
    public_ip_name= ctx.instance.runtime_properties['publicip']
    RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
    vm_name = contants.VM_PREFIX +RANDOM_SUFFIX_VALUE
    credentials='Bearer '+auth.get_token_from_client_credentials()
    subscription_id = ctx.node.properties['subscription_id']
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    
    
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
                        "adminUsername": ctx.node.properties['ssh_username'],
                        "linuxConfiguration": {
                            "disablePasswordAuthentication": "true",
                            "ssh": {
                                "publicKeys": [
                                    {
                                        "path": "/home/"+ctx.node.properties['ssh_username']+"/.ssh/authorized_keys",
                                        "keyData": ctx.node.properties['key_data']}
                                ]
                            }
                        }
                    },
                    "storageProfile": {
                        "imageReference": {
                            "publisher": ctx.node.properties['image_reference_publisher'],
                            "offer": ctx.node.properties['image_reference_offer'],
                            "sku" : ctx.node.properties['image_reference_sku'],
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
    credentials='Bearer '+auth.get_token_from_client_credentials()
   
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = resourcegroup.resource_group_name
    public_ip_name= publicip.public_ip_name
    get_pip_info_url= constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
    raw_response = requests.get(url=get_pip_info_url, headers=headers)
    ctx.logger.info("raw_response : " + str(raw_response))
    response_get_info = raw_response.json()
    ctx.logger.info("response_get_info : " + str(response_get_info))
    currProperties = response_get_info[u'properties']
    ctx.logger.info("currProperties : " + str(currProperties))
    currIpAddress = currProperties[u'ipAddress']
    ctx.logger.info("Current public IP address is " + str(currIpAddress))
    ctx.instance.runtime_properties['vm_public_ip']= currIpAddress
    resource_group_name = resourcegroup.resource_group_name
    start_vm_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_start_vm=requests.post(start_vm_url,headers=headers)
    print (response_start_vm.text)
    
    
#stop_vm
@operation
def stop_vm(**_):
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials='Bearer '+auth.get_token_from_client_credentials()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    resource_group_name = resourcegroup.resource_group_name
    stop_vm_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_stop_vm=requests.post(stop_vm_url,headers=headers)
    print (response_stop_vm.text)


@operation
def delete_virtual_machine(**_):
    resource_group_name = ctx.node.runtime_properties['resource_group']
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials='Bearer '+auth.get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    
    ctx.logger.info("Checking availability of virtual network: " + vm_name)
    if 1:
        try:
            ctx.logger.info("Deleting the virtual machine: " + vm_name)
            vm_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
            response_vm = requests.delete(url=vm_url,headers=headers)
            print(response_vm.text)

        except:
            ctx.logger.info("Virtual Machine " + vm_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Machine " + vm_name + " does not exist.")


@operation
def set_dependent_resources_names(azure_config,**kwargs):
    ctx.logger.info("Setting set_private_ip")
    vm_private_ip = ctx.target.instance.runtime_properties['private_ip']
    ctx.logger.info("vm_private_ip is " + vm_private_ip)
    ctx.source.instance.runtime_properties['ip'] = vm_private_ip
    ctx.source.instance.runtime_properties['resource_group'] = ctx.target.instance.runtime_properties['resource_group']
    ctx.source.instance.runtime_properties['storage_account'] = ctx.target.instance.runtime_properties['storage_account']
    ctx.source.instance.runtime_properties['vnet'] = ctx.target.instance.runtime_properties['vnet']
    ctx.source.instance.runtime_properties['publicip'] = ctx.target.instance.runtime_properties['publicip']
    ctx.source.instance.runtime_properties['nic'] = ctx.target.instance.runtime_properties['nic']



def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
