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

# Built-in Imports
import requests
from requests import Request,Session,Response
import json
import constants
import sys
import os
from resourcegroup import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation

@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_custom_script(**_):
    custom_script_name = ''
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    command = ''
    file_uri = ''
    vm_name = ''

    custom_script_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providersMicrosoft.Compute/virtualMachines/'+vm_name+'/extensions/'+custom_script_name+'?api-version=2015-05-01-preview'
    custom_script_params = json.dumps({ 
       "id":"/subscriptions/6f680d2a-6047-4286-876f-c0ec0b1ff1d0/resourceGroups/resource_group_h8y7t/providers/Microsoft.Compute/virtualMachines/mdgiga28b2acro/extensions/SampleCustomScript",
       "name": custom_script_name,
       "type": "Microsoft.Compute/virtualMachines/extensions",
       "location": location,
       "properties": {
         "publisher": "Microsoft.OSTCExtensions",
         "type": "CustomScriptForLinux",
         "typeHandlerVersion": "1.2",
         "settings": {
           "fileUris": [ file_uri ],
           "commandToExecute": command
         }
       }
    }
    )
    response_as = requests.put(url=custom_script_url, data=custom_script_params, headers=headers) 
    print response_as.text 
    
    
@operation
def delete_custom_script(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    custom_script_name = ''
    vm_name = ''
    delete_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/extensions/'+custom_script_name+'?api-version=2015-05-01-preview'
    response_as = requests.delete(url=delete_url, headers=headers)
    print(response_as.text)
    
    
@operation
def get_custom_script_info(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    custom_script_name = ''
    vm_name = ''
    get_info_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/extensions/'+custom_script_name+'?api-version=2015-05-01-preview'
    response_as = requests.get(url=get_info_url, headers=headers)
    print(response_as.text)
