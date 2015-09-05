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
key_data= """---- BEGIN SSH2 PUBLIC KEY ----
Comment: "rsa-key-20150804"
AAAAB3NzaC1yc2EAAAABJQAAAQEA0Y5tAjA2C9xPLRMMfU37J3kGUYQzRAbPu2gN
9HKKB+/bkzEE+W9zysYgL1vu3heqUewQlnMz2G6gfDca+6FmitMpZdz8E0ZYUy4M
CG+fWs/6xT92OsVLAi2VRgQlyGqOD+KJEZdMnIbbWyPzaLC0yaUDEUNWe2hRNkr0
daRY21UCCZG9+zZNR4ndJWxjJyF4Om1G4R5gruickOs5yECbgEMISpENWmXATc6U
UsVhRznp4u6iBusZO3ilH7B3YbDyGhXs4X/TcwBj6zuWaJsHXzorTL621g4Ppp4I
g6QVQSrBpNBe2JCjou6tlGSBFm7vApUwAYaMStDzaIcLck/nUQ==
---- END SSH2 PUBLIC KEY ----"""

resource = 'https://management.core.windows.net/'

RESOURCE_GROUP_REQUIRED_PROPERTIES=['vm_name','location','subscription_id']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VNET_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VM_REQUIRED_PROPERTIES = ['vm_name','vm_os_type','vm_size','subscription_id','key_data','location']
NIC_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
PUBLIC_IP_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']




