# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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
'''
    Constants
    ~~~~~~~~~
    Microsoft Azure plugin for Cloudify constants
'''

# Provider context absolute path
CONFIG_PATH = '/opt/cloudify_azure_provider.conf'
CONFIG_PATH_ENV_VAR_NAME = 'CFY_AZURE_CONFIG_PATH'

# OAuth 2.0 constants
# az cloud # endpoints.activeDirectory
OAUTH2_ENDPOINT = 'https://login.microsoftonline.com'
# az cloud # endpoints.activeDirectoryResourceId
OAUTH2_MGMT_RESOURCE = 'https://management.core.windows.net/'
OAUTH2_GRANT_TYPE = 'client_credentials'

# Connection constants
# az cloud # endpoints.resourceManager
CONN_API_ENDPOINT = 'https://management.azure.com'
# az cloud # suffixes.storageEndpoint
CONN_STORAGE_ENDPOINT = "core.windows.net"

# API version constants
# Each service has its own API version independent of any other services
API_VER_RESOURCES = '2017-05-10'
API_VER_STORAGE = '2015-06-15'
API_VER_NETWORK = '2016-03-30'
API_VER_COMPUTE = '2016-03-30'
API_VER_STORAGE_BLOB = '2015-12-11'

# Relationship constants
REL_CONTAINED_IN_RG = \
    'cloudify.azure.relationships.contained_in_resource_group'
REL_CONTAINED_IN_SA = \
    'cloudify.azure.relationships.contained_in_storage_account'
REL_CONTAINED_IN_VN = \
    'cloudify.azure.relationships.contained_in_virtual_network'
REL_CONTAINED_IN_NSG = \
    'cloudify.azure.relationships.contained_in_network_security_group'
REL_CONTAINED_IN_RT = \
    'cloudify.azure.relationships.contained_in_route_table'
REL_CONTAINED_IN_LB = \
    'cloudify.azure.relationships.contained_in_load_balancer'
REL_NIC_CONNECTED_TO_NSG = \
    'cloudify.azure.relationships.nic_connected_to_network_security_group'
REL_NIC_CONNECTED_TO_IPC = \
    'cloudify.azure.relationships.nic_connected_to_ip_configuration'
REL_IPC_CONNECTED_TO_SUBNET = \
    'cloudify.azure.relationships.ip_configuration_connected_to_subnet'
REL_IPC_CONNECTED_TO_PUBIP = \
    'cloudify.azure.relationships.ip_configuration_connected_to_public_ip'
REL_CONNECTED_TO_SA = \
    'cloudify.azure.relationships.connected_to_storage_account'
REL_CONNECTED_TO_AS = \
    'cloudify.azure.relationships.connected_to_availability_set'
REL_CONNECTED_TO_NIC = \
    'cloudify.azure.relationships.connected_to_nic'
REL_CONNECTED_TO_IPC = \
    'cloudify.azure.relationships.connected_to_ip_configuration'
REL_CONNECTED_TO_LB_BE_POOL = \
    'cloudify.azure.relationships.connected_to_lb_be_pool'
REL_CONNECTED_TO_LB_PROBE = \
    'cloudify.azure.relationships.connected_to_lb_probe'
REL_VMX_CONTAINED_IN_VM = \
    'cloudify.azure.relationships.vmx_contained_in_vm'
REL_LB_CONNECTED_TO_NIC = \
    'cloudify.azure.relationships.lb_connected_to_nic'
REL_LB_CONNECTED_TO_IPC = \
    'cloudify.azure.relationships.lb_connected_to_ip_configuration'

SECURE_KW = ['client_id', 'client_secret', 'username',
             'adminUsername', 'adminPassword', 'keyData']
