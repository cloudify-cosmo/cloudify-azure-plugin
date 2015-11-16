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

credentials = ''
COMMON_REQ_PROPERTIES = ['subscription_id','location']

api_version = '2015-05-01-preview'
api_version_resource_group = '2015-01-01'
api_version_network = '2015-06-15'
storage_account_type = 'Standard_LRS'

vnet_address_prefixes = ["10.1.0.0/16", "10.2.0.0/16"]
address_prefix = "10.1.0.0/24"
IP_PREFIX = 'myip1'
image_reference_version = 'latest'
os_disk_name = 'osdisk'
vm_caching = 'ReadWrite'
vm_createOption = 'FromImage'
vm_version = "latest"
azure_url = 'https://management.azure.com'
login_url = 'https://login.microsoftonline.com'
sourcePortRange = 65000
destinationPortRange = 60000
priority = 100
nsg_rule_name='my_ns_rules'
resource = 'https://management.core.windows.net/'
path_to_azure_conf = '~/azure_config.json'
path_to_local_azure_token_file = '/tmp/azure_token_file.json'

RESOURCE_GROUP_REQUIRED_PROPERTIES=['location', 'subscription_id']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['location', 'subscription_id']
VNET_REQUIRED_PROPERTIES = ['location', 'subscription_id']
VM_REQUIRED_PROPERTIES = ['vm_prefix', 'image_reference_offer', 'image_reference_publisher', 'image_reference_sku', 'vm_size', 'subscription_id', 'key_data', 'location']
NIC_REQUIRED_PROPERTIES = ['location', 'subscription_id']
PUBLIC_IP_REQUIRED_PROPERTIES = ['location', 'subscription_id']
CUSTOM_SCRIPT_REQUIRED_PROPERTIES=['location', 'subscription_id', 'custom_script_command', 'custom_script_path']

RESOURCE_GROUP_KEY = 'resource_group_key_name'
RESOURCE_GROUP_PREFIX = 'resource_group_'
EXISTING_RESOURCE_GROUP_KEY = 'existing_resource_group_name'

STORAGE_ACCOUNT_KEY = 'storage_account_key_name'
STORAGE_ACCOUNT_PREFIX = 'storageaccount'
EXISTING_STORAGE_ACCOUNT_KEY = 'existing_storage_account_name'

PRIVATE_IP_ADDRESS_KEY = 'private_ip_address_key_name'
PUBLIC_IP_KEY = 'public_ip_key_name'
PUBLIC_IP_PREFIX = 'public_ip_'
EXISTING_PUBLIC_IP_NAME = 'existing_public_ip_name'

VNET_KEY = 'vnet_key_name'
VNET_PREFIX = 'vnet_'
EXISTING_VNET_KEY = 'existing_vnet_name'

AVAILABILITY_SET_KEY = 'availability_set_key_name'
AVAILABILITY_SET_PREFIX = 'availability_set_'

SUBNET_KEY = 'subnet_key_name'
SUBNET_PREFIX = 'subnet_'

CUSTOM_SCRIPT_KEY = 'custom_script_key_name'
CUSTOM_SCRIPT_PREFIX = 'custom_script_'

DATA_DISK_KEY = 'data_disk_key_name'
DATA_DISK_PREFIX = 'data_disk_'

VM_KEY = 'vm_key_name'
VM_PREFIX = 'vm_prefix'

NIC_KEY = 'nic_key_name'
NIC_PREFIX = 'nic_'
EXISTING_NIC_KEY = 'existing_nic_name'

SECURITY_GROUP_KEY = 'security_group_key_name'
SECURITY_GROUP_PREFIX = 'security_group_'
EXISTING_SECURITY_GROUP_KEY = 'existing_security_group_name'
NSG_RULES_DESCRIPTION = 'IMPLEMENTING SECURITY GROUP RULES'

AUTH_TOKEN_VALUE = 'auth_token_value'
AUTH_TOKEN_EXPIRY = 'auth_token_expiry'

REQUEST_ACCEPTED = 'request accepted'
CREATE_RESPONSE = 'CREATE_RESPONSE'

USE_EXTERNAL_RESOURCE = 'use_external_resource'

THROW_RECOVERABLE = "1"
THROW_NON_RECOVERABLE = "2"
RETURN_STATUS_CODE = "3"
