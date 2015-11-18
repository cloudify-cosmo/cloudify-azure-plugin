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
import constants
import sys
import os
import auth
from resourcegroup import *
import subnet
import utils
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify import ctx
from cloudify.decorators import operation


@operation
def creation_validation(**_):
    for property_key in constants.VNET_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)





@operation
def create_vnet(**_):

    vnet_name = utils.set_resource_name(_get_vnet_name, 'VNET', constants.VNET_KEY, constants.EXISTING_VNET_KEY,
                                        constants.VNET_PREFIX)
    if vnet_name is None:
        # Using an existing VNET, so don't create anything
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    if constants.VNET_KEY not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[constants.VNET_KEY] = vnet_name 
    
    check_vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version_network
    create_vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version_network
    vnet_json = _get_vnet_json(vnet_name, location, subscription_id, resource_group_name)
    vnet_params = json.dumps(vnet_json)
    
    utils.check_or_create_resource(headers, vnet_name, vnet_params, check_vnet_url, create_vnet_url, 'VNET')
        
    ctx.logger.info("{0} is {1}".format(constants.VNET_KEY, vnet_name))


@operation
def delete_vnet(**_):
    delete_current_vnet()
    utils.clear_runtime_properties()


def delete_current_vnet(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing VNET was used, so there's no need to delete")
        return

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vnet_name = ctx.instance.runtime_properties[constants.VNET_KEY]
    headers, location, subscription_id = auth.get_credentials()

    try:
        ctx.logger.info("Deleting the virtual network: {0}".format(vnet_name))
        vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version_network
        response_vnet = requests.delete(url=vnet_url, headers=headers)
        if response_vnet.text:
            ctx.logger.info("Deleted VNET {0}, response is: {1}".format(vnet_name, response_vnet.text))
        elif response_vnet.status_code:
            ctx.logger.info("Deleted VNET {0}, status code is: {1}".format(vnet_name, response_vnet.status_code))
        else:
            ctx.logger.info("Deleted VNET {0}, there is status code".format(vnet_name))
    except:
        ctx.logger.info("Virtual Network {0} could not be deleted.".format(vnet_name))
        raise NonRecoverableError("Virtual Network {0} could not be created.".format(vnet_name))


@operation
def set_resource_group_details(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]


@operation
def set_security_group_details(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.SECURITY_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.SECURITY_GROUP_KEY]


def _set_security_group_details(azure_config, **kwargs):
    if constants.SECURITY_GROUP_KEY in ctx.target.instance.runtime_properties:
        set_security_group_details(azure_config)


@operation
def set_subnet_details(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    subnet.set_subnets_from_runtime("vnet.set_subnet_details", ctx.source.instance.runtime_properties, ctx.target.instance.runtime_properties, False)
    _set_security_group_details(azure_config)

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_vnet_name(vnet_name):
    ctx.logger.info("In _get_vnet_name looking for {0} ".format(vnet_name))
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{0} is not in vnet runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))
    headers, location, subscription_id = auth.get_credentials()
    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version_network
    response_list = requests.get(url, headers=headers)
    ctx.logger.info("VNET response_list.text {0}".format(response_list.text))
    if vnet_name in response_list.text:
        return True
    else:
        ctx.logger.info("Virtual Network {0} does not exist".format(vnet_name))
        return False


def _get_vnet_json(vnet_name, location, subscription_id, resource_group_name):
    vnet_json = {
        "name": vnet_name,
        "location": location,
        "properties": {
            "addressSpace": {
                "addressPrefixes": constants.vnet_address_prefixes
            },
            "subnets": []
        }
    }
    _add_subnets(vnet_json, subscription_id, resource_group_name)
    return vnet_json


def _add_subnets(vnet_json, subscription_id, resource_group_name):
    vnet_properties = vnet_json['properties']
    vnet_subnets = vnet_properties['subnets']
    for curr_key in ctx.instance.runtime_properties:
        if curr_key.startswith(constants.SUBNET_KEY):
            current_subnet_name = ctx.instance.runtime_properties[curr_key]
            vnet_curr_subnet = {
                "name": current_subnet_name,
                "properties": {
                    "addressPrefix": constants.address_prefix
                }
            }
            vnet_curr_subnet = _add_security_group(vnet_curr_subnet, subscription_id, resource_group_name)
            vnet_subnets.append(vnet_curr_subnet)
    return vnet_json


# Github issue #22 : Add support for security group per subnet (when there's more than one subnet)
def _add_security_group(vnet_curr_subnet, subscription_id, resource_group_name):
    if constants.SECURITY_GROUP_KEY in ctx.instance.runtime_properties:
        security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
        curr_subnet_properties = vnet_curr_subnet['properties']
        curr_subnet_properties['networkSecurityGroup'] = {
            "id": "/subscriptions/{0}/resourceGroups/{1}/providers/Microsoft.Network/networkSecurityGroups/{2}".format(subscription_id, resource_group_name, security_group_name)
        }
    return vnet_curr_subnet
