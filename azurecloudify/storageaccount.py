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
from resourcegroup import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation



@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_storage_account(**_):
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        if constants.EXISTING_STORAGE_ACCOUNT_KEY in ctx.node.properties:
            existing_storage_account_name = ctx.node.properties[constants.EXISTING_STORAGE_ACCOUNT_KEY]
            if existing_storage_account_name:
                storage_account_exists = _get_storage_account_name(existing_storage_account_name)
                if not storage_account_exists:
                    raise NonRecoverableError("Storage account {} doesn't exist your Azure account".format(existing_storage_account_name))
            else:
                raise NonRecoverableError("The value of '{}' in the input, is empty".format(constants.EXISTING_STORAGE_ACCOUNT_KEY))
        else:
            raise NonRecoverableError("'{}' was specified, but '{}' doesn't exist in the input".format('use_external_resource',constants.EXISTING_RESOURCE_GROUP_KEY))

        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = ctx.node.properties[constants.EXISTING_STORAGE_ACCOUNT_KEY]
        return

    location = ctx.node.properties['location']
    subscription_id = ctx.node.properties['subscription_id']
    random_suffix_value = utils.random_suffix_generator()
    storage_account_name = constants.STORAGE_ACCOUNT_PREFIX+random_suffix_value
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    credentials = 'Bearer '+auth.get_auth_token()

    headers = {"Content-Type": "application/json", "Authorization": credentials}

    try:
        ctx.logger.info("Creating new storage account: {}".format(storage_account_name))
        storage_account_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
        storage_account_params = json.dumps({"properties": {"accountType": constants.storage_account_type, }, "location": location})
        response_sa = requests.put(url=storage_account_url, data=storage_account_params, headers=headers)

        if response_sa.text:
            ctx.logger.info("create_storage_account:{} response_sa.text is {}".format(storage_account_name, response_sa.text))
            if utils.request_failed("{}:{}".format('create_storage_account', storage_account_name), response_sa):
                raise NonRecoverableError("Storage account {} could not be created".format(storage_account_name))

        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = storage_account_name
    except:
        ctx.logger.info("Storage Account {} could not be created.".format(storage_account_name))
        raise NonRecoverableError("Storage Account {} could not be created.".format(storage_account_name))


@operation
def delete_storage_account(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    subscription_id = ctx.node.properties['subscription_id']
    credentials = 'Bearer '+auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    ctx.logger.info("Deleting Storage Account {}".format(storage_account_name))
    try:
        storage_account_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
        response_sa = requests.delete(url=storage_account_url, headers=headers)
        print response_sa.text
        ctx.logger.info("response_sa storage account : {}".format(response_sa.text))
    except:
        ctx.logger.info("Storage Account {} could not be deleted.".format(storage_account_name))

    utils.clear_runtime_properties()


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_storage_account_name(storage_account_name):
    ctx.logger.info("In _get_storage_account_name looking for {} ".format(storage_account_name))
    subscription_id = ctx.node.properties['subscription_id']
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in storage acoount runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))

    credentials = 'Bearer ' + auth.get_auth_token()
    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts?api-version='+constants.api_version
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    response_list = requests.get(url, headers=headers)
    ctx.logger.info("storage account response_list.text {} ".format(response_list.text))
    if storage_account_name in response_list.text:
        return True
    else:
        ctx.logger.info("Storage account {} does not exist".format(storage_account_name))
        return False
