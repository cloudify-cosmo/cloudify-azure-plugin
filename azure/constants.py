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

# Look at https://github.com/cloudify-cosmo/cloudify-aws-plugin/blob/1.2/ec2/constants.py

# instance module constants


subscription_id = 'REPLACE_WITH_SUBSCRIPTION_ID'
location = 'West US'


COMMON_REQ_PROPERTIES=['subscription_id','location']

credentials = <Bearer token>
headers = {"Content-Type": "application/json", "Authorization": credentials}
head = {"Authorization": credentials}


resource_group_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland?api-version=2015-05-01-preview'

list_resource_group_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourcegroups?api-version=2015-01-01'
list_storage_account_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/Microsoft.Storage/storageAccounts?api-version=2015-05-01-preview'

storage_account_type = 'Standard_LRS'
storage_account_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/Microsoft.Storage/storageAccounts/marylandstorage?api-version=2015-05-01-preview'

vnet_address_prefixes = ["10.1.0.0/16","10.2.0.0/16"]

subnet_name = 'Subnet-1'
address_prefix = "10.1.0.0/24"
vnet_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/microsoft.network/virtualNetworks/mdvnet?api-version=2015-05-01-preview'
list_vnet_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/microsoft.network/virtualnetworks?api-version=2015-05-01-preview'
ip_config_name = 'myip1'
nic_url="https://management.azure.com/subscriptions/"+subscription_id+"/resourceGroups/maryland/providers/microsoft.network/networkInterfaces/myNic?api-version=2015-05-01-preview"

vm_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/virtualmachine?validating=true&api-version=2015-05-01-preview'
vm_size = 'Standard_A0'
os_profile_computername = 'myComputer'
os_profile_adminUsername = 'adminUser'
os_profile_adminPassword = 'Password1'
image_reference_publisher = 'Canonical'
image_reference_offer = 'UbuntuServer'
image_reference_sku = '14.04.2-LTS'
image_reference_version = 'latest'
os_disk_name = 'osdisk'
os_disk_uri = 'http://marylandstorage.blob.core.windows.net/vhds/osdisk.vhd'
vm_caching = 'ReadWrite'
vm_createOption = 'FromImage'
list_vms_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/Microsoft.Compute/virtualmachines?api-version=2015-05-01-preview'
vm_start_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/virtualmachine/start?api-version=2015-05-01-preview '
vm_stop_url='https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/virtualmachine/stop?api-version=2015-05-01-preview'
vm_type="Microsoft.Compute/virtualMachines"
computer_name='mycomputer'
admin_username='azuretest'
key_path="/home/azuredemo/.ssh/authorized_keys"
vm_version="latest"
ubuntu_12_04_5_name="ubuntu.vm.12.04.5"


RESOURCE_GROUP_REQ_PROPERTIES=['resource_group_name','location']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['storage_account_name']
VNET_REQUIRED_PROPERTIES = ['vnet_name', 'subnet_name']
VM_REQUIRED_PROPERTIES = ['vm_name']




