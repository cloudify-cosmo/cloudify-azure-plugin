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
import utils
import subnet
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import auth
import azurerequests


@operation
def creation_validation(**_):
    for property_key in constants.PUBLIC_IP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_public_ip(**_):
    public_ip_name = utils.set_resource_name(_get_public_ip_name, 'Public IP',
                                             constants.PUBLIC_IP_KEY, constants.EXISTING_PUBLIC_IP_NAME,
                                             constants.PUBLIC_IP_PREFIX)
    if public_ip_name is None:
        # Using an existing public ip, so don't create anything
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    if constants.PUBLIC_IP_KEY not in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY] = public_ip_name

    check_public_ip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version_network
    create_public_ip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version_network
    public_ip_params = _get_public_ip_params(location, public_ip_name)
    utils.check_or_create_resource(headers, public_ip_name, public_ip_params, check_public_ip_url, create_public_ip_url, 'public_ip')

    ctx.logger.info("{0} is {1}".format(constants.PUBLIC_IP_KEY, public_ip_name))


@operation
def verify_provision(start_retry_interval, **kwargs):
    public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]
    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the public_ip ({0}) to be provisioned'.format(public_ip_name),
            retry_after=start_retry_interval)


@operation
def delete_public_ip(**_):
    delete_current_public_ip()
    utils.clear_runtime_properties()


def delete_current_public_ip(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing Public IP was used, so there's no need to delete")
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    public_ip_name = ctx.instance.runtime_properties[constants.PUBLIC_IP_KEY]

    try:
        ctx.logger.info("Deleting Public IP")
        public_ip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/ publicIPAddresses/'+public_ip_name+'?api-version='+constants.api_version_network
        response_pip = requests.delete(url=public_ip_url, headers=headers)
        print(response_pip.text)

    except:
        ctx.logger.info("Public IP {0} could not be deleted.".format(public_ip_name))


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    ctx.source.instance.runtime_properties[constants.VNET_KEY] = ctx.target.instance.runtime_properties[constants.VNET_KEY]
    ctx.logger.info("{0} is {1}".format(constants.VNET_KEY, ctx.target.instance.runtime_properties[constants.VNET_KEY]))
    subnet.set_subnets_from_runtime("public.set_dependent_resources_names", ctx.source.instance.runtime_properties, ctx.target.instance.runtime_properties)
    _set_security_group_details(azure_config)


def _set_security_group_details(azure_config, **kwargs):
    if constants.SECURITY_GROUP_KEY in ctx.target.instance.runtime_properties:
        ctx.source.instance.runtime_properties[constants.SECURITY_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.SECURITY_GROUP_KEY]


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def _get_public_ip_name(public_ip_name):
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{0} is not in public ip runtime_properties yet.".format(constants.RESOURCE_GROUP_KEY))
    headers, location, subscription_id = auth.get_credentials()
    pip_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses?api-version='+constants.api_version_network
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


def get_provisioning_state(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    public_ip_name = ctx.instance.runtime_properties[constants.VNET_KEY]

    ctx.logger.info("Searching for public ip {0}".format(public_ip_name))
    headers, location, subscription_id = auth.get_credentials()

    check_public_ip_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.network/" \
                          "publicIPAddresses/{3}?api-version={4}".format(constants.azure_url,
                                subscription_id, resource_group_name, public_ip_name, constants.api_version_network)

    return azurerequests.get_provisioning_state(headers, resource_group_name, check_public_ip_url)

