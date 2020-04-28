# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
    resources.storage.StorageAccount
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Storage Account interface
"""
import random
import string

from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import utils
from azure_sdk.resources.storage.storage_account import StorageAccount


def sa_name_generator():
    """Generates a unique SA resource name"""
    return ''.join(random.choice(
        string.ascii_lowercase + string.digits) for i in range(3, 24))


def get_unique_name(storage_account, resource_group_name, name):
    if not name:
        for _ in range(0, 15):
            name = sa_name_generator()
            try:
                result = storage_account.get(resource_group_name, name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except CloudError:  # if exception that means name is not used
                return name
    else:
        return name


@operation(resumable=True)
def create(ctx, **_):
    """Uses an existing, or creates a new, Storage Account"""
    # Generate a resource name (if needed)
    azure_config = ctx.node.properties.get('azure_config')
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    storage_account = StorageAccount(azure_config, ctx.logger)
    name = get_unique_name(storage_account, resource_group_name, name)
    ctx.instance.runtime_properties['name'] = name
    sa_sku = ctx.node.properties.get('sku')
    sa_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
        'account_type': ctx.node.properties.get('resource_config', {}).get(
            'accountType'),
        'network_rule_set': ctx.node.properties.get('resource_config', {}).get(
            'networkAcls'),
        'enable_https_traffic_only':
            ctx.node.properties.get('resource_config', {}).get(
                'supportsHttpsTrafficOnly'),
        'encryption': {
            'services': ctx.node.properties.get('resource_config', {}).get(
                'encryption'),
            'key_source': ctx.node.properties.get('resource_config', {}).get(
                'keySource'),
        }
    }
    if sa_sku:
        sa_params['sku'] = sa_sku
    # clean empty values from params
    sa_params = \
        utils.cleanup_empty_params(sa_params)
    # Create a resource (if necessary)
    try:
        result = storage_account.get(resource_group_name, name)
        if ctx.node.properties.get('use_external_resource', False):
            ctx.logger.info("Using external resource")
        else:
            ctx.logger.info("Resource with name {0} exists".format(name))
            return
    except CloudError:
        if ctx.node.properties.get('use_external_resource', False):
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing storage_account '{0}'.".format(name))
        else:
            try:
                result = \
                    storage_account.create(
                        resource_group_name,
                        name,
                        sa_params)
            except CloudError as cr:
                raise cfy_exc.NonRecoverableError(
                    "create storage_account '{0}' "
                    "failed with this error : {1}".format(name,
                                                          cr.message)
                    )

    ctx.instance.runtime_properties['resource_group'] = resource_group_name
    ctx.instance.runtime_properties['resouce'] = result
    ctx.instance.runtime_properties['resource_id'] = result.get("id", "")


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Storage Account"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = ctx.node.properties.get('azure_config')
    resource_group_name = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    storage_account = StorageAccount(azure_config, ctx.logger)
    try:
        storage_account.get(resource_group_name, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        storage_account.delete(resource_group_name, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create storage_account '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
