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

from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.storage.storage_account import StorageAccount


@operation(resumable=True)
@decorators.with_generate_name(StorageAccount)
@decorators.with_azure_resource(StorageAccount)
def create(ctx, **_):
    """Uses an existing, or creates a new, Storage Account"""
    # Generate a resource name (if needed)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_STORAGE)
    storage_account = StorageAccount(azure_config, ctx.logger, api_version)
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
    result = utils.handle_create(
        storage_account,
        resource_group_name,
        name,
        additional_params=sa_params)
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
@decorators.with_azure_resource(StorageAccount)
def delete(ctx, **_):
    """Deletes a Storage Account"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_STORAGE)
    storage_account = StorageAccount(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, storage_account, resource_group_name, name)
