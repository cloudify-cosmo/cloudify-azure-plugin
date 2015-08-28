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

credentials= 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSIsImtpZCI6Ik1uQ19WWmNBVGZNNXBPWWlKSE1iYTlnb0VLWSJ9.eyJhdWQiOiJodHRwczovL21hbmFnZW1lbnQuY29yZS53aW5kb3dzLm5ldC8iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9hN2Q3MTI5Ni1kNjQ3LTQ4YjktOGYzMS04NjZmYjA3ZThlZGYvIiwiaWF0IjoxNDQwNzM3MzY4LCJuYmYiOjE0NDA3MzczNjgsImV4cCI6MTQ0MDc0MTI2OCwidmVyIjoiMS4wIiwidGlkIjoiYTdkNzEyOTYtZDY0Ny00OGI5LThmMzEtODY2ZmIwN2U4ZWRmIiwib2lkIjoiMWU2Y2ZkMTAtNjRlMi00NzE5LTkzNjQtYjllNjkxYWJmOWI2IiwiZW1haWwiOiJhenVyZWRlbW9AZ2lnYXNwYWNlcy5jb20iLCJwdWlkIjoiMTAwMzAwMDA4NzZDQkUyQiIsImlkcCI6ImxpdmUuY29tIiwiYWx0c2VjaWQiOiIxOmxpdmUuY29tOjAwMDNCRkZEQTU2Njg4NTIiLCJzdWIiOiJTbm5UXy0yaGh0cTN3US1DZnRsT1diRzljR2g5S3B1UWVRME56MjJCamtzIiwiZ2l2ZW5fbmFtZSI6Ik5hdGkiLCJmYW1pbHlfbmFtZSI6IlNoYWxvbSIsIm5hbWUiOiJOYXRpIFNoYWxvbSIsImFtciI6WyJwd2QiXSwiZ3JvdXBzIjpbIjI2MmE2NjUzLTEwNmYtNGFlNi1hNDcxLTFiZWMzNDBiNjJlZSJdLCJ1bmlxdWVfbmFtZSI6ImxpdmUuY29tI2F6dXJlZGVtb0BnaWdhc3BhY2VzLmNvbSIsIndpZHMiOlsiNjJlOTAzOTQtNjlmNS00MjM3LTkxOTAtMDEyMTc3MTQ1ZTEwIl0sImFwcGlkIjoiYzQ0YjQwODMtM2JiMC00OWMxLWI0N2QtOTc0ZTUzY2JkZjNjIiwiYXBwaWRhY3IiOiIyIiwic2NwIjoidXNlcl9pbXBlcnNvbmF0aW9uIiwiYWNyIjoiMSIsImlwYWRkciI6IjIwNi4xOTYuMTg0LjgwIn0.PHNDfE8osmm19mgpwRy9lydWMHlp9triWma7A0k2GZahMwWydtmth5ydHvWZ9abldsvO5t5ON9oYEgp55RR3Rvn6CBUZu-7h9hKm1tLnVyUx0t7f-YI-wFqs8HSBo4lI3kWJRBfFrcDQq6n5RriqV96CvSgv4IlKkqvGYOsCxwincSaj87gV20YouND61S_jkR13DQM3ng6c8Sg7njeL6bdSMognwhIijUiUmMbYwzPqUWc51CUpZ_4oVAeB1bpT9fgnxwzANHWza_BVVlAzidSrIU-C0K43IVqXG08TrBPwrQnmlcrcAdXkXv2yJoNKS7wZbBOTF4_-tC_TQRIk2A'
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

RESOURCE_GROUP_REQUIRED_PROPERTIES=['vm_name','location','subscription_id']
STORAGE_ACCOUNT_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VNET_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
VM_REQUIRED_PROPERTIES = ['vm_name','vm_os_type','vm_size','subscription_id','key_data','location']
NIC_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']
PUBLIC_IP_REQUIRED_PROPERTIES = ['vm_name','location','subscription_id']




