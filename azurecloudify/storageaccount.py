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
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import utils
import auth
import azurerequests


@operation
def creation_validation(**_):
    for property_key in constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_storage_account(**_):
    storage_account_name = utils.set_resource_name(_get_storage_account_name, 'Storage account',
                      constants.STORAGE_ACCOUNT_KEY, constants.EXISTING_STORAGE_ACCOUNT_KEY,
                      constants.STORAGE_ACCOUNT_PREFIX)
    if storage_account_name is None:
        # Using an existing storage account, so don't create anything
        return constants.ACCEPTED_STATUS_CODE

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    if constants.STORAGE_ACCOUNT_KEY not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = storage_account_name

    ctx.logger.info("Creating a new storage account: {0}".format(storage_account_name))
    storage_account_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
    storage_account_params = json.dumps({"properties": {"accountType": constants.storage_account_type, }, "location":location})
    status_code = utils.check_or_create_resource(headers, storage_account_name, storage_account_params, storage_account_url, storage_account_url, 'storage_account')
    ctx.logger.info("{0} is {1}".format(constants.STORAGE_ACCOUNT_KEY, storage_account_name))
    return status_code


@operation
def verify_provision(start_retry_interval, **kwargs):
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the storage_account ({0}) to be provisioned'.format(storage_account_name),
            retry_after=start_retry_interval)


@operation
def delete_storage_account(**_):
    status_code = delete_current_storage_account()
    utils.clear_runtime_properties()
    return status_code


def delete_current_storage_account(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing storage_account was used, so there's no need to delete")
        return constants.ACCEPTED_STATUS_CODE

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    ctx.logger.info("Deleting Storage Account {0}".format(storage_account_name))
    try:
        storage_account_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts/'+storage_account_name+'?api-version='+constants.api_version
        response_sa = requests.delete(url=storage_account_url, headers=headers)
        ctx.logger.info("response_sa storage account : {0}".format(response_sa.text))
        return response_sa.status_code
    except:
        ctx.logger.info("Storage Account {0} could not be deleted.".format(storage_account_name))
    return constants.FAILURE_CODE


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY])
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_storage_account_name(storage_account_name):
    ctx.logger.info("In _get_storage_account_name looking for {0} ".format(storage_account_name))
    headers, location, subscription_id = auth.get_credentials()

    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in storage account runtime_properties yet".format(constants.RESOURCE_GROUP_KEY))

    url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts?api-version='+constants.api_version

    response_list = requests.get(url, headers=headers)
    ctx.logger.info("storage account response_list.text {0} ".format(response_list.text))
    if storage_account_name in response_list.text:
        return True
    else:
        ctx.logger.info("Storage account {0} does not exist".format(storage_account_name))
        return False


def get_provisioning_state(**_):
    utils.validate_node_properties(constants.STORAGE_ACCOUNT_REQUIRED_PROPERTIES, ctx.node.properties)

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]
    ctx.logger.info("Searching for storage account {0} in resource group {1}".format(storage_account_name, resource_group_name))
    headers, location, subscription_id = auth.get_credentials()

    storage_account_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/" \
                          "Microsoft.Storage/storageAccounts/{3}?api-version={4}".\
        format(constants.azure_url, subscription_id, resource_group_name, storage_account_name, constants.api_version)
    return azurerequests.get_provisioning_state(headers, storage_account_name, storage_account_url)


def get_storageaccount_access_keys(**_):

    ctx.logger.info("In get_storageaccount_access_keys")
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.logger.info("In get_storageaccount_access_keys resource group is {0}".format(resource_group_name))
    storage_account_name = ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY]

    api_version = constants.api_version
    keys_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.Storage/" \
                  "storageAccounts/{3}/listKeys?api-version={4}"\
                    .format(constants.azure_url, subscription_id, resource_group_name,
                    storage_account_name, api_version)

    response = requests.post(url=keys_url, data="{}", headers=headers)
    result = response.json()
    return [result['key1'], result['key2']]