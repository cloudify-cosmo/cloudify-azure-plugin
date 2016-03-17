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
import auth
import utils
from cloudify import ctx
from cloudify.decorators import operation
import azurerequests


@operation
def creation_validation(**_):
    for property_key in constants.VM_REQUIRED_PROPERTIES:
        utils.validate_node_properties(property_key, ctx.node.properties)


@operation
def create_vm(**_):
    create_a_vm()


def create_a_vm(**_):
    utils.set_runtime_properties_from_file()
    random_suffix_value = utils.random_suffix_generator()
    vm_name = ctx.node.properties[constants.VM_PREFIX]+random_suffix_value
    ctx.logger.info("Creating new virtual machine: {0}".format(vm_name))

    _set_ip_addresses_keys(vm_name)

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
    return start_a_vm(start_retry_interval, **kwargs)


def start_a_vm(start_retry_interval, **kwargs):

    resource_group_name = ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vm_name = ctx.source.instance.runtime_properties[constants.VM_KEY]

    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the server ({0}) to be provisioned'.format(vm_name),
            retry_after=start_retry_interval)

    headers, location, subscription_id = auth.get_credentials()
    start_vm_succeeded, status_code = _start_vm_call(headers, vm_name, subscription_id, resource_group_name)
    ctx.logger.info("start_a_vm: start_vm_succeeded is {0}, status code is {1}".format(start_vm_succeeded, status_code))
    ctx.source.instance.runtime_properties[constants.SERVER_STARTED] = start_vm_succeeded
    return constants.OK_STATUS_CODE


@operation
def check_if_vm_started(start_retry_interval, **kwargs):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]

    start_vm_succeeded = ctx.instance.runtime_properties[constants.SERVER_STARTED]
    headers, location, subscription_id = auth.get_credentials()
    if not start_vm_succeeded:
        start_vm_succeeded, status_code = _start_vm_call(headers, vm_name, subscription_id, resource_group_name)
        ctx.logger.info("set_ips: start_vm_succeeded is {0}, status code is {1}".format(start_vm_succeeded, status_code))
        if start_vm_succeeded:
            ctx.instance.runtime_properties[constants.SERVER_STARTED] = True
            ctx.logger.info("set_ips: vm has started")
        else:
            return ctx.operation.retry(message='Waiting for the server ({0}) to be started'.format(vm_name),
                                   retry_after=start_retry_interval)
    else:
        ctx.logger.info("set_ips: vm has already started")

    _set_public_ip(subscription_id, resource_group_name, headers)
    return constants.OK_STATUS_CODE


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


def _delete_vm_and_disks(start_retry_interval=30, **kwargs):
    delete_current_virtual_machine(start_retry_interval, **kwargs)
    _delete_os_disk()
    _delete_data_disks()


@operation
def delete_virtual_machine(start_retry_interval=30, **kwargs):
    _delete_vm_and_disks(start_retry_interval, **kwargs)
    utils.clear_runtime_properties()


def delete_a_virtual_machine(start_retry_interval=30, **kwargs):
    _delete_vm_and_disks(start_retry_interval, **kwargs)


def delete_current_virtual_machine(start_retry_interval=30, **kwargs):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    vm_name = ctx.instance.runtime_properties[constants.VM_KEY]
    ctx.instance.runtime_properties[constants.RESOURCE_NOT_DELETED] = True

    try:
        ctx.logger.info("Deleting the virtual machine: {0}".format(vm_name))
        vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'?validating=true&api-version='+constants.api_version
        response_vm = requests.delete(url=vm_url, headers=headers)
        return azurerequests.check_delete_response(response_vm, start_retry_interval,
                                                   'delete_current_virtual_machine', vm_name, 'VM')
    except:
        ctx.logger.info("Virtual Machine {0} could not be deleted".format(vm_name))


@operation
def set_storage_account_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file(required_keys=[constants.RESOURCE_GROUP_KEY, constants.STORAGE_ACCOUNT_KEY]+constants.REQUIRED_CONFIG_DATA)


@operation
def set_nic_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file(required_keys=None, prefixed_keys=[constants.PUBLIC_IP_KEY, constants.PRIVATE_IP_ADDRESS_KEY, constants.NIC_KEY], need_suffix=None)


@operation
def set_data_disks(azure_config, **kwargs):
    # This should be per disk issue #31
    utils.write_target_runtime_properties_to_file(required_keys=None, prefixed_keys=[constants.DATA_DISK_SIZE_KEY, constants.DATA_DISK_KEY, constants.DATA_DISK_LUN_KEY],  need_suffix=None)


def _set_private_ip(vm_name):
    vm_private_ip = ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY]
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


def _set_ip_addresses_keys(vm_name):
    current_public_ip_name = None
    current_private_ip_key = None
    private_ip_keys = []
    for current_key in ctx.instance.runtime_properties:
        if current_key.startswith(constants.PUBLIC_IP_KEY):
            public_key_instance_id = current_key.split(constants.PUBLIC_IP_KEY)[1]
            current_public_ip_name = ctx.instance.runtime_properties[current_key]
        elif current_key.startswith(constants.PRIVATE_IP_ADDRESS_KEY):
            private_ip_keys.append(current_key)
            current_private_ip_key = current_key

    if current_public_ip_name is not None:
        ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY] = current_public_ip_name

    if len(private_ip_keys) > 1:
        # There are two private IP addresses, so the one which doesn't correspond to the
        # public IP address, will be used
        for current_key in private_ip_keys:
            private_key_instance_id = current_key.split(constants.PRIVATE_IP_ADDRESS_KEY)[1]
            if private_key_instance_id != public_key_instance_id:
                ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY] = \
                    ctx.instance.runtime_properties[current_key]
                _set_private_ip(vm_name)
                return
    else:
        ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY] = \
            ctx.instance.runtime_properties[current_private_ip_key]
        _set_private_ip(vm_name)


def _start_vm_call(headers, vm_name, subscription_id, resource_group_name):
    ctx.logger.info("In _start_vm_call starting {0}".format(vm_name))
    start_vm_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualMachines/'+vm_name+'/start?api-version='+constants.api_version
    response_start_vm = requests.post(start_vm_url, headers=headers)
    if response_start_vm.status_code:
        status_code = response_start_vm.status_code
        ctx.logger.info("_start_vm_call:{0} - Status code is {1}".format(vm_name, response_start_vm.status_code))
        if response_start_vm.status_code in [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE]:
            ctx.logger.info("_start_vm_call: VM has started")
            if response_start_vm.text:
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
        ctx.logger.info("{0} is already in storage_profile".format(constants.DATA_DISKS))
        return

    storage_profile[constants.DATA_DISKS] = []
    data_disks = storage_profile[constants.DATA_DISKS]
    for curr_key in ctx.instance.runtime_properties:
        if curr_key.startswith(constants.DATA_DISK_KEY):
            ctx.logger.info("_set_data_disk_json : disk key is {0}".format(curr_key))
            disk_name = ctx.instance.runtime_properties[curr_key]
            ctx.logger.info("_set_data_disk_json : disk_name is {0}".format(disk_name))
            vhd_uri = "https://{0}.blob.core.windows.net/vhds/{1}.vhd".format(storage_account_name, disk_name)
            # Later make this property per disk issue #31
            disk_size = ctx.instance.runtime_properties[constants.DATA_DISK_SIZE_KEY]
            ctx.logger.info("_set_data_disk_json : disk_size is {0}".format(disk_size))
            curr_disk = {
                "name": disk_name,
                "createOption": "Empty",
                "vhd": {
                    "uri": vhd_uri
                },
                "caching": "None",
                "diskSizeGB": disk_size
            }

            if constants.DATA_DISK_LUN_KEY in ctx.instance.runtime_properties:
                lun = ctx.instance.runtime_properties[constants.DATA_DISK_LUN_KEY]
                curr_disk["lun"] = lun;
            storage_profile[constants.DATA_DISKS].append(curr_disk)


def _get_vm_base_json(location, random_suffix_value,
                      resource_group_name, storage_account_name,
                      subscription_id, vm_name):
    os_disk_name = "{0}{1}".format(constants.os_disk_prefix, random_suffix_value)
    ctx.instance.runtime_properties[constants.OS_DISK_NAME] = os_disk_name

    os_disk_uri = "https://{0}.blob.core.windows.net/vhds/{1}.vhd"\
        .format(storage_account_name, os_disk_name)
    ctx.instance.runtime_properties[constants.OS_DISK_URI] = os_disk_uri

    # VM profile for Linux
    # Disables password authentication and uses SSH keys instead
    os_profile_linux_config = {
        "disablePasswordAuthentication": "true",
        "ssh": {
            "publicKeys": [{
                "path": "/home/{0}/.ssh/authorized_keys".format(
                    ctx.node.properties['ssh_username']),
                "keyData": ctx.node.properties['key_data']
            }]
        }
    }

    # VM profile for Windows
    #
    os_profile_windows_config = {
        "provisionVMAgent": True,
        "winRM": {
            "listeners": [{
                "protocol": "http"
            }]
        }
    }

    os_profile = {"computername": vm_name}

    if ctx.node.properties.get('windows_os'):
        os_profile['adminUsername'] = ctx.node.properties['username']
        os_profile['adminPassword'] = ctx.node.properties['password']
        os_profile['windowsConfiguration'] = os_profile_windows_config
    else:
        os_profile['adminUsername'] = ctx.node.properties['ssh_username']
        os_profile['linuxConfiguration'] = os_profile_linux_config

    return {
        "id": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Compute/virtualMachines/{2}".format(
            subscription_id, resource_group_name, vm_name),
        "name": vm_name,
        "type": "Microsoft.Compute/virtualMachines",
        "location": location,
        "properties": {
            "hardwareProfile": {
                "vmSize": ctx.node.properties['vm_size']
            },
            "osProfile": os_profile,
            "storageProfile": {
                "imageReference": {
                    "publisher": ctx.node.properties['image_reference_publisher'],
                    "offer": ctx.node.properties['image_reference_offer'],
                    "sku": ctx.node.properties['image_reference_sku'],
                    "version": constants.vm_version
                },
                "osDisk": {
                    "name": "{0}".format(os_disk_name),
                    "vhd": {
                        "uri": os_disk_uri
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


def _delete_os_disk(start_retry_interval):
    headers, location, subscription_id = auth.get_credentials()

    os_disk_name = ctx.instance.runtime_properties[constants.OS_DISK_NAME]
    delete_os_disk_url = ctx.instance.runtime_properties[constants.OS_DISK_URI]
    ctx.instance.runtime_properties[constants.RESOURCE_NOT_DELETED] = True

    try:
        ctx.logger.info("Deleting the OS Disk {0}: {1}".format(os_disk_name, delete_os_disk_url))
        response_delete_os_disk = requests.delete(url=delete_os_disk_url, headers=headers)
        return azurerequests.check_delete_response(response_delete_os_disk, start_retry_interval,
                                                   '_delete_os_disk', os_disk_name, constants.OS_DISK)
    except:
        ctx.logger.info("OS disk {0} could not be deleted".format(delete_os_disk_url))


def _delete_data_disks(start_retry_interval):
    headers, location, subscription_id = auth.get_credentials()
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    for curr_key in ctx.instance.runtime_properties:
        if curr_key.startswith(constants.DATA_DISK_KEY):
            disk_name = ctx.instance.runtime_properties[curr_key]
            ctx.logger.info("_delete_data_disks : disk_name is {0}".format(disk_name))
            delete_data_disk_url = "https://{0}.blob.core.windows.net/vhds/{1}.vhd".format(storage_account_name, disk_name)
            ctx.instance.runtime_properties[constants.RESOURCE_NOT_DELETED] = True
            try:
                ctx.logger.info("Deleting the data Disk {0}: {1}".format(disk_name, delete_data_disk_url))
                response_delete_data_disk = requests.delete(url=delete_data_disk_url, headers=headers)
                return azurerequests.check_delete_response(response_delete_data_disk, start_retry_interval,
                                                   '_delete_data_disks', disk_name, constants.OS_DISK)
            except:
                ctx.logger.info("Data disk {0} could not be deleted".format(delete_data_disk_url))


def get_provisioning_state(**_):
    current_instance = utils.get_instance_or_source_instance()
    resource_group_name = current_instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vm_name = current_instance.runtime_properties[constants.VM_KEY]

    ctx.logger.info("Searching for {0}".format(vm_name))
    headers, location, subscription_id = auth.get_credentials()

    virtual_machine_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Compute/" \
                          "virtualMachines/{3}?validating=true&api-version={4}".format(constants.azure_url,
                                subscription_id, resource_group_name, vm_name, constants.api_version)
    return azurerequests.get_provisioning_state(headers, resource_group_name, virtual_machine_url)
