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
import auth
import utils
from resourcegroup import *
from publicip import *
from vnet import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
 

 
@operation
def creation_validation(**_):
    for property_key in constants.NIC_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


def _get_nic_params(current_subnet_name, location, resource_group_name, subscription_id, vnet_name):
    network_str = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/".format(subscription_id,
                                                                                            resource_group_name)
    nic_json = {
        "location": location,
        "properties": {
            "ipConfigurations": [
                {
                    "name": constants.IP_PREFIX + utils.random_suffix_generator(),
                    "properties": {
                        "subnet": {
                            "id": network_str + "virtualNetworks/" + vnet_name + "/subnets/" + current_subnet_name
                        },
                        "privateIPAllocationMethod": "Dynamic"
                    }
                }
            ],
        }
    }
    if constants.PUBLIC_IP_KEY in ctx.instance.runtime_properties:
        public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
        nic_properties = nic_json['properties']
        properties_ip_configurations0 = nic_properties['ipConfigurations'][0]
        ip_configurations_properties = properties_ip_configurations0['properties']
        public_ip_address_json = {
            "id": network_str + "publicIPAddresses/" + public_ip_name
        }
        ip_configurations_properties['publicIPAddress'] = public_ip_address_json
    ctx.logger.info("nic_json : {}".format(nic_json))
    print nic_json
    nic_params = json.dumps(nic_json)
    return network_str, nic_params


def set_nic_private_ip():
    if constants.CREATE_RESPONSE in ctx.instance.runtime_properties:
        response_nic_json = ctx.instance.runtime_properties[constants.CREATE_RESPONSE]
        nic_root_properties = response_nic_json[u'properties']
        ctx.logger.info("nic_root_properties : {}".format(str(nic_root_properties)))
        ip_configurations = nic_root_properties[u'ipConfigurations'][0]
        ctx.logger.info("nic ip_configurations0 : {}".format(str(ip_configurations)))
        curr_properties = ip_configurations[u'properties']
        ctx.logger.info("nic curr_properties : {}".format(str(curr_properties)))
        private_ip_address = curr_properties[u'privateIPAddress']
        ctx.logger.info("nic private_ip_address : {}".format(str(private_ip_address)))
        ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY] = str(private_ip_address)


@operation
def create_nic(**_):
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        if constants.EXISTING_NIC_KEY in ctx.node.properties:
            existing_nic_name = ctx.node.properties[constants.EXISTING_NIC_KEY]
            if existing_nic_name:
                nic_exists = _get_nic_name(existing_nic_name)
                if not nic_exists:
                    raise NonRecoverableError("NIC {} doesn't exist your Azure account".format(existing_nic_name))
            else:
                raise NonRecoverableError("The value of '{}' in the input, is empty".format(constants.EXISTING_NIC_KEY))
        else:
            raise NonRecoverableError("'{}' was specified, but '{}' doesn't exist in the input".format('use_external_resource', constants.EXISTING_NIC_KEY))

        ctx.instance.runtime_properties[constants.NIC_KEY] = ctx.node.properties[constants.EXISTING_NIC_KEY]
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    vnet_name = ctx.instance.runtime_properties[constants.VNET_KEY]
    current_subnet_name = ctx.instance.runtime_properties[constants.SUBNET_KEY]
    if constants.NIC_KEY in ctx.instance.runtime_properties:
        nic_name = ctx.instance.runtime_properties[constants.NIC_KEY]
    else:
        random_suffix_value = utils.random_suffix_generator()
        nic_name = constants.NIC_PREFIX+random_suffix_value
        ctx.instance.runtime_properties[constants.NIC_KEY] = nic_name

    ctx.logger.info("Creating new network interface card: {}".format(nic_name))
    network_str, nic_params = _get_nic_params(current_subnet_name, location, resource_group_name, subscription_id, vnet_name)
    check_nic_url = constants.azure_url+network_str+"/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
    create_nic_url = constants.azure_url+network_str+"/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
    utils.check_or_create_resource(headers, vnet_name, nic_params, check_nic_url, create_nic_url, 'NIC', True)

    set_nic_private_ip()


@operation
def delete_nic(**_):
    delete_current_nic()
    utils.clear_runtime_properties()


def delete_current_nic(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing NIC was used, so there's no need to delete")
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    nic_name = ctx.instance.runtime_properties[constants.NIC_KEY]

    try:
        ctx.logger.info("Deleting NIC {}".format(nic_name))
        nic_url = constants.azure_url+"/subscriptions/"+subscription_id+"/resourceGroups/"+resource_group_name+"/providers/microsoft.network/networkInterfaces/"+nic_name+"?api-version="+constants.api_version
        response_nic = requests.delete(url=nic_url, headers=headers)
        print(response_nic.text)
    except:
        ctx.logger.info("Network Interface Card {} could not be deleted.".format(nic_name))


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.source.instance.runtime_properties[constants.VNET_KEY] = ctx.target.instance.runtime_properties[constants.VNET_KEY]
    ctx.source.instance.runtime_properties[constants.SUBNET_KEY] = ctx.target.instance.runtime_properties[constants.SUBNET_KEY]
    ctx.logger.info("{} is {}".format(constants.VNET_KEY, ctx.target.instance.runtime_properties[constants.VNET_KEY]))
    if constants.PUBLIC_IP_KEY in ctx.target.instance.runtime_properties:
        ctx.logger.info("{} is {}".format(constants.PUBLIC_IP_KEY, ctx.target.instance.runtime_properties[constants.PUBLIC_IP_KEY]))
        ctx.source.instance.runtime_properties[constants.PUBLIC_IP_KEY] = ctx.target.instance.runtime_properties[constants.PUBLIC_IP_KEY]
    else:
        ctx.logger.info("{} is NOT in runtime props ".format(constants.PUBLIC_IP_KEY))



def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_nic_name(nic_name):
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in nic runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))
    headers, location, subscription_id = auth.get_credentials()
    nic_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkInterfaces?api-version='+constants.api_version
    response_get_nic_name = requests.get(url=nic_url,headers=headers)
    if nic_name in response_get_nic_name.text:
        return True
    return False

