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
import auth
import utils
import subnet
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import azurerequests

 
@operation
def creation_validation(**_):
    for property_key in constants.NIC_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


def _get_nic_params(current_subnet_name, location, resource_group_name, subscription_id, vnet_name):
    network_str = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/".format(subscription_id,
                                                                                            resource_group_name)
    nic_json = {
        "location": location,
        "properties": {
            "ipConfigurations": [
                {
                    "name": current_subnet_name,
                    "properties": {
                        "subnet": {
                            "id": "{0}virtualNetworks/{1}/subnets/{2}".format(network_str, vnet_name, current_subnet_name)
                        },
                        "privateIPAllocationMethod": "Dynamic"
                    }
                }
            ],
        }
    }
    nic_properties = nic_json['properties']
    security_group_properties = nic_json['properties']
    properties_ip_configurations0 = nic_properties['ipConfigurations'][0]
    ip_configurations_properties = properties_ip_configurations0['properties']
    if constants.PUBLIC_IP_KEY in ctx.instance.runtime_properties:
       
        public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
        public_ip_address_json = {
            "id": network_str + "publicIPAddresses/" + public_ip_name
        }
        ip_configurations_properties['publicIPAddress'] = public_ip_address_json
        nic_properties['enableIPForwarding'] = 'true'
    
    if constants.SECURITY_GROUP_KEY in ctx.instance.runtime_properties:
        security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
        security_group_json = {  
            "id": "/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/Microsoft.Network/networkSecurityGroups/"+security_group_name
        }
        security_group_properties['networkSecurityGroup'] = security_group_json
    ctx.logger.info("nic_json : {0}".format(nic_json))
    nic_params = json.dumps(nic_json)
    return network_str, nic_params


def set_nic_private_ip():
    if constants.SUCCESSFUL_RESPONSE_JSON in ctx.instance.runtime_properties:
        response_nic_json = ctx.instance.runtime_properties[constants.SUCCESSFUL_RESPONSE_JSON]
        nic_root_properties = response_nic_json[u'properties']
        ctx.logger.info("nic_root_properties : {0}".format(str(nic_root_properties)))
        ip_configurations = nic_root_properties[u'ipConfigurations'][0]
        ctx.logger.info("nic ip_configurations0 : {0}".format(str(ip_configurations)))
        curr_properties = ip_configurations[u'properties']
        ctx.logger.info("nic curr_properties : {0}".format(str(curr_properties)))
        private_ip_address = curr_properties[u'privateIPAddress']
        ctx.logger.info("nic private_ip_address : {0}".format(str(private_ip_address)))

        curr_private_ip_key = "{0}{1}{2}".format(constants.PRIVATE_IP_ADDRESS_KEY, ctx.node.id, ctx.instance.id)
        private_ip_str = str(private_ip_address)
        ctx.instance.runtime_properties[curr_private_ip_key] = private_ip_str


@operation
def create_nic(**_):
    create_a_nic()


def create_a_nic(**_):
    utils.set_runtime_properties_from_file()
    _set_nic_subnet()
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        if constants.EXISTING_NIC_KEY in ctx.node.properties:
            existing_nic_name = ctx.node.properties[constants.EXISTING_NIC_KEY]
            if existing_nic_name:
                nic_exists = _get_nic_name(existing_nic_name)
                if not nic_exists:
                    raise NonRecoverableError("NIC {0} doesn't exist your Azure account".format(existing_nic_name))
            else:
                raise NonRecoverableError("The value of '{0}' in the input, is empty".format(constants.EXISTING_NIC_KEY))
        else:
            raise NonRecoverableError("'{0}' was specified, but '{1}' doesn't exist in the input".format(constants.USE_EXTERNAL_RESOURCE, constants.EXISTING_NIC_KEY))
        curr_nic_key = _get_nic_key()
        ctx.instance.runtime_properties[curr_nic_key] = ctx.node.properties[constants.EXISTING_NIC_KEY]
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
   
    vnet_name = ctx.instance.runtime_properties[constants.VNET_KEY]
    current_subnet_name = ctx.instance.runtime_properties[constants.SUBNET_KEY]
    nic_name = utils.key_in_runtime(constants.NIC_KEY, ends_with_key=False, starts_with_key=True, return_value=True)
    if not nic_name:
        random_suffix_value = utils.random_suffix_generator()
        nic_name = constants.NIC_PREFIX+random_suffix_value
        curr_nic_key = _get_nic_key()
        ctx.instance.runtime_properties[curr_nic_key] = nic_name

    ctx.logger.info("Creating new network interface card: {0}".format(nic_name))
    network_str, nic_params = _get_nic_params(current_subnet_name, location, resource_group_name, subscription_id, vnet_name)
    create_nic_url = constants.azure_url+network_str+"/networkInterfaces/"+nic_name+"?api-version="+constants.api_version_network
    return utils.create_resource(headers, nic_name, nic_params, create_nic_url, 'NIC')


@operation
def verify_provision(start_retry_interval, **kwargs):
    curr_nic_key = _get_nic_key()
    nic_name = ctx.instance.runtime_properties[curr_nic_key]
    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the NIC ({0}) to be provisioned'.format(nic_name), retry_after=start_retry_interval)

    set_nic_private_ip()

@operation
def delete_nic(**_):
    delete_a_nic()
    utils.clear_runtime_properties()


def delete_a_nic(**_):
    delete_current_nic()


def delete_current_nic(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing NIC was used, so there's no need to delete")
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    nic_name = utils.key_in_runtime(constants.NIC_KEY, ends_with_key=False, starts_with_key=True, return_value=True)

    try:
        ctx.logger.info("Deleting NIC {0}".format(nic_name))
        nic_url = constants.azure_url+"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
        response_nic = requests.delete(url=nic_url, headers=headers)
        print(response_nic.text)
    except:
        ctx.logger.info("Network Interface Card {0} could not be deleted.".format(nic_name))


@operation
def set_security_group_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.SECURITY_GROUP_KEY])


@operation
def set_public_ip_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY, constants.PUBLIC_IP_KEY, constants.VNET_KEY, constants.SECURITY_GROUP_KEY], prefixed_keys=[constants.SUBNET_KEY], need_suffix=[constants.PUBLIC_IP_KEY])


@operation
def set_vnet_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY, constants.VNET_KEY, constants.SECURITY_GROUP_KEY], [constants.SUBNET_KEY])


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_nic_name(nic_name):
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{0} is not in nic runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))
    headers, location, subscription_id = auth.get_credentials()
    nic_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkInterfaces?api-version='+constants.api_version
    response_get_nic_name = requests.get(url=nic_url,headers=headers)
    if nic_name in response_get_nic_name.text:
        return True
    return False


def _get_nic_key():
    curr_nic_key = "{0}{1}{2}".format(constants.NIC_KEY, ctx.node.id, ctx.instance.id)
    nic_is_public = utils.key_in_runtime(constants.PUBLIC_IP_KEY, ends_with_key=False, starts_with_key=True, return_value=False)
    if nic_is_public:
        curr_nic_key = "{0}{1}".format(curr_nic_key, constants.PUBLIC_IP_KEY)

    return curr_nic_key

def _set_nic_subnet():
    for current_key in ctx.instance.runtime_properties:
        if current_key.startswith(constants.SUBNET_KEY):
            ctx.instance.runtime_properties[constants.SUBNET_KEY] = ctx.instance.runtime_properties[current_key]
            return


def get_provisioning_state(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    nic_key = _get_nic_key()
    nic_name = ctx.instance.runtime_properties[nic_key]

    ctx.logger.info("Searching for NIC {0}".format(nic_name))
    headers, location, subscription_id = auth.get_credentials()

    network_str = "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/".format(subscription_id,
                                                                                              resource_group_name)
    check_nic_url = "{0}{1}/networkInterfaces/{2}?api-version={3}".format(constants.azure_url, network_str, nic_name,
                                                                          constants.api_version_network)
    return azurerequests.get_provisioning_state(headers, resource_group_name, check_nic_url,
                                                save_successful_response=True)

