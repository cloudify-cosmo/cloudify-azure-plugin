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
    cloudify_azure.resources.network.ipconfiguration
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

# default context
from cloudify import ctx
# Relationships, node zombies... er... walkers
from cloudify_azure import (constants, utils)
# Relationship interfaces
from cloudify_azure.resources.network.subnet \
    import Subnet
from cloudify_azure.resources.network.publicipaddress \
    import PublicIPAddress


def get_ip_configurations(_ctx=ctx):
    '''
        Finds all IP Configurations associated with the current node.
        This method searches for any IP Configuration-specific
        relationships and, later, traverses the IP Configuration
        relationships for its dependencies

    :returns: Array of IP Configuration dicts
    :rtype: list
    '''
    ipconfigs = list()
    for rel in _ctx.instance.relationships:
        if constants.REL_NIC_CONNECTED_TO_IPC in rel.type_hierarchy:
            ipconfigs.append(
                build_ip_configuration(rel.target))
    # Weed out bad IP Configurations
    return [x for x in ipconfigs if x is not None]


def get_id_reference(resource, rel_type, api_fmt=True, _ctx=ctx):
    '''
        Finds a resource by relationship type and
        returns an Azure ID

    :param `cloudify_azure.resources.base.Resource` resource:
        Resource class to map resources to
    :param string rel_type: Cloudify relationship name
    :param boolean api_fmt: If True, returns the resource ID as a dict
        object with an *id* key. If False, returns just the ID string
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Azure ID of a resource
    :rtype: string or dict or None
    '''
    subscription_id = utils.get_subscription_id()
    for rel in _ctx.instance.relationships:
        if rel_type in rel.type_hierarchy:
            iface = resource(_ctx=rel.target)
            name = rel.target.node.properties.get('name')
            resid = '/subscriptions/{0}{1}/{2}'.format(
                subscription_id,
                iface.endpoint,
                name)
            if api_fmt:
                return {'id': resid}
            return resid
    return None


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
    subnet = get_id_reference(Subnet,
                              constants.REL_IPC_CONNECTED_TO_SUBNET,
                              _ctx=ipc)
    # Find a referenced Public IP
    pubip = get_id_reference(PublicIPAddress,
                             constants.REL_IPC_CONNECTED_TO_PUBIP,
                             _ctx=ipc)

    # Build a partial config and update it with properties config
    return utils.dict_update({
        'name': ipc.node.properties.get('name'),
        'properties': {
            'subnet': subnet,
            'publicIPAddress': pubip
        }
    }, utils.get_resource_config(_ctx=ipc))
