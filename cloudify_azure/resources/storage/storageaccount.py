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
    resources.storage.StorageAccount
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Storage Account interface
'''

import httplib
# Random string
import random
import string
# Node properties and logger
from cloudify import ctx
# Exception handling
from cloudify.exceptions import RecoverableError
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
# Logger, API version
from cloudify_azure import (constants, utils)


class StorageAccount(Resource):
    '''
        Microsoft Azure Storage Account interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 api_version=constants.API_VER_STORAGE,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        Resource.__init__(
            self,
            'Storage Account',
            '/{0}/{1}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Storage/storageAccounts'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)

    def list_keys(self, name=None):
        '''
            Calls /listKeys

        :param string name: Name of the existing resource
        :returns: Response data from the Azure API call
        :rtype: dict
        :raises: :exc:`cloudify.exceptions.RecoverableError`
        '''
        # Get the resource name
        name = name or utils.get_resource_name(self.ctx)
        url = '{0}/{1}/listKeys'.format(self.endpoint, name)
        res = self.client.request(
            method='post',
            url=url)
        if res.status_code != httplib.OK:
            raise RecoverableError(
                'Unexpected status returned after calling '
                '/listKeys. Status={0}'.format(res.status_code))
        keys = res.json()
        ret = list()
        for key in keys:
            ret.append({
                'name': key,
                'key': keys[key]
            })
        self.log.debug('keys: {0}'.format(keys))
        return ret


def sa_name_generator():
    '''Generates a unique SA resource name'''
    return ''.join(random.choice(
        string.ascii_lowercase + string.digits) for i in range(3, 24))


@operation
def create(**_):
    '''Uses an existing, or creates a new, Storage Account'''
    # Generate a resource name (if needed)
    utils.generate_resource_name(
        StorageAccount(),
        generator=sa_name_generator)
    # Create a resource (if necessary)
    utils.task_resource_create(
        StorageAccount(),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': utils.get_resource_config()
        })


@operation
def delete(**_):
    '''Deletes a Storage Account'''
    # Delete the resource
    utils.task_resource_delete(
        StorageAccount())
