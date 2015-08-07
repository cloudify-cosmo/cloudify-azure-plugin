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
def list_all_rg(**_):
    list_rg=requests.get(url=constants.list_resource_group_url, headers=constants.headers)
    print list_rg.text

    #list_all_rg=      #access name
    #print final_list_of_names


@operation
def delete_resource_group(**_):
    resource_group_name = ctx.node.properties['resource_group_name']
    if resource_group_name in [resource_group_name for rg in list_all_rg()]:
        try:
            ctx.logger.info("Deleting Resource Group: " + resource_group_name)
            response_rg = requests.delete(url=constants.resource_group_url, headers=constants.headers)
            print(response_rg.text)
        except WindowsAzureMissingResourceError:
            ctx.logger.info("Resource Group" +  resource_group_name + "could not be deleted." )
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group '%s' does not exist" + resource_group_name)




#storage_group
@operation
def list_all_sg(**_):
    list_sg = requests.get(url=constants.list_storage_account_url, headers = constants.headers)
    print list_sg.text
    #sg_account_name_list= #extract sg_name
    #return sg_account_name_list

@operation
def delete_storage_account(**_):
    storage_account_name = ctx.node.properties['storage_account_name']
    ctx.logger.info("Deleting Storage Account"+storage_account_name)
    if storage_account_name in [storage_account_name for sa in list_all_sg()]:
        try:
            response_sg = requests.delete(url=constants.storage_account_url,headers=constants.headers)
            print response_sg.text

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Storage Account " + storage_account_name + " could not be deleted.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + " does not exist.")



#vnet

@operation
def list_all_vnet(**_):
    list_vnet = requests.get(url=constants.list_vnet_url, headers = constants.headers)
    print list_vnet.text
    #vnet_list= #extract vnet_name
    #return vnet_list
list_all_vnet()

@operation
def delete_vnet(**_):
    vnet_name = ctx.node.properties['vnet_name']
    ctx.logger.info("Checking availability of virtual network: " + vnet_name)
    if vnet_name  in [vnet_name for vnet in list_all_vnet()]:
        try:
            ctx.logger.info("Deleting the virtual network: " + vnet_name)
            response_vnet = requests.delete(url=constants.vnet_url,headers=constants.headers)
            print response_vnet.text

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Virtual Network " + vnet_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Network " + vnet_name + " does not exist.")



#nic:
@operation
def delete_nic(**_):
    ctx.logger.info("Deleting NIC")
    response_nic = requests.delete(url=constants.nic_url,headers=constants.headers)
    print(response_nic.text)

"""
#load_balancer
lb_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/microsoft.network/ loadBalancers/mdloadbalancer/Subnet-1?api-version=2015-05-01-preview'
response_lb=requests.delete(url=lb_url,headers=headers)
print(response_lb.text)

"""

#virtual_machine
@operation
def list_all_vms(**_):
    list_vms = requests.get(url=constants.list_vms_url, headers = constants.headers)
    print list_vms.text
    #vm_list= #extract vm_name
   #return vm_list


@operation
def delete_virtual_machine(**_):
    vm_name = ctx.node.properties['vm_name']
    ctx.logger.info("Checking availability of virtual network: " + vm_name)
    if vm_name in [vm_name for vm in list_all_vnet()]:
        try:
            ctx.logger.info("Deleting the virtual machine: " + vm_name)
            response_vm = requests.delete(url=constants.vm_url,headers=constants.headers)
            print(response_vm.text)

        except WindowsAzureMissingResourceError:
            ctx.logger.info("Virtual Machine " + vm_name + " could not be deleted.")
        sys.exit(1)
    else:
        ctx.logger.info("Virtual Machine " + vm_name + " does not exist.")





