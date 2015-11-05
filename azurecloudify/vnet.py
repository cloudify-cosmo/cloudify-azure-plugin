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
from resourcegroup import *
import utils
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation



@operation
def creation_validation(**_):
    for property_key in constants.VNET_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_vnet(**_):

    vnet_name = utils.set_resource_name(_get_vnet_name, 'VNET',constants.VNET_KEY, constants.EXISTING_VNET_KEY,
                                        constants.VNET_PREFIX)
    if vnet_name is None:
        # Using an existing VNET, so don't create anything
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    if constants.VNET_KEY in ctx.instance.runtime_properties:
        current_subnet_name = ctx.instance.runtime_properties[constants.SUBNET_KEY]
    else:
        ctx.instance.runtime_properties[constants.VNET_KEY] = vnet_name
        current_subnet_name = constants.SUBNET_PREFIX+utils.random_suffix_generator()
        ctx.instance.runtime_properties[constants.SUBNET_KEY] = current_subnet_name

    check_vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
    create_vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
    vnet_params = json.dumps({"name": vnet_name, "location": location, "properties": {"addressSpace": {"addressPrefixes": constants.vnet_address_prefixes},"subnets": [{"name": current_subnet_name, "properties": {"addressPrefix": constants.address_prefix}}]}})
    utils.check_or_create_resource(headers, vnet_name, vnet_params, check_vnet_url, create_vnet_url, 'VNET')

    ctx.logger.info("{0} is {1}".format(constants.VNET_KEY, vnet_name))


@operation
def delete_vnet(**_):
    delete_current_vnet()
    utils.clear_runtime_properties()


def delete_current_vnet(**_):
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        ctx.logger.info("An existing VNET was used, so there's no need to delete")
        return

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vnet_name = ctx.instance.runtime_properties[constants.VNET_KEY]
    subscription_id = ctx.node.properties['subscription_id']
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

    try:
        ctx.logger.info("Deleting the virtual network: {0}".format(vnet_name))
        vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
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
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.source.instance.runtime_properties[constants.SECURITY_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.SECURITY_GROUP_KEY]

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_vnet_name(vnet_name):
    ctx.logger.info("In _get_vnet_name looking for {0} ".format(vnet_name))
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{0} is not in vnet runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))
    credentials = 'Bearer ' + auth.get_auth_token()
    subscription_id = ctx.node.properties['subscription_id']
    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    response_list = requests.get(url, headers=headers)
    ctx.logger.info("VNET response_list.text {0}".format(response_list.text))
    if vnet_name in response_list.text:
        return True
    else:
        ctx.logger.info("Virtual Network {0} does not exist".format(vnet_name))
        return False
