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
import auth
import utils
import os
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation

@operation
def creation_validation(**_):
    for property_key in constants.VM_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
   
@operation
def create_vm(**_):
    random_suffix_value = utils.random_suffix_generator()
    vm_name = ctx.node.properties[constants.VM_PREFIX]+random_suffix_value
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    location = ctx.node.properties['location']
    nic_name = ctx.instance.runtime_properties[constants.NIC_KEY]
    credentials = 'Bearer ' + auth.get_auth_token()
    subscription_id = ctx.node.properties['subscription_id']
    headers = {"Content-Type": "application/json", "Authorization": credentials}

    try:
        ctx.logger.info("Creating new virtual machine: ".format(vm_name))
        virtual_machine_params = json.dumps(
        {
            "id": "/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Compute/virtualMachines/"+vm_name,
            "name": vm_name,
            "type": "Microsoft.Compute/virtualMachines",
            "location": location,
            "properties": {
                "hardwareProfile": {
                    "vmSize": ctx.node.properties['vm_size']
                },
                "osProfile": {
                    "computername": vm_name,
                    "adminUsername": ctx.node.properties['ssh_username'],
                    "linuxConfiguration": {
                        "disablePasswordAuthentication": "true",
                        "ssh": {
                            "publicKeys": [
                                {
                                    "path": "/home/"+ctx.node.properties['ssh_username']+"/.ssh/authorized_keys",
                                    "keyData": ctx.node.properties['key_data']
                                }
                             ]
                         }
                     }
                },
                "storageProfile": {
                    "imageReference": {
                        "publisher": ctx.node.properties['image_reference_publisher'],
                        "offer": ctx.node.properties['image_reference_offer'],
                        "sku": ctx.node.properties['image_reference_sku'],
                        "version": constants.vm_version
                    },
                    "osDisk": {
                        "name": constants.os_disk_name+random_suffix_value,
                        "vhd": {
                            "uri": "http://"+storage_account_name+".blob.core.windows.net/vhds/osdisk{}.vhd".format(random_suffix_value)
                        },
                        "caching": "ReadWrite",
                        "createOption": "FromImage"
                    }
                },
                "networkProfile": {
                    "networkInterfaces": [
                        {
                            "id": "/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Network/networkInterfaces/"+nic_name
                        }
                    ]}
                }
            })
        virtual_machine_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
        response_vm = requests.put(url=virtual_machine_url, data=virtual_machine_params, headers=headers)
        if response_vm.text:
            ctx.logger.info("create_vm:{} response_vm.text is {}".format(vm_name, response_vm.text))
            if utils.request_failed("{}:{}".format('create_vm', vm_name), response_vm):
                raise NonRecoverableError("Virtual Machine {} could not be created".format(vm_name))
        elif response_vm:
            ctx.logger.info("create_vm:{} response_vm is {}".format(vm_name, response_vm))
        else:
            ctx.logger.info("create_vm:{} response_vm is empty".format(vm_name))
        ctx.instance.runtime_properties[constants.VM_KEY] = vm_name
    except:
        ctx.logger.info("Virtual Machine {} could not be created".format(vm_name))
        raise NonRecoverableError("Virtual Machine {} could not be created".format(vm_name))


@operation
def start_vm(**_):
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    if constants.REQUEST_ACCEPTED in ctx.instance.runtime_properties:
        if _vm_is_started(headers, vm_name, subscription_id, resource_group_name):
            _set_public_ip(subscription_id, resource_group_name, headers)
        else:
            raise RecoverableError("start_vm: request already accepted - Waiting for vm {} to start...".format(vm_name))
    else:
        if _start_vm_call(headers, vm_name, subscription_id, resource_group_name):
            if _vm_is_started(headers, vm_name, subscription_id, resource_group_name):
                _set_public_ip(subscription_id, resource_group_name, headers)
            else:
                raise RecoverableError("start_vm: vm {} is not ready yet ...".format(vm_name))
        else:
            raise RecoverableError("start_vm: Failed to start {} ".format(vm_name))


@operation
def stop_vm(**_):
    subscription_id = ctx.node.properties['subscription_id']
    
    credentials = 'Bearer ' + auth.get_auth_token()
    
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    stop_vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_stop_vm = requests.post(stop_vm_url,headers=headers)
    print (response_stop_vm.text)


@operation
def delete_virtual_machine(**_):
    delete_current_virtual_machine()
    utils.clear_runtime_properties()


def delete_current_virtual_machine(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    subscription_id = ctx.node.properties['subscription_id']
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]

    try:
        ctx.logger.info("Deleting the virtual machine: {}".format(vm_name))
        vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
        response_vm = requests.delete(url=vm_url, headers=headers)
        print(response_vm.text)

    except:
        ctx.logger.info("Virtual Machine {} could not be deleted".format(vm_name))


@operation
def set_dependent_resources_names(azure_config, **kwargs):

    if constants.STORAGE_ACCOUNT_KEY in ctx.target.instance.runtime_properties:
        ctx.source.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = ctx.target.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
        ctx.logger.info("{} is {}".format(constants.STORAGE_ACCOUNT_KEY, ctx.target.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]))
        ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
        ctx.logger.info("{} is {}".format(constants.RESOURCE_GROUP_KEY, ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]))
        return

    if constants.PRIVATE_IP_ADDRESS_KEY in ctx.target.instance.runtime_properties:
        ctx.logger.info("Setting set_private_ip")
        vm_private_ip = ctx.target.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY]
        ctx.logger.info("vm_private_ip is {}".format(vm_private_ip))
        ctx.source.instance.runtime_properties['ip'] = vm_private_ip
        ctx.source.instance.runtime_properties['host_ip'] = vm_private_ip
        ctx.logger.info("host_ip is {}".format(vm_private_ip))

    if constants.PUBLIC_IP_KEY in ctx.target.instance.runtime_properties:
        ctx.logger.info("{} is {}".format(constants.PUBLIC_IP_KEY, ctx.target.instance.runtime_properties[constants.PUBLIC_IP_KEY]))
        ctx.source.instance.runtime_properties[constants.PUBLIC_IP_KEY] = ctx.target.instance.runtime_properties[constants.PUBLIC_IP_KEY]
    else:
        ctx.logger.info("{} is NOT in runtime props ".format(constants.PUBLIC_IP_KEY))

    if constants.NIC_KEY in ctx.target.instance.runtime_properties:
        ctx.source.instance.runtime_properties[constants.NIC_KEY] = ctx.target.instance.runtime_properties[constants.NIC_KEY]
        ctx.logger.info("{} is {}".format(constants.NIC_KEY, ctx.target.instance.runtime_properties[constants.NIC_KEY]))
    
    if constants.SECURITY_GROUP_KEY in ctx.target.instance.runtime_properties:
        ctx.source.instance.runtime_properties[constants.SECURITY_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
        ctx.logger.info("{} is {}".format(constants.SECURITY_GROUP_KEY, ctx.target.instance.runtime_properties[constants.SECURITY_GROUP_KEY]))
        


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _set_public_ip(subscription_id, resource_group_name, headers):
    if constants.PUBLIC_IP_KEY in ctx.instance.runtime_properties:
        public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
        get_pip_info_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
        raw_response = requests.get(url=get_pip_info_url, headers=headers)
        ctx.logger.info("raw_response : {}".format(str(raw_response)))
        response_get_info = raw_response.json()
        ctx.logger.info("response_get_info : {}".format(str(response_get_info)))
        curr_properties = response_get_info[u'properties']
        ctx.logger.info("currProperties : {}".format(str(curr_properties)))
        curr_ip_address = curr_properties[u'ipAddress']
        ctx.logger.info("Current public IP address is {}".format(str(curr_ip_address)))
        ctx.instance.runtime_properties['vm_public_ip'] = curr_ip_address
        ctx.instance.runtime_properties['public_ip'] = curr_ip_address


def _vm_is_started(headers, vm_name, subscription_id, resource_group_name):
    ctx.logger.info("In _vm_is_started checking {}".format(vm_name))
    check_vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?api-version='+constants.api_version
    check_vm_response = requests.get(check_vm_url, headers=headers)
    return utils.resource_provisioned('_vm_is_started',vm_name, check_vm_response)


def _start_vm_call(headers, vm_name, subscription_id , resource_group_name):
    ctx.logger.info("In _vm_is_started checking {}".format(vm_name))
    start_vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_start_vm = requests.post(start_vm_url, headers=headers)
    if response_start_vm.text:
        ctx.logger.info("_start_vm_call {} response_start_vm.text is {}".format(vm_name, response_start_vm.text))
        ctx.logger.info("_start_vm_call:{} status code is {}".format(vm_name, response_start_vm.status_code))
        if utils.request_failed("{}:{}".format('_start_vm_call', vm_name), response_start_vm):
            raise NonRecoverableError("Virtual Machine {} could not be started".format(vm_name))
    if response_start_vm.status_code:
        ctx.logger.info("_start_vm_call:{} - Status code is {}".format(vm_name, response_start_vm.status_code))
        if response_start_vm.status_code == 202:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        elif response_start_vm.status_code == 200:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        else:
            return False
    raise NonRecoverableError("_start_vm_call:{} - No Status code for vm {}".format(vm_name, response_start_vm.status_code))
