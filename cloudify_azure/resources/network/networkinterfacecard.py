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
    resources.network.NetworkInterfaceCard
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Network Interface Card interface
'''

# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
# Logger, API version
from cloudify_azure import (constants, utils)
# IP configurations
from cloudify_azure.resources.network.ipconfiguration \
    import get_ip_configurations
from cloudify_azure.resources.network.networksecuritygroup \
    import NetworkSecurityGroup

# pylint: disable=R0913


class NetworkInterfaceCard(Resource):
    '''
        Microsoft Azure Network Interface Card interface

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
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        Resource.__init__(
            self,
            'Network Interface Card',
            '/{0}/{1}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network/networkInterfaces'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


def get_connected_nsg():
    '''Finds a connected Network Security Group'''
    nsg = None
    nsg_name = None
    for rel in ctx.instance.relationships:
        if constants.REL_NIC_CONNECTED_TO_NSG in rel.type_hierarchy:
            nsg = NetworkSecurityGroup(_ctx=rel.target)
            nsg_name = utils.get_resource_name(rel.target)
    return {
        'id': '/subscriptions/{0}{1}/{2}'.format(
            utils.get_subscription_id(_ctx=nsg.ctx),
            nsg.endpoint,
            nsg_name)
    } if nsg else None


@operation
def create(**_):
    '''Uses an existing, or creates a new, Network Interface Card'''
    # Create a resource (if necessary)
    utils.task_resource_create(
        NetworkInterfaceCard(),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': utils.dict_update(
                utils.get_resource_config(),
                {
                    'networkSecurityGroup': get_connected_nsg(),
                    'ipConfigurations': get_ip_configurations()
                })
        })


@operation
def delete(**_):
    '''Deletes a Network Interface Card'''
    # Delete the resource
    utils.task_resource_delete(
        NetworkInterfaceCard())
