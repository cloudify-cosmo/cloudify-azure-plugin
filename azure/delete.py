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
import json
import requests
import constants
import utils
import sys
from cloudify.exceptions import NonRecoverableError
from azure import WindowsAzureConflictError
from azure import WindowsAzureMissingResourceError
from cloudify import ctx
from cloudify.decorators import operation

#resourcegroup:

@operation
def delete_resource_group(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    if resource_group_name in [resource_group_name for rg in utils.list_all_resource_group()]:
        try:
            ctx.logger.info("Deleting Resource Group: " + resource_group_name)
            resource_group_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'?api-version='+constants.api_version
            response_rg = requests.delete(url=resource_group_url, headers=constants.headers)
            print(response_rg.text)
        except WindowsAzureMissingResourceError:
            ctx.logger.info("Resource Group" +  resource_group_name + "could not be deleted." )
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group '%s' does not exist" + resource_group_name)


#storage_group

@operation
def delete_storage_account(**_):
    storage_account_name = ctx.node.properties['vm_name']+'_storage_group'
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Deleting Storage Account"+storage_account_name)
    if storage_account_name in [storage_account_name for sa in utils.list_all_storage_account()]:
        try:
            storage_account_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
            response_sg = requests.delete(url=storage_account_url,headers=constants.headers)
            print response_sg.text

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Storage Account " + storage_account_name + " could not be deleted.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + " does not exist.")



#vnet

@operation
def delete_vnet(**_):
    vnet_name = ctx.node.properties['vm_name']+'_vnet'
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Checking availability of virtual network: " + vnet_name)
    if vnet_name  in [vnet_name for vnet in utils.list_all_virtual_networks()]:
        try:
            ctx.logger.info("Deleting the virtual network: " + vnet_name)
            vnet_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
            response_vnet = requests.delete(url=vnet_url,headers=constants.headers)
            print response_vnet.text

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Virtual Network " + vnet_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Network " + vnet_name + " does not exist.")


def delete_public_ip():
    public_ip_name = ctx.node.properties['vm_name']+'_pip'
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if public_ip_name  in [public_ip_name for pip in utils.list_all_public_ips()]:
        try:
            ctx.logger.info("Deleting Public IP")
            public_ip_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/ publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
            response_pip = requests.delete(url=public_ip_url,headers=constants.headers)
            print(response_pip.text)
        except WindowsAzureMissingResourceError:
            ctx.logger.info("Public IP " + public_ip_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Public IP " + public_ip_name + " does not exist.")



#nic:
@operation
def delete_nic(**_):
    nic_name = ctx.node.properties['vm_name']+'_nic'
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    if nic_name in [nic_name for pip in utils.list_all_nics()]:
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


#virtual_machine

@operation
def delete_virtual_machine(**_):
    vm_name = ctx.node.properties['vm_name']
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    ctx.logger.info("Checking availability of virtual network: " + vm_name)
    if vm_name in [vm_name for vm in utils.list_all_virtual_machines()]:
        try:
            ctx.logger.info("Deleting the virtual machine: " + vm_name)
            vm_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
            response_vm = requests.delete(url=vm_url,headers=constants.headers)
            print(response_vm.text)

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Virtual Machine " + vm_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Machine " + vm_name + " does not exist.")





