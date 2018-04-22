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
    resources.network.Subnet
    ~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Subnet interface
'''

# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
# Logger, API version
from cloudify_azure import (constants, utils)
# Relationship interfaces
from cloudify_azure.resources.network.networksecuritygroup \
    import NetworkSecurityGroup
from cloudify_azure.resources.network.routetable \
    import RouteTable

# pylint: disable=R0913


class Subnet(Resource):
    '''
        Microsoft Azure Subnet interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string virtual_network: Name of the parent Virtual Network
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 virtual_network=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        virtual_network = virtual_network or \
            utils.get_virtual_network(_ctx=_ctx)
        Resource.__init__(
            self,
            'Subnet',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network',
                'virtualNetworks/{0}'.format(virtual_network),
                'subnets'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


@operation
def create(**_):
    '''Uses an existing, or creates a new, Subnet'''
    # Create a resource (if necessary)
    utils.task_resource_create(
        Subnet(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': utils.get_resource_config()
        })


@operation
def delete(**_):
    '''Deletes a Subnet'''
    # Delete the resource
    utils.task_resource_delete(
        Subnet(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        )
    )


@operation
def attach_network_security_group(**_):
    '''Attaches a Network Security Group (source) to the Subnet (target)'''
    nsg = NetworkSecurityGroup(_ctx=ctx.source)
    nsg_name = utils.get_resource_name(ctx.source)
    # Attach
    utils.task_resource_update(
        Subnet(_ctx=ctx.target, api_version=ctx.source.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ), {
            'properties': {
                'networkSecurityGroup': {
                    'id': '/subscriptions/{0}{1}/{2}'.format(
                        utils.get_subscription_id(_ctx=ctx.source),
                        nsg.endpoint,
                        nsg_name)
                }
            }
        }, _ctx=ctx.target)


@operation
def detach_network_security_group(**_):
    '''Detaches a Network Security Group to the Subnet'''
    # Detach
    utils.task_resource_update(
        Subnet(_ctx=ctx.target, api_version=ctx.source.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ), {
            'properties': {
                'networkSecurityGroup': None
            }
        }, _ctx=ctx.target)


@operation
def attach_route_table(**_):
    '''Attaches a Route Table (source) to the Subnet (target)'''
    rtbl = RouteTable(_ctx=ctx.source)
    rtbl_name = utils.get_resource_name(ctx.source)
    # Attach
    utils.task_resource_update(
        Subnet(_ctx=ctx.target, api_version=ctx.source.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ), {
            'properties': {
                'routeTable': {
                    'id': '/subscriptions/{0}{1}/{2}'.format(
                        utils.get_subscription_id(_ctx=ctx.source),
                        rtbl.endpoint,
                        rtbl_name)
                }
            }
        }, _ctx=ctx.target)


@operation
def detach_route_table(**_):
    '''Detaches a Route Table to the Subnet'''
    # Detach
    utils.task_resource_update(
        Subnet(_ctx=ctx.target, api_version=ctx.source.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ), {
            'properties': {
                'routeTable': None
            }
        }, _ctx=ctx.target)
