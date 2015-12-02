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
import auth
import utils
import os
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import azurerequests

@operation
def creation_validation(**_):
    for property_key in constants.VM_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_vm(**_):
    create_a_vm()


def create_a_vm(**_):
    utils.set_runtime_properties_from_file()
    random_suffix_value = utils.random_suffix_generator()
    vm_name = ctx.node.properties[constants.VM_PREFIX]+random_suffix_value
    ctx.logger.info("Creating new virtual machine: {0}".format(vm_name))

    _set_ip_addresses()

    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    #availability_set_name = ctx.instance.runtime_properties[constants.AVAILABILITY_SET_KEY]
    availability_set_name = "To be developed by Pranjali and Vaidehi"
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    virtual_machine_params = _get_virtual_machine_params(location, random_suffix_value, resource_group_name,
                                                        storage_account_name, subscription_id, vm_name, availability_set_name)
    virtual_machine_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
    response_vm = requests.put(url=virtual_machine_url, data=virtual_machine_params, headers=headers)
    ctx.instance.runtime_properties[constants.VM_KEY] = vm_name
    return response_vm.status_code


@operation
def start_vm(start_retry_interval, **kwargs):
    start_a_vm(start_retry_interval, **kwargs)


def start_a_vm(start_retry_interval, **kwargs):

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]

    if constants.SERVER_START_INVOKED not in ctx.instance.runtime_properties:
        curr_status = get_provisioning_state()
        if curr_status != constants.SUCCEEDED:
            return ctx.operation.retry(
                message='Waiting for the server ({0}) to be provisioned'.format(vm_name),
                retry_after=start_retry_interval)
    return check_if_vm_started(resource_group_name, vm_name, start_retry_interval)


def check_if_vm_started(resource_group_name, vm_name, start_retry_interval, **kwargs):

    headers, location, subscription_id = auth.get_credentials()
    start_vm_succeeded, status_code = _start_vm_call(headers, vm_name, subscription_id, resource_group_name)
    ctx.logger.info("start_a_vm: start_vm_succeeded is {0}, status code is {1}".format(start_vm_succeeded, status_code))
    if start_vm_succeeded:
        ctx.logger.info("start_a_vm: vm has started")
        response_start_vm = ctx.instance.runtime_properties[constants.START_RESPONSE]
        ctx.logger.info("start_a_vm response_start_vm : {0}".format(response_start_vm.text))
        _set_public_ip(subscription_id, resource_group_name, headers)
        _set_private_ip(vm_name)
        return constants.OK_STATUS_CODE
    else:
        return ctx.operation.retry(message='Waiting for the server ({0}) to be started'.format(vm_name),
                                   retry_after=start_retry_interval)


@operation
def stop_vm(**_):
    stop_a_vm()


def stop_a_vm(**_):
    headers, location, subscription_id = auth.get_credentials()
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    stop_vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_stop_vm = requests.post(stop_vm_url,headers=headers)
    print (response_stop_vm.text)


@operation
def delete_virtual_machine(**_):
    delete_current_virtual_machine()
    utils.clear_runtime_properties()


def delete_a_virtual_machine(**_):
    delete_current_virtual_machine()


def delete_current_virtual_machine(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]

    try:
        ctx.logger.info("Deleting the virtual machine: {0}".format(vm_name))
        vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
        response_vm = requests.delete(url=vm_url, headers=headers)
        if response_vm.text:
            ctx.logger.info("delete_current_virtual_machine response is {0}".format(response_vm.text))
        else:
            ctx.logger.info("delete_current_virtual_machine status code is {0}".format(response_vm.status_code))
    except:
        ctx.logger.info("Virtual Machine {0} could not be deleted".format(vm_name))


@operation
def set_storage_account_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file(required_keys=[constants.RESOURCE_GROUP_KEY, constants.STORAGE_ACCOUNT_KEY])


@operation
def set_nic_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file(required_keys=None, prefixed_keys=[constants.PUBLIC_IP_KEY, constants.PRIVATE_IP_ADDRESS_KEY, constants.NIC_KEY], need_suffix=None)


@operation
def set_data_disks(azure_config, **kwargs):
    # This should be per disk issue #31
    utils.write_target_runtime_properties_to_file(required_keys=None, prefixed_keys=[constants.DISK_SIZE_KEY, constants.DATA_DISKS], need_suffix=None)


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _set_private_ip(vm_name):
    vm_private_ip = utils.key_in_runtime(constants.PRIVATE_IP_ADDRESS_KEY, ends_with_key=False,
                                         starts_with_key=True, return_value=True)
    if vm_private_ip:
        ctx.logger.info("Setting {0} private ip address".format(vm_name))
        ctx.logger.info("vm_private_ip is {0}".format(vm_private_ip))

        # Which one of the following two is required ?
        ctx.instance.runtime_properties['ip'] = vm_private_ip
        ctx.instance.runtime_properties['host_ip'] = vm_private_ip


def _set_public_ip(subscription_id, resource_group_name, headers):
    if constants.PUBLIC_IP_KEY in ctx.instance.runtime_properties:
        public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
        get_pip_info_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
        raw_response = requests.get(url=get_pip_info_url, headers=headers)
        ctx.logger.info("raw_response : {0}".format(str(raw_response)))
        response_get_info = raw_response.json()
        ctx.logger.info("response_get_info : {0}".format(str(response_get_info)))
        curr_properties = response_get_info[u'properties']
        ctx.logger.info("currProperties : {0}".format(str(curr_properties)))
        curr_ip_address = curr_properties[u'ipAddress']
        ctx.logger.info("Current public IP address is {}".format(str(curr_ip_address)))
        ctx.instance.runtime_properties['vm_public_ip'] = curr_ip_address
        ctx.instance.runtime_properties['public_ip'] = curr_ip_address


def _set_ip_addresses():
    current_public_ip_key = None
    current_private_ip_key = None
    private_ip_keys = []
    for current_key in ctx.instance.runtime_properties:
        if current_key.startswith(constants.PUBLIC_IP_KEY):
            public_key_instance_id = current_key.split(constants.PUBLIC_IP_KEY)[1]
            current_public_ip_key = ctx.instance.runtime_properties[current_key]
        elif current_key.startswith(constants.PRIVATE_IP_ADDRESS_KEY):
            private_ip_keys.append(current_key)
            current_private_ip_key = current_key

    if current_public_ip_key is not None:
        ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY] = current_public_ip_key

    if len(private_ip_keys) > 1:
        # There are two private IP addresses, so the one which doesn't correspond to the
        # public IP address, will be used
        for current_key in private_ip_keys:
            private_key_instance_id = current_key.split(constants.PRIVATE_IP_ADDRESS_KEY)[1]
            if private_key_instance_id != public_key_instance_id:
                ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY] = ctx.instance.runtime_properties[current_key]
                return
    else:
        ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY] = current_private_ip_key


def _start_vm_call(headers, vm_name, subscription_id, resource_group_name):
    ctx.logger.info("In _start_vm_call starting {0}".format(vm_name))
    start_vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_start_vm = requests.post(start_vm_url, headers=headers)
    ctx.instance.runtime_properties[constants.SERVER_START_INVOKED] = True
    if response_start_vm.status_code:
        status_code = response_start_vm.status_code
        ctx.logger.info("_start_vm_call:{0} - Status code is {1}".format(vm_name, response_start_vm.status_code))
        if response_start_vm.status_code in [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE]:
            ctx.logger.info("_start_vm_call: VM has started")
            ctx.instance.runtime_properties[constants.START_RESPONSE] = response_start_vm
            ctx.logger.info("_start_vm_call: response_start_vm is {0}".format(response_start_vm.text))
            return True, status_code
    return False, constants.NA_CODE


def _get_virtual_machine_params(location, random_suffix_value, resource_group_name, storage_account_name,
                               subscription_id, vm_name, availability_set_name):
    ctx.logger.info("In _get_virtual_machine_params vm:{0} b4 _get_vm_base_json".format(vm_name))
    vm_json = _get_vm_base_json(location, random_suffix_value, resource_group_name, storage_account_name,
                                subscription_id, vm_name, availability_set_name)

    ctx.logger.info("In _get_virtual_machine_params vm:{0} b4 _set_network_json".format(vm_name))
    _set_network_json(vm_json, subscription_id, resource_group_name)
    ctx.logger.info("In _get_virtual_machine_params vm:{0} b4 _set_data_disk_json".format(vm_name))
    _set_data_disk_json(vm_json, storage_account_name)
    ctx.logger.info("get_virtual_machine_params:{0} {1}".format(vm_name, json.dumps(vm_json)))
    return json.dumps(vm_json)


def _set_network_json(vm_json, subscription_id, resource_group_name):
    vm_properties = vm_json['properties']
    network_profile = vm_properties['networkProfile']
    network_interfaces = network_profile['networkInterfaces']
    for curr_key in ctx.instance.runtime_properties:
        if curr_key.startswith(constants.NIC_KEY):
            nic_name = ctx.instance.runtime_properties[curr_key]
            curr_interface = {
                "id": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/networkInterfaces/{2}".format(subscription_id, resource_group_name, nic_name)
            }
            interface_properties = {}
            if curr_key.endswith(constants.PUBLIC_IP_KEY):
                interface_properties['primary'] = 'true'
            else:
                interface_properties['primary'] = 'false'
            curr_interface['properties'] = interface_properties
            network_interfaces.append(curr_interface)


def _set_data_disk_json(vm_json, storage_account_name):
    vm_properties = vm_json['properties']
    storage_profile = vm_properties['storageProfile']
    if constants.DATA_DISKS in storage_profile:
        return

    storage_profile[constants.DATA_DISKS] = []
    data_disks = storage_profile[constants.DATA_DISKS]
    lun = 0
    for curr_key in ctx.instance.runtime_properties:
        if curr_key.startswith(constants.DATA_DISK_KEY):
            disk_name = ctx.instance.runtime_properties[curr_key]
            vhd_uri = "https://{0}.blob.core.windows.net/vhds/{1}.vhd".format(storage_account_name, disk_name)
            # Later make this property per disk issue #31
            disk_size = ctx.instance.runtime_properties[constants.DISK_SIZE_KEY]
            curr_disk = {
                "lun": lun,
                "name": disk_name,
                "createOption": "Empty",
                "vhd": {
                    "uri": vhd_uri
                },
                "caching": "None",
                "diskSizeGB": disk_size
            }
            data_disks.append(curr_disk)
            lun += 1


def _get_vm_base_json(location, random_suffix_value, resource_group_name, storage_account_name, subscription_id,
                      vm_name,availability_set_name):
    return {
        "id": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Compute/virtualMachines/{2}".format(
            subscription_id, resource_group_name, vm_name),
        "name": vm_name,
        "type": "Microsoft.Compute/virtualMachines",
        "location": location,
        "properties": {
# To be developed by Pranjali and Vaidehi
#            "availabilitySet": {
#                "id": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Compute/availabilitySets/{2}".format(subscription_id, resource_group_name, availability_set_name)
#            },
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
                                "path": "/home/{0}/.ssh/authorized_keys".format(ctx.node.properties['ssh_username']),
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
                    "name": "{0}{1}".format(constants.os_disk_name, random_suffix_value),
                    "vhd": {
                        "uri": "http://{0}.blob.core.windows.net/vhds/osdisk{1}.vhd".format(storage_account_name,
                                                                                            random_suffix_value)
                    },
                    "caching": "ReadWrite",
                    "createOption": "FromImage"
                }
            },
            "networkProfile": {
                "networkInterfaces": []
            }
        }
    }


def get_provisioning_state(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]

    ctx.logger.info("Searching for {0}".format(vm_name))
    headers, location, subscription_id = auth.get_credentials()

    virtual_machine_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Compute/" \
                          "virtualMachines/{3}?validating=true&api-version={4}".format(constants.azure_url,
                                subscription_id, resource_group_name, vm_name, constants.api_version)
    return azurerequests.get_provisioning_state(headers, resource_group_name, virtual_machine_url)
