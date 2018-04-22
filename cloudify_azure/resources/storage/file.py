# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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
'''
    resources.storage.FileShare
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Storage File Share interface
'''

# Name generation
import random
import string
# Node properties and logger
from cloudify import ctx
# Exception handling
from cloudify.exceptions import RecoverableError, NonRecoverableError
# Lifecycle operation decorator
from cloudify.decorators import operation
# Storage Account resource class
from cloudify_azure.resources.storage.storageaccount import StorageAccount
# Logger, API version
from cloudify_azure import (constants, utils)
# Azure storage API interface
from azure.storage import CloudStorageAccount

# pylint: disable=W0703
# pylint: disable=R0914


def file_share_name_generator():
    '''Generates a unique File Share resource name'''
    return ''.join(random.choice(string.lowercase + string.digits)
                   for i in range(random.randint(24, 63)))


def file_share_exists(filesvc, share_name):
    '''
        Checks if a File Share already exists

    :rtype: `azure.storage.file.models.Share` or `None`
    :returns: Azure File Share object if the File Share
        exists or None if it does not
    '''
    ctx.logger.debug('Checking if File Share "{0}" exists'
                     .format(share_name))
    try:
        props = filesvc.get_share_properties(share_name)
        ctx.logger.debug('File Share "{0}" exists'
                         .format(share_name))
        return props
    except Exception:
        ctx.logger.debug('File Share "{0}" does not exist'
                         .format(share_name))
        return None


@operation
def create_file_share(**_):
    '''Creates an Azure File Share'''
    # Get resource config values
    res_cfg = utils.get_resource_config() or dict()
    share_name = ctx.node.properties.get('name')
    metadata = res_cfg.get('metadata')
    quota = res_cfg.get('quota')
    fail_on_exist = res_cfg.get('fail_on_exist', False)
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not share_name:
        raise NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Get the storage account
    storage_account = utils.get_parent(
        ctx.instance,
        rel_type=constants.REL_CONTAINED_IN_SA)
    storage_account_name = utils.get_resource_name(_ctx=storage_account)
    # Get the storage account keys
    keys = StorageAccount(_ctx=storage_account).list_keys()
    if not isinstance(keys, list) or len(keys) < 1:
        raise RecoverableError(
            'StorageAccount reported no usable authentication keys')
    # Get an interface to the Storage Account
    storage_account_key = keys[0].get('key')
    storageacct = CloudStorageAccount(
        account_name=storage_account_name,
        account_key=storage_account_key)
    # Get an interface to the File Service
    filesvc = storageacct.create_file_service()
    if ctx.node.properties.get('use_external_resource', False):
        # Attempt to use an existing File Share (if specified)
        ctx.logger.debug('Checking for existing File Share "{0}"'
                         .format(share_name))
        try:
            share = filesvc.get_share_properties(share_name)
            metadata = share.get('metadata', dict())
            quota = share.get('properties', dict()).get('quota')
            created = False
        except Exception as ex:
            ctx.logger.error('File Share "{0}" does not exist and '
                             '"use_external_resource" is set to true'
                             .format(share_name))
            raise NonRecoverableError(ex)
    else:
        # Generate a new File Share name if needed
        if not share_name:
            ctx.logger.info('Generating a new File Share name')
            for _ in xrange(0, 10):
                tmpname = file_share_name_generator()
                if not file_share_exists(filesvc, tmpname):
                    share_name = tmpname
                    break
        # Handle name error
        if not share_name:
            raise NonRecoverableError(
                'Error generating a new File Share name. Failed '
                'after 10 tries.')
        # Attempt to create the File Share
        ctx.logger.debug('Creating File Share "{0}"'.format(share_name))
        created = filesvc.create_share(
            share_name=share_name,
            metadata=metadata,
            quota=quota,
            fail_on_exist=False)
        if not created:
            ctx.logger.warn('File Share already exists')
            if fail_on_exist:
                raise NonRecoverableError(
                    'File Share already exists in the storage account and '
                    '"fail_on_exist" set to True')
    # Set run-time properties
    ctx.instance.runtime_properties['name'] = share_name
    ctx.instance.runtime_properties['quota'] = quota
    ctx.instance.runtime_properties['metadata'] = metadata
    ctx.instance.runtime_properties['created'] = created
    ctx.instance.runtime_properties['storage_account'] = storage_account_name
    ctx.instance.runtime_properties['username'] = storage_account_name
    ctx.instance.runtime_properties['password'] = storage_account_key
    ctx.instance.runtime_properties['uri'] = '{0}.file.{1}/{2}'.format(
        storage_account_name, constants.CONN_STORAGE_FILE_ENDPOINT, share_name
    )
