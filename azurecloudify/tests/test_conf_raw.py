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

###############################################################
#                     NOTE !!!
# Replace this file's name to test_conf.py prior to using it
###############################################################

PATH_TO_AZURE_CONF = "REPLACE_WITH_LOCAL_PATH"
SUBSCRIPTION_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX'
LOCATION = 'westus'
VM_PREFIX = 'testvm'
VM_SIZE = 'Standard_A2'
IMAGE_REFERENCE_PUBLISHER = 'Canonical'
IMAGE_REFERENCE_OFFER = 'UbuntuServer'
IMAGE_REFERENCE_SKU = '12.04.5-LTS'
CLIENT_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX'
USE_EXTERNAL_RESOURCE = False
TENANT_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXX'
RESOURCE_GROUP_NAME = 'testrg1'
STORAGE_ACCOUNT_NAME = 'testsa1'
VNET_NAME = 'testvnet1'
SUBNET = 'testsubnet1'
EXISTING_NIC_NAME = ''
EXISTING_PUBLIC_IP_NAME = ''
SSH_USERNAME = 'azuretest'
AAD_PASSWORD = 'my_passsword'
key_data ="  | "+ \
"   ---- BEGIN SSH2 PUBLIC KEY ----"+\
"   Comment = \"rsa-key-20150804\""+\
""+\
"   AAAAB3NzaC1yc2EAAAABJQAAAQEA0Y5tAjA2C9xPLRMMfU37J3kGUYQzRAbPu2gN"+\
"   9HKKB+/bkzEE+W9zysYgL1vu3heqUewQlnMz2G6gfDca+6FmitMpZdz8E0ZYUy4M"+\
"   CG+fWs/6xT92OsVLAi2VRgQlyGqOD+KJEZdMnIbbWyPzaLC0yaUDEUNWe2hRNkr0"+\
"   daRY21UCCZG9+zZNR4ndJWxjJyF4Om1G4R5gruickOs5yECbgEMISpENWmXATc6U"+\
"   UsVhRznp4u6iBusZO3ilH7B3YbDyGhXs4X/TcwBj6zuWaJsHXzorTL621g4Ppp4I"+\
"   g6QVQSrBpNBe2JCjou6tlGSBFm7vApUwAYaMStDzaIcLck/nUQ=="+\
"   ---- END SSH2 PUBLIC KEY ---- "


