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
    resources.storage.Disk
    ~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Storage Disk interface
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


def disk_name_generator():
    '''Generates a unique Disk resource name'''
    return ''.join(random.choice(string.lowercase + string.digits)
                   for i in range(random.randint(32, 76))) + '.vhd'


def data_disk_exists(pageblobsvc, disk_container, disk_name):
    '''
        Checks if a Data Disk already exists

    :rtype: `azure.storage.blob.models.Blob` or `None`
    :returns: Azure Page Blob object if the Data Disk
        exists or None if it does not
    '''
    ctx.logger.debug('Checking if Data Disk "{0}/{1}" exists'
                     .format(disk_container, disk_name))
    try:
        props = pageblobsvc.get_blob_properties(disk_container, disk_name)
        ctx.logger.debug('Data Disk "{0}/{1}" exists'
                         .format(disk_container, disk_name))
        return props
    except Exception:
        ctx.logger.debug('Data Disk "{0}/{1}" does not exist'
                         .format(disk_container, disk_name))
        return None


def get_cloud_storage_account(_ctx=ctx):
    '''Gets the Azure Blob storage service'''
    # Get the storage account
    storage_account = utils.get_parent(
        _ctx.instance,
        rel_type=constants.REL_CONTAINED_IN_SA)
    storage_account_name = utils.get_resource_name(_ctx=storage_account)
    # Get the storage account keys
    keys = StorageAccount(_ctx=storage_account).list_keys()
    if not isinstance(keys, list) or len(keys) < 1:
        raise RecoverableError(
            'StorageAccount reported no usable authentication keys')
    # Get an interface to the Storage Account
    storage_account_key = keys[0].get('key')
    return CloudStorageAccount(
        account_name=storage_account_name,
        account_key=storage_account_key)


@operation
def create_data_disk(**_):
    '''Uses an existing, or creates a new, Data Disk placeholder'''
    res_cfg = utils.get_resource_config() or dict()
    disk_name = ctx.node.properties.get('name')
    disk_container = res_cfg.get('container_name')
    # Validation
    if ctx.node.properties.get('use_external_resource', False):
        if not disk_name:
            raise NonRecoverableError(
                '"use_external_resource" specified without '
                'a resource "name"')
        if not disk_container:
            raise NonRecoverableError(
                '"use_external_resource" specified without '
                'a resource "container_name"')
    # Get the storage account
    csa = get_cloud_storage_account()
    # Get an interface to the Page Blob Service
    pageblobsvc = csa.create_page_blob_service()
    # Generate a VHD Data Disk name if needed
    if not disk_name:
        ctx.logger.info('Generating a new Data Disk name')
        for _ in xrange(0, 10):
            tmpname = disk_name_generator()
            if not data_disk_exists(pageblobsvc, disk_container, tmpname):
                disk_name = tmpname
                break
    # Set the runtime properties
    ctx.instance.runtime_properties['name'] = disk_name
    ctx.instance.runtime_properties['diskSizeGB'] = \
        res_cfg.get('size')
    ctx.instance.runtime_properties['container'] = \
        disk_container
    ctx.instance.runtime_properties['uri'] = (
        'https://{0}.blob.{1}/{2}/{3}'.format(
            csa.account_name, constants.CONN_STORAGE_ENDPOINT,
            disk_container, disk_name)
    )


@operation
def delete_data_disk(**_):
    '''Deletes a Data Disk'''
    res_cfg = utils.get_resource_config() or dict()
    disk_name = ctx.instance.runtime_properties.get('name')
    disk_container = ctx.instance.runtime_properties.get('container')
    # If we're not deleting the disk, skip the lifecycle operation
    if ctx.node.properties.get('use_external_resource', False) or \
       not res_cfg.get('force_delete', False):
        return
    # Validate the name exists
    if not disk_name or not disk_container:
        raise NonRecoverableError(
            'Attempted to delete Data Disk without a name or '
            'container name specified')
    # Get the storage account
    csa = get_cloud_storage_account()
    # Get an interface to the Page Blob Service
    pageblobsvc = csa.create_page_blob_service()
    # Delete the blob
    ctx.logger.info('Deleting Data Disk "{0}/{1}"'
                    .format(disk_container, disk_name))
    pageblobsvc.delete_blob(disk_container, disk_name)
    for prop in ['name', 'diskSizeGB', 'container', 'uri']:
        try:
            del ctx.instance.runtime_properties[prop]
        except IndexError:
            ctx.logger.debug(
                'Attempted to delete property {0} but failed.'.format(
                    prop))
