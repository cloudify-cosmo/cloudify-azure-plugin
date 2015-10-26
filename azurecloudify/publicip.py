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
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import auth



@operation
def creation_validation(**_):
    for property_key in constants.PUBLIC_IP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_public_ip(**_):
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        if constants.EXISTING_PUBLIC_IP_NAME in ctx.node.properties:
            existing_public_ip_name = ctx.node.properties[constants.EXISTING_PUBLIC_IP_NAME]
            if existing_public_ip_name:
                public_ip_exists = _get_public_ip_name(existing_public_ip_name)
                if not public_ip_exists:
                    raise NonRecoverableError("Public ip {} doesn't exist your Azure account".format(existing_public_ip_name))
            else:
                raise NonRecoverableError("The value of '{}' in the input, is empty".format(constants.EXISTING_PUBLIC_IP_NAME))
        else:
            raise NonRecoverableError("'{}' was specified, but '{}' doesn't exist in the input".format('use_external_resource',constants.EXISTING_PUBLIC_IP_NAME))

        ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY] = ctx.node.properties[constants.EXISTING_PUBLIC_IP_NAME]
        return

    subscription_id = ctx.node.properties['subscription_id']
    location = ctx.node.properties['location']
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

    ctx.logger.info("{}  - Setting or looking for".format(constants.PUBLIC_IP_KEY))
    if constants.PUBLIC_IP_KEY in ctx.instance.runtime_properties:
        ctx.logger.info("{}  - looking for".format(constants.PUBLIC_IP_KEY))
        public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
        ctx.logger.info("{} is #1 {}".format(constants.PUBLIC_IP_KEY,public_ip_name))
    else:
        random_suffix_value = utils.random_suffix_generator()
        public_ip_name = constants.PUBLIC_IP_PREFIX+random_suffix_value
        ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY] = public_ip_name
        ctx.logger.info("{} is #2 {}".format(constants.PUBLIC_IP_KEY,public_ip_name))

    check_public_ip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
    create_public_ip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
    public_ip_params = _get_public_ip_params(location, public_ip_name)
    utils.check_or_create_resource(headers, public_ip_name, public_ip_params, check_public_ip_url, create_public_ip_url, 'public_ip')

    ctx.logger.info("{} is {}".format(constants.PUBLIC_IP_KEY, public_ip_name))

@operation
def delete_public_ip(**_):

    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

    try:
        ctx.logger.info("Deleting Public IP")
        public_ip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/ publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version
        response_pip = requests.delete(url=public_ip_url,headers=headers)
        print(response_pip.text)

    except:
        ctx.logger.info("Public IP {} could not be deleted.".format(public_ip_name))

    utils.clear_runtime_properties()


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.source.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = ctx.target.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    ctx.source.instance.runtime_properties[constants.VNET_KEY] = ctx.target.instance.runtime_properties[constants.VNET_KEY]
    ctx.source.instance.runtime_properties[constants.SUBNET_KEY] = ctx.target.instance.runtime_properties[constants.SUBNET_KEY]
    ctx.logger.info("{} is {}".format(constants.VNET_KEY, ctx.target.instance.runtime_properties[constants.VNET_KEY]))


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_public_ip_name(public_ip_name):
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in public ip runtime_properties yet.".format(constants.RESOURCE_GROUP_KEY))
    credentials = 'Bearer ' + auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    subscription_id = ctx.node.properties['subscription_id']
    pip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses?api-version='+constants.api_version
    response_get_pip = requests.get(url=pip_url,headers=headers)
    if public_ip_name in response_get_pip.text:
        return True
    else:
        return False

def _get_public_ip_params(location, public_ip_name):
    return json.dumps({
        "location": location,
        "name": public_ip_name,
        "properties": {
            "publicIPAllocationMethod": "Dynamic",
            "idleTimeoutInMinutes": 4,
        }
    })

