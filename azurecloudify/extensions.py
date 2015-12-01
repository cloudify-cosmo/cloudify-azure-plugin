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
import json
import constants
import sys
import os
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import utils
import auth
import azurerequests


@operation
def creation_validation(**_):
    for property_key in constants.CUSTOM_SCRIPT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_custom_script(**_):
    utils.set_runtime_properties_from_file()
    custom_script_name = constants.CUSTOM_SCRIPT_PREFIX+utils.random_suffix_generator()
    ctx.instance.runtime_properties[constants.CUSTOM_SCRIPT_KEY] = custom_script_name
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
           "fileUris": [file_uri],
           "commandToExecute": command
         }
       }
    }
    )
    response_as = requests.put(url=custom_script_url, data=custom_script_params, headers=headers) 
    print response_as.text 


@operation
def verify_provision(start_retry_interval, **kwargs):

    custom_script_name = ctx.instance.runtime_properties[constants.CUSTOM_SCRIPT_KEY]
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]
    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the custom script ({0}), of VM {1} to be provisioned'.format(custom_script_name, vm_name),
                retry_after=start_retry_interval)


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY, constants.VM_KEY])


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def get_provisioning_state(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]
    custom_script_name = ctx.instance.runtime_properties[constants.CUSTOM_SCRIPT_KEY]

    ctx.logger.info("Searching for custom script {0} for VM {1}".format(custom_script_name, vm_name))
    headers, location, subscription_id = auth.get_credentials()

    custom_script_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Compute/" \
                          "virtualMachines/{3}/extensions/{4}?api-version={5}".format(constants.azure_url,
                                subscription_id, resource_group_name, vm_name, custom_script_name,
                                constants.api_version)

    return azurerequests.get_provisioning_state(headers, resource_group_name, custom_script_url)