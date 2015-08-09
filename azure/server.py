
import requests
import json
from azure import constants
from azure import utils
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

    resource_group_name = ctx.node.properties['resource_group_name']
    location = ctx.node.properties['location']
    resource_group_url = constants.resource_group_url
    ctx.logger.info("Checking availability of resource_group: " + resource_group_name)

    if resource_group_name not in [resource_group_name for rg in utils.list_all_rg()]:
        try:
            ctx.logger.info("Creating new Resource group: " + resource_group_name)
            rg_params=json.dumps({"name":resource_group_name,"location": location})
            response_rg = requests.put(url=resource_group_url, data=rg_params, headers=constants.headers)
            print response_rg.text
        except WindowsAzureConflictError:
            ctx.logger.info("Resource Group " + constants.resource_group_name + " could not be created")
            sys.exit(1)
    else:
        ctx.logger.info("Resource Group " + constants.resource_group_name + " has already been provisioned")

@operation
def resource_group_creation_validation(**_):
    resource_group_name = ctx.node.properties['resource_group_name']
    if resource_group_name in resource_group_name in [resource_group_name for rg in utils.list_all_rg()]:
        ctx.logger.info("Resource group: " + resource_group_name + " successfully created.")
    else:
        ctx.logger.info("Resource Group " + resource_group_name + " creation validation failed.")
        sys.exit(1)




@operation
def create_storage_account(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)
    storage_account_name = ctx.node.properties['storage_account_name']
    ctx.logger.info("Checking availability of storage account: " + storage_account_name)
    if storage_account_name not in [storage_account_name for sg in utils.list_all_sg()]:
        try:
            ctx.logger.info("Creating new storage account: " + storage_account_name)
            sg_params=json.dumps({"properties": {"accountType": constants.storage_account_type,}, "location": constants.location})
            response_sg = requests.put(url=constants.storage_account_url, data=sg_params, headers=constants.headers)
            print response_sg.text
        except WindowsAzureConflictError:
            ctx.logger.info("Storage Account " + storage_account_name + "could not be created.")
            sys.exit(1)
    else:
        ctx.logger.info("Storage Account " + storage_account_name + "has already been provisioned by another user.")

@operation
def storage_account_creation_validation(**_):
    storage_account_name = ctx.node.properties['storage_account_name']
    if storage_account_name in [storage_account_name for sg in utils.list_all_sg()]:
        ctx.logger.info("Storage account: " + storage_account_name + " successfully created.")
    else:
        ctx.logger.info("Storage Account " + storage_account_name + " creation validation failed..")
        sys.exit(1)




@operation
#vnet:
def create_vnet(**_):
    for property_key in constants.VNET_REQUIRED_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)

vnet_name = ctx.node.properties['vnet_name']
location = ctx.node.properties['location']
vnet_url = constants.vnet_url
ctx.logger.info("Checking availability of virtual network: " + vnet_name)

if vnet_name not in [vnet_name for vnet in utils.list_all_vnet()]:
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
    vnet_name = ctx.node.properties['vnet_name']
    if vnet_name in [vnet_name for vnet in utils.list_all_vnet()]:
        ctx.logger.info("Virtual Network: " + vnet_name + " successfully created.")
    else:
        ctx.logger.info("Virtual Network " + vnet_name + " creation validation failed.")
        sys.exit(1)

@operation
#nic:
def create_nic():
    nic_name = ctx.node.properties['nic_name']
    nic_params=json.dumps({
                "location":constants.location,
                "properties":{
                    "ipConfigurations":[
                        {
                            "name":constants.ip_config_name,
                            "properties":{
                                "subnet":{
                                    "id":"/subscriptions/"+constants.subscription_id+"/resourceGroups/maryland/providers/Microsoft.Network/virtualNetworks/mdvnet/subnets/Subnet-1"
                                },
                                "privateIPAllocationMethod":"Dynamic",
                            }
                        }
                    ],
                }
            })
    response_nic = requests.put(url=constants.nic_url, data=nic_params, headers=constants.headers)
    print(response_nic.text)


#virtualmachine:

@operation
def create_vm(**_):
    for property_key in constants.VM_REQUIRED_PROPERTIES:
        utils.validate_node_property(property_key, ctx.node.properties)

        vm_name = ctx.node.properties['vm_name']
        ctx.logger.info("Checking availability of virtual network: " + vm_name)
        if vm_name not in [vm_name for vm in utils.list_all_virtual_machines()]:
            try:
                ctx.logger.info("Creating new virtual machine: " + vm_name)

                vm_params_1=json.dumps(
                    {
                        "id":"/subscriptions/"+constants.subscription_id+"/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/new",
                        "name":"new",
                        "type":constants.vm_type,
                        "location":constants.location,
                        "properties": {
                            "hardwareProfile": {
                                "vmSize": constants.vm_size
                            },
                            "osProfile": {
                                "computername": constants.computer_name,
                                "adminUsername": constants.admin_username,
                                "linuxConfiguration": {
                                    "disablePasswordAuthentication": "true",
                                    "ssh": {
                                        "publicKeys": [
                                            {
                                                "path": constants.key_path,
                                                "keyData": <RSA Public key here>}
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
                                        "uri": "http://ruchikastorage.blob.core.windows.net/vhds/osdisk.vhd"
                                    },
                                    "caching": "ReadWrite",
                                    "createOption": "FromImage"
                                }
                            },
                            "networkProfile": {
                                "networkInterfaces": [
                                    {
                                        "id": "/subscriptions/"+constants.subscription_id+"/resourceGroups/maryland/providers/Microsoft.Network/networkInterfaces/nic"
                                    }
                                ]
                            }
                        }
                    })
                response_vm = requests.put(url=constants.vm_url, data=vm_params_1, headers=constants.headers)
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








