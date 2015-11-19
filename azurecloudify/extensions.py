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
    for property_key in constants.CUSTOM_SCRIPT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_custom_script(**_):
    if 1 == 1:
        return;
    custom_script_name = constants.CUSTOM_SCRIPT_PREFIX+utils.random_suffix_generator()
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    command = ctx.node.properties['custom_script_command']
    file_uri = ctx.node.properties['custom_script_path']
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]

    custom_script_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/extensions/'+custom_script_name+'?api-version='+constants.api_version
    custom_script_params = json.dumps({ 
       "id":"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Compute/virtualMachines/"+vm_name+"/extensions/"+custom_script_name,
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
    
def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
