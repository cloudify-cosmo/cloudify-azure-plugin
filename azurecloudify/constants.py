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

credentials= 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSIsImtpZCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9lOGY4M2RkZi00ZGVlLTRlMWQtYjc3YS1mZjNkZGFhZjUyZDgvIiwiaWF0IjoxNDQxMTMyMjAwLCJuYmYiOjE0NDExMzIyMDAsImV4cCI6MTQ0MTEzNjEwMCwidmVyIjoiMS4wIiwidGlkIjoiZThmODNkZGYtNGRlZS00ZTFkLWI3N2EtZmYzZGRhYWY1MmQ4Iiwib2lkIjoiMTFkMWMyNTMtOTdmZC00N2E2LWJjMWItOTRkMDI3ZTk0YWE2IiwiZW1haWwiOiJhenVyZS1jbG91ZGlmeUBnaWdhc3BhY2VzLmNvbSIsInB1aWQiOiIxMDAzMDAwMDkzNzk5RTJDIiwiaWRwIjoibGl2ZS5jb20iLCJhbHRzZWNpZCI6IjE6bGl2ZS5jb206MDAwM0JGRkRENTNEMTA1QiIsInN1YiI6InFzbGdkMHY5V2FzLTJNcjdJdktySlJjc1hlMzduQVlqLVh6V0ZxblZ1eUkiLCJnaXZlbl9uYW1lIjoiYXp1cmUtY2xvdWRpZnkiLCJmYW1pbHlfbmFtZSI6ImF6dXJlLWNsb3VkaWZ5IiwibmFtZSI6ImF6dXJlLWNsb3VkaWZ5IiwiYW1yIjpbInB3ZCJdLCJncm91cHMiOlsiMmMxNTk2YjMtMDBhOS00YmEwLWFkNjEtYTBmNDM3ZDc1MGIwIl0sInVuaXF1ZV9uYW1lIjoibGl2ZS5jb20jYXp1cmUtY2xvdWRpZnlAZ2lnYXNwYWNlcy5jb20iLCJ3aWRzIjpbIjYyZTkwMzk0LTY5ZjUtNDIzNy05MTkwLTAxMjE3NzE0NWUxMCJdLCJhcHBpZCI6ImM0NGI0MDgzLTNiYjAtNDljMS1iNDdkLTk3NGU1M2NiZGYzYyIsImFwcGlkYWNyIjoiMiIsInNjcCI6InVzZXJfaW1wZXJzb25hdGlvbiIsImFjciI6IjEiLCJpcGFkZHIiOiIyMDYuMTk2LjE4NC44NiJ9.ql5ZdUD03xeodB21m5xbFQ4-8UWmFVLmxTFLFGNiWShN1WYy_gCviXIc3hbiJIsDD3qtL9R86HA9TG5TK9W8RmdVyKAEs1cw6Bns4_yZpBD64BwFRVXP3UNnmgbZeOuPIRTIlXuBC-OPGt13hpNGvhwQd008aCqvPQEVlllqeqq3AlYU3aydQayx3PaUfAppvD4s7KDg2GADf4Tr56nD6kphFNWGu11DqhaME18QPMcK7av4dayowExQ0xjaTDkqJ6d0UCeDbWqLrWvJW_UXEoT1v7gyL6wxgHowRJRh1e2XHCDpzu5QCxdo6r3RlxUyQ0S0yGRecaUsjgFjE0b9LQ'

headers = {"Content-Type": "application/json", "Authorization": credentials}

subscription_id = 'REPLACE_WITH_SUBSCRIPTION_ID'

COMMON_REQ_PROPERTIES=['subscription_id','location']

api_version='2015-05-01-preview'
api_version_resource_group='2015-01-01'
storage_account_type = 'Standard_LRS'

vnet_address_prefixes = ["10.1.0.0/16","10.2.0.0/16"]
subnet_name = 'Subnet-1'
address_prefix = "10.1.0.0/24"
ip_config_name = 'myip1'
image_reference_publisher = 'Canonical'
image_reference_offer = 'UbuntuServer'
image_reference_sku = '14.04.2-LTS'
image_reference_version = 'latest'
os_disk_name = 'osdisk'
vm_caching = 'ReadWrite'
vm_createOption = 'FromImage'
admin_username='azuretest'
vm_version="latest"
azure_url='https://management.azure.com'
key_data= ''

RESOURCE_GROUP_REQUIRED_PROPERTIES=['vm_name','location','subscription_id']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VNET_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VM_REQUIRED_PROPERTIES = ['vm_name','vm_os_type','vm_size','subscription_id','key_data','location']
NIC_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
PUBLIC_IP_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']




