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
    resources.storage.FileShare
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Storage File Share interface
"""

from msrestazure.azure_exceptions import CloudError

from cloudify.decorators import operation
from cloudify.exceptions import (RecoverableError, NonRecoverableError)

from azure_sdk.resources.storage.file_share import FileShare
from azure_sdk.resources.storage.storage_account import StorageAccount
from cloudify_azure import (constants, utils, decorators)


@operation(resumable=True)
@decorators.with_generate_name(FileShare)
@decorators.with_azure_resource(FileShare)
def create(ctx, **_):
    """Creates an Azure File Share"""
    share_name = utils.get_resource_name(ctx)
    res_cfg = ctx.node.properties.get("resource_config", {})
    metadata = res_cfg.get('metadata')
    share_quota = res_cfg.get('quota')
    if ctx.node.properties.get('use_external_resource', False) and \
            not share_name:
        raise NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    storage_account = utils.get_storage_account(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    azure_config = utils.get_client_config(ctx.node.properties)

    keys = StorageAccount(azure_config, ctx.logger).list_keys(
        resource_group_name, storage_account)
    if not keys or not keys.get("key1"):
        raise RecoverableError(
            'StorageAccount reported no usable authentication keys')
    # Get an interface to the Storage Account
    storage_account_key = keys.get("key1")
    # Get an interface to the File Share

    api_version = \
        ctx.node.properties.get('api_version',
                                constants.API_VER_STORAGE_FILE_SHARE)

    file_share = FileShare(azure_config, ctx.logger, api_version)
    try:
        result = \
            file_share.create(resource_group_name,
                              storage_account,
                              share_name,
                              metadata,
                              share_quota)
    except CloudError as cr:
        raise NonRecoverableError(
            "create file share '{0}' "
            "failed with this error : {1}".format(share_name,
                                                  cr.message)
        )
    ctx.instance.runtime_properties['quota'] = share_quota
    ctx.instance.runtime_properties['metadata'] = metadata
    ctx.instance.runtime_properties['storage_account'] = storage_account
    ctx.instance.runtime_properties['username'] = storage_account
    ctx.instance.runtime_properties['password'] = storage_account_key
    ctx.instance.runtime_properties['uri'] = '{0}.file.{1}/{2}'.format(
        storage_account, constants.CONN_STORAGE_ENDPOINT, share_name
    )
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=share_name,
        resource_get_create_result=result)


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a File Share"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    share_name = utils.get_resource_name(ctx)
    storage_account = ctx.instance.runtime_properties.get(
        'storage_account') or utils.get_storage_account(ctx)
    api_version = \
        ctx.node.properties.get('api_version',
                                constants.API_VER_STORAGE_FILE_SHARE)

    file_share = FileShare(azure_config, ctx.logger, api_version)
    try:

        file_share.delete(resource_group_name,
                          storage_account,
                          share_name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise NonRecoverableError(
            "delete file share '{0}' "
            "failed with this error : {1}".format(share_name,
                                                  cr.message))
