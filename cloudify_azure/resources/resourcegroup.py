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
    resources.ResourceGroup
    ~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Resource Group interface
'''

# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
# API version
from cloudify_azure import (constants, utils)


class ResourceGroup(Resource):
    '''
        Microsoft Azure Resource Group interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 api_version=constants.API_VER_RESOURCES,
                 logger=None,
                 _ctx=ctx):
        Resource.__init__(
            self,
            'Resource Group',
            '/resourceGroups',
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


@operation
def create(**_):
    '''Uses an existing, or creates a new, Resource Group'''
    # Create a resource (if necessary)
    utils.task_resource_create(
        ResourceGroup(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_RESOURCES)),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags')
        })


@operation
def delete(**_):
    '''Deletes a Resource Group'''
    # Delete the resource
    utils.task_resource_delete(
        ResourceGroup(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_RESOURCES)))
