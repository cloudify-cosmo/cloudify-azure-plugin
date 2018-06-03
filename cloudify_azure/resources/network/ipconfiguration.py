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
    resources.network.IPConfiguration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure IP Configuration psuedo-interface

    Blueprint notes
    ^^^^^^^^^^^^^^^
    `cloudify.azure.nodes.network.IPConfiguration` is a shell node type
    that will be typically used for connecting a Network Interface Card to
    a private IP, Subnet, Public IP Address, Load Balancer Backend Address
    Pools, and/or Load Balancer Inbound NAT Rules. This is essentially a
    "glue" node between NICs and other network resources.

    Generally, in a blueprint, users should instantiate resources such
    as a Subnet and Public IP Address first, then create one or more
    IP Configuration node(s) that connects to them, then create a Network
    Interface Card which connects to the IP Configuration(s).
'''
# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Logger, API version
from cloudify_azure import (constants, utils)
# IP configurations
# Relationship interfaces
from cloudify_azure.resources.network.subnet \
    import Subnet
from cloudify_azure.resources.network.publicipaddress \
    import PublicIPAddress

# pylint: disable=R0913


class IPConfiguration(Resource):
    '''
        Microsoft Azure IP Configuration interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string resource_group: Name of the parent Resource Group
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 network_interface_card=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        network_interface_card = network_interface_card or \
            _ctx.node.properties.get('network_interface_card_name')
        Resource.__init__(
            self,
            'IP Configuration',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network/',
                'networkInterfaces/{0}'.format(network_interface_card),
                'ipConfigurations'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


def get_ip_configurations(_ctx=ctx,
                          rel=constants.REL_NIC_CONNECTED_TO_IPC):
    '''
        Finds all IP Configurations associated with the current node.
        This method searches for any IP Configuration-specific
        relationships and, later, traverses the IP Configuration
        relationships for its dependencies

    :returns: Array of IP Configuration dicts
    :rtype: list
    '''
    ipconfigs = list()
    for node_rel in _ctx.instance.relationships:
        if rel in node_rel.type_hierarchy:
            ipconfigs.append(
                build_ip_configuration(node_rel.target))
    # Weed out bad IP Configurations
    return [x for x in ipconfigs if x is not None]


def build_ip_configuration(ipc):
    '''
        Attempts to construct a proper IP Configuration from
        a context object

    :params `cloudify.context.RelationshipSubjectContext` ipc:
        IP Configuration context object
    :returns: IP Configuration dict
    :rtype: dict or None
    '''
    if not ipc or not ipc.instance.relationships:
        return None
    # Find a referenced Subnet
    subnet = utils.get_rel_id_reference(
        Subnet,
        constants.REL_IPC_CONNECTED_TO_SUBNET,
        _ctx=ipc)
    # Find a referenced Public IP
    pubip = utils.get_rel_id_reference(
        PublicIPAddress,
        constants.REL_IPC_CONNECTED_TO_PUBIP,
        _ctx=ipc)
    ip_configuration = {
        'name': utils.get_resource_name(ipc),
        'properties': {
            'subnet': subnet,
            'publicIPAddress': pubip
        }
    }
    ip_configuration['properties'] = utils.dict_update(
        ip_configuration['properties'],
        utils.get_resource_config(_ctx=ipc))
    return ip_configuration
