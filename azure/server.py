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
def start(**_):
    #subscription_id = ctx.node.properties['subscription_id']
    location = ctx.node.properties['location']


@operation
def start_creation_validation(**_):
    for property_key in constants.COMMON_REQ_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)


@operation
#resourcegroup:
def create_resource_group(**_):
    for property_key in constants.RESOURCE_GROUP_REQ_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)

    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version
    ctx.logger.info("Checking availability of resource_group: " + resource_group_name)

    if resource_group_name not in [resource_group_name for rg in utils.list_all_resource_groups()]:
        try:
            ctx.logger.info("Creating new Resource group: " + resource_group_name)
            resource_group_params=json.dumps({"name":resource_group_name,"location": location})
            response_rg = requests.put(url=resource_group_url, data=resource_group_params, headers=constants.headers)
            print response_rg.text
        except WindowsAzureConflictError:
            ctx.logger.info("Resource Group " + resource_group_name + " could not be created")
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " has already been provisioned")

@operation
def resource_group_creation_validation(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if resource_group_name in resource_group_name in [resource_group_name for rg in utils.list_all_resource_groups()]:
        ctx.logger.info("Resource group: " + resource_group_name + " successfully created.")
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " creation validation failed.")
        sys.exit(1)




@operation
def create_storage_account(**_):
    location = ctx.node.properties['location']
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)
    storage_account_name = ctx.node.properties['vm_name']+'_storage_group'
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Checking availability of storage account: " + storage_account_name)
    if storage_account_name not in [storage_account_name for sg in utils.list_all_storage_accounts()]:
        try:
            ctx.logger.info("Creating new storage account: " + storage_account_name)
            storage_account_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
            storage_group_params=json.dumps({"properties": {"accountType": constants.storage_account_type,}, "location": location})
            response_sg = requests.put(url=storage_account_url, data=storage_group_params, headers=constants.headers)
            print response_sg.text
        except WindowsAzureConflictError:
            ctx.logger.info("Storage Account " + storage_account_name + "could not be created.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + "has already been provisioned by another user.")

@operation
def storage_account_creation_validation(**_):
    storage_account_name = ctx.node.properties['vm_name']+'_storage_group'
    if storage_account_name in [storage_account_name for sg in utils.list_all_storage_accounts()]:
        ctx.logger.info("Storage account: " + storage_account_name + " successfully created.")
    else:
        ctx.logger.info("Storage Account " + storage_account_name + " creation validation failed..")
        sys.exit(1)




@operation
#vnet:
def create_vnet(**_):
    for property_key in constants.VNET_REQUIRED_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    vnet_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
    ctx.logger.info("Checking availability of virtual network: " + vnet_name)

    if vnet_name not in [vnet_name for vnet in utils.list_all_vnets()]:
        try:
            ctx.logger.info("Creating new virtual network: " + vnet_name)
    
            vnet_params=json.dumps({"name":vnet_name, "location": location,"properties": {"addressSpace": {"addressPrefixes": constants.vnet_address_prefixes},"subnets": [{"name": constants.subnet_name, "properties": {"addressPrefix": constants.address_prefix}}]}})
            response_vnet = requests.put(url=vnet_url, data=vnet_params, headers=constants.headers)
            print response_vnet.text
        except WindowsAzureConflictError:
            ctx.logger.info("Virtual Network " + vnet_name + "could not be created.")
            sys.exit(1)
    else:
        ctx.logger.info("Virtual Network" + vnet_name + "has already been provisioned by another user.")
    
    
    def vnet_creation_validation(**_):
        ctx.node.properties['vm_name']+'_vnet'
        if vnet_name in [vnet_name for vnet in utils.list_all_vnets()]:
            ctx.logger.info("Virtual Network: " + vnet_name + " successfully created.")
        else:
            ctx.logger.info("Virtual Network " + vnet_name + " creation validation failed.")
            sys.exit(1)
@operation
def create_public_ip(**_):
    vm_name=ctx.node.properties['vm_name']
    public_ip_name=:vm_name+'_pip'
    subscription_id = ctx.node.properties['subscription_id']
    location = ctx.node.properties['location']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    public_ip_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version={api-version}='+constants.api_version
    if public_ip_name not in [public_ip_name for pip in utils.list_all_public_ips()]:
        try:
            ctx.logger.info("Associating VM with new public ip : " + public_ip_name)


            public_ip_params=json.dumps({
                    "location": location,
                    "name":public_ip_name,
                    "properties": {
                        "publicIPAllocationMethod": "Static",
                        "idleTimeoutInMinutes": 4,

                    }
                }

                )
        except WindowsAzureConflictError:
            ctx.logger.info("Public IP" + public_ip_name + "could not be created.")
        sys.exit(1)
    else:
        ctx.logger.info("Public IP" + public_ip_name + "has already been assigned to another VM")




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
    nic_url="https://management.azure.com/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version

    response_nic = requests.put(url=nic_url, data=nic_params, headers=constants.headers)
    print(response_nic.text)


#virtualmachine:

@operation
def create_vm(**_):

    for property_key in constants.VM_REQUIRED_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)
        
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    storage_account_name = ctx.node.properties['vm_name']+'_storage_group'
    location = ctx.node.properties['location']
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
    nic_name = ctx.node.properties['vm_name']+'_nic'
    vm_name = ctx.node.properties['vm_name']
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Checking availability of virtual network: " + vm_name)
    if vm_name not in [vm_name for vm in utils.list_all_virtual_machines()]:
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
                                        "keyData": "RSA Public key here"}
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
                                "uri": "http://"+storage_account_name+"blob.core.windows.net/vhds/osdisk.vhd"
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
            virtual_machine_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
            response_vm = requests.put(url=virtual_machine_url, data=virtual_machine_params, headers=constants.headers)
            print(response_vm.text)
        except WindowsAzureConflictError:
          ctx.logger.info("Virtual Machine " + vm_name + "could not be created.")
          sys.exit(1)
    else:
     ctx.logger.info("Virtual Machine" + vm_name + "has already been provisioned by another user.")


def vm_creation_validation():
    vm_name = ctx.node.properties['vm_name']
    if vm_name in [vm_name for vms in utils.list_all_virtual_machines()]:
        ctx.logger.info("Virtual Machine: " + vm_name + " successfully created.")
    else:
        ctx.logger.info("Virtual Machine " + vm_name + " creation validation failed.")
        sys.exit(1)
        
#start_vm
def start_vm(**_):
    subscription_id = ctx.node.properties['subscription_id']
    vm_name = ctx.node.properties['vm_name']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    start_vm_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_start_vm=requests.post(start_vm_url,headers=constants.headers)
    print (response_start_vm.text)
    
#stop_vm
def stop_vm(**_):
    subscription_id = ctx.node.properties['subscription_id']
    vm_name = ctx.node.properties['vm_name']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    stop_vm_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_stop_vm=requests.post(stop_vm_url,headers=constants.headers)
    print (response_stop_vm.text)
