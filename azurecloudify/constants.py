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

credentials ='Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSIsImtpZCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9lOGY4M2RkZi00ZGVlLTRlMWQtYjc3YS1mZjNkZGFhZjUyZDgvIiwiaWF0IjoxNDQxNDgwNDMxLCJuYmYiOjE0NDE0ODA0MzEsImV4cCI6MTQ0MTQ4NDMzMSwidmVyIjoiMS4wIiwidGlkIjoiZThmODNkZGYtNGRlZS00ZTFkLWI3N2EtZmYzZGRhYWY1MmQ4Iiwib2lkIjoiNDg0ODI0YzktZWY5ZC00NmFjLThjMjktNWQxZTg0ZjI5YmFhIiwic3ViIjoiNDg0ODI0YzktZWY5ZC00NmFjLThjMjktNWQxZTg0ZjI5YmFhIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvZThmODNkZGYtNGRlZS00ZTFkLWI3N2EtZmYzZGRhYWY1MmQ4LyIsImFwcGlkIjoiNGRlNDQ3NTAtMmM1OC00MDdlLTg1MDQtMDhkOWMyZTkxMjU0IiwiYXBwaWRhY3IiOiIxIn0.c-uox0JLR9edeuJTEZs3wa6dI8ct2uOrFayf3OY04p8y-PA-g7XnbgKgwNtJ0W3-hiTmdgiFhRol0fM6dR82AgRM5H5IYxL_rp_weTa7PNpMc9BDDHIEbdsM9tzaCvZBJJTlyMTA1ucTFuANYlL_eHY4BkIpW2R21qtO4ozx41AZp2QWJ5GytWTXSVsMxCa_UrM_boVaQgOWzROZw6bi6Rqg4PrxpMb87Ca3R_Bwju2eEuAF2K8qGuGcGSwK1zvWw7b1hVrKh6ll7SQfdapTdNW42haW6MzoBsDcWmnwPbnOz0BzYurtpxA79u9xkEOL-Z_HAGWvCuOtoNzJ_1iVGA'
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


resource = 'https://management.core.windows.net/'

RESOURCE_GROUP_REQUIRED_PROPERTIES=['vm_name','location','subscription_id']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VNET_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VM_REQUIRED_PROPERTIES = ['vm_name','vm_os_type','vm_size','subscription_id','key_data','location']
NIC_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
PUBLIC_IP_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']




