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
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        if constants.EXISTING_VNET_KEY in ctx.node.properties:
            existing_vnet_name = ctx.node.properties[constants.EXISTING_VNET_KEY]
            if existing_vnet_name:
                vnet_exists = _get_vnet_name(existing_vnet_name)
                if not vnet_exists:
                    raise NonRecoverableError("Vnet {} doesn't exist your Azure account".format(existing_vnet_name))
            else:
                raise NonRecoverableError("The value of '{}' in the input, is empty".format(constants.EXISTING_VNET_KEY))
        else:
            raise NonRecoverableError("'{}' was specified, but '{}' doesn't exist in the input".format('use_external_resource', constants.EXISTING_VNET_KEY))

        ctx.instance.runtime_properties[constants.VNET_KEY] = ctx.node.properties[constants.EXISTING_VNET_KEY]
        return

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    random_suffix_value = utils.random_suffix_generator()
    vnet_name = constants.VNET_PREFIX+random_suffix_value
    vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version

    try:
        ctx.logger.info("Creating new virtual network: {}".format(vnet_name))

        vnet_params = json.dumps({"name": vnet_name, "location": location,"properties": {"addressSpace": {"addressPrefixes": constants.vnet_address_prefixes},"subnets": [{"name": constants.subnet_name, "properties": {"addressPrefix": constants.address_prefix}}]}})
        response_vnet = requests.put(url=vnet_url, data=vnet_params, headers=headers)
        print response_vnet.text
        ctx.logger.info("response_vnet : {}".format(response_vnet.text))
        ctx.instance.runtime_properties[constants.VNET_KEY] = vnet_name
        ctx.logger.info("{} is {}".format(constants.VNET_KEY, vnet_name))
    except:
        ctx.logger.info("Virtual Network {} could not be created.".format(vnet_name))
        sys.exit(1)


@operation
def delete_vnet(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    vnet_name = ctx.instance.runtime_properties[constants.VNET_KEY]
    subscription_id = ctx.node.properties['subscription_id']
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

    ctx.logger.info("Checking availability of virtual network: {}".format(vnet_name))
    try:
        ctx.logger.info("Deleting the virtual network: {}".format(vnet_name))
        vnet_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualNetworks/'+vnet_name+'?api-version='+constants.api_version
        response_vnet = requests.delete(url=vnet_url, headers=headers)
        print response_vnet.text
    except:
        ctx.logger.info("Virtual Network {} could not be deleted.".format(vnet_name))
        raise NonRecoverableError("Virtual Network {} could not be created.".format(vnet_name))

    utils.clear_runtime_properties()


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.source.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = ctx.target.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_vnet_name(vnet_name):
    ctx.logger.info("In _get_vnet_name looking for {} ".format(vnet_name))
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in vnet runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))
    credentials = auth.get_auth_token()
    subscription_id = ctx.node.properties['subscription_id']
    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version
    headers = {"Content-Type": "application/json", "Authorization": "{}".format(credentials)}
    response_list = requests.get(url, headers=headers)
    ctx.logger.info("VNET response_list.text {}".format(response_list.text))
    if vnet_name in response_list.text:
        return True
    else:
        ctx.logger.info("Virtual Network {} does not exist".format(vnet_name))
        return False
