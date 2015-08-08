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



credentials = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSIsImtpZCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9hN2Q3MTI5Ni1kNjQ3LTQ4YjktOGYzMS04NjZmYjA3ZThlZGYvIiwiaWF0IjoxNDM4Mzg1MjE1LCJuYmYiOjE0MzgzODUyMTUsImV4cCI6MTQzODM4OTExNSwidmVyIjoiMS4wIiwidGlkIjoiYTdkNzEyOTYtZDY0Ny00OGI5LThmMzEtODY2ZmIwN2U4ZWRmIiwib2lkIjoiMWU2Y2ZkMTAtNjRlMi00NzE5LTkzNjQtYjllNjkxYWJmOWI2IiwiZW1haWwiOiJhenVyZWRlbW9AZ2lnYXNwYWNlcy5jb20iLCJwdWlkIjoiMTAwMzAwMDA4NzZDQkUyQiIsImlkcCI6ImxpdmUuY29tIiwiYWx0c2VjaWQiOiIxOmxpdmUuY29tOjAwMDNCRkZEQTU2Njg4NTIiLCJzdWIiOiJTbm5UXy0yaGh0cTN3US1DZnRsT1diRzljR2g5S3B1UWVRME56MjJCamtzIiwiZ2l2ZW5fbmFtZSI6Ik5hdGkiLCJmYW1pbHlfbmFtZSI6IlNoYWxvbSIsIm5hbWUiOiJOYXRpIFNoYWxvbSIsImFtciI6WyJwd2QiXSwiZ3JvdXBzIjpbIjI2MmE2NjUzLTEwNmYtNGFlNi1hNDcxLTFiZWMzNDBiNjJlZSJdLCJ1bmlxdWVfbmFtZSI6ImxpdmUuY29tI2F6dXJlZGVtb0BnaWdhc3BhY2VzLmNvbSIsIndpZHMiOlsiNjJlOTAzOTQtNjlmNS00MjM3LTkxOTAtMDEyMTc3MTQ1ZTEwIl0sImFwcGlkIjoiYzQ0YjQwODMtM2JiMC00OWMxLWI0N2QtOTc0ZTUzY2JkZjNjIiwiYXBwaWRhY3IiOiIyIiwic2NwIjoidXNlcl9pbXBlcnNvbmF0aW9uIiwiYWNyIjoiMSJ9.R9-9zHGKfpdtgqTLxbbmCvnN-rbdQIK0AhyTawG76Dv27RRHjW0Ve_2PRjnaukNtdR9F_Uft9zuZIn2_A-K3OYo2vTUdsWeftyCyTnQ-mbLNvLKwGk72Nyt1FZw7rIrbCjjh6uHBSdeawheoHuWMGf9W3fojGf_oh21jUiOatB78r5Tqil-wmlF4NYdHX718vtLo5LzgEphqwJE4xC7PrcpZo_wFikgXLqMwLh1RjUvxgfRctpVSeZFnD6RRAidZisjPbcNJ-3TRbAjjichLS8c8Dbk20tjrpplvj9dYJVeKeBNTsmst1S9Xz60mqgank9CrLGLb7mRLyjZkpH2xqQ'
headers = {"Content-Type": "application/json", "Authorization": credentials}
head = {"Authorization": credentials}


resource_group_url = 'https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland?api-version=2015-05-01-preview'

list_resource_group_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourcegroups?api-version=2015-01-01'
list_storage_account_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/Microsoft.Storage/storageAccounts?api-version=2015-05-01-preview'

storage_account_type = 'Standard_LRS'
storage_account_url = 'https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/Microsoft.Storage/storageAccounts/marylandstorage?api-version=2015-05-01-preview'

vnet_address_prefixes = ["10.1.0.0/16","10.2.0.0/16"]

subnet_name = 'Subnet-1'
address_prefix = "10.1.0.0/24"
vnet_url = 'https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/microsoft.network/virtualNetworks/mdvnet?api-version=2015-05-01-preview'
list_vnet_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/microsoft.network/virtualnetworks?api-version=2015-05-01-preview'
ip_config_name = 'myip1'
nic_url="https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/microsoft.network/networkInterfaces/myNic?api-version=2015-05-01-preview"

vm_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/virtualmachine?validating=true&api-version=2015-05-01-preview'
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
list_vms_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/Microsoft.Compute/virtualmachines?api-version=2015-05-01-preview'
vm_start_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/virtualmachine/start?api-version=2015-05-01-preview '
vm_stop_url='https://management.azure.com/subscriptions/79c57714-7a07-445e-9dd7-f3a5318bb44e/resourceGroups/maryland/providers/Microsoft.Compute/virtualMachines/virtualmachine/stop?api-version=2015-05-01-preview'
vm_type="Microsoft.Compute/virtualMachines"
computer_name='mycomputer'
admin_username='azuredemo'
key_path="/home/azuredemo/.ssh/authorized_keys"
vm_version="latest"
ubuntu_12_04_5_name="ubuntu.vm.12.04.5"


RESOURCE_GROUP_REQ_PROPERTIES=['resource_group_name','location']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['storage_account_name']
VNET_REQUIRED_PROPERTIES = ['vnet_name', 'subnet_name']
VM_REQUIRED_PROPERTIES = ['vm_name']




