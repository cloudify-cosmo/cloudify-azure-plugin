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
"""
from cloudify import ctx
from cloudify_azure import (constants, utils)


def get_ip_configurations(_ctx=ctx,
                          rel=constants.REL_NIC_CONNECTED_TO_IPC):
    """
        Finds all IP Configurations associated with the current node.
        This method searches for any IP Configuration-specific
        relationships and, later, traverses the IP Configuration
        relationships for its dependencies

    :returns: Array of IP Configuration dicts
    :rtype: list
    """
    ipconfigs = list()
    for node_rel in _ctx.instance.relationships:
        if isinstance(rel, tuple):
            if any(x in node_rel.type_hierarchy for x in rel):
                ipconfigs.append(
                    build_ip_configuration(node_rel.target))
        else:
            if rel in node_rel.type_hierarchy:
                ipconfigs.append(
                    build_ip_configuration(node_rel.target))
    # Weed out bad IP Configurations
    return [x for x in ipconfigs if x is not None]


def build_ip_configuration(ipc):
    """
        Attempts to construct a proper IP Configuration from
        a context object

    :params `cloudify.context.RelationshipSubjectContext` ipc:
        IP Configuration context object
    :returns: IP Configuration dict
    :rtype: dict or None
    """
    if not ipc or not ipc.instance.relationships:
        return None
    # Find a referenced Subnet/PublicIPAddress
    rel_sub_type = constants.REL_IPC_CONNECTED_TO_SUBNET
    rel_pip_type = constants.REL_IPC_CONNECTED_TO_PUBIP
    for rel in ipc.instance.relationships:
        if isinstance(rel_sub_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_sub_type):
                subnet = {
                    'id': rel.target.instance.runtime_properties['resource_id']
                }
        else:
            if rel_sub_type in rel.type_hierarchy:
                subnet = {
                    'id': rel.target.instance.runtime_properties['resource_id']
                }
        if isinstance(rel_pip_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_pip_type):
                pubip = {
                    'id': rel.target.instance.runtime_properties['resource_id']
                }
        else:
            if rel_pip_type in rel.type_hierarchy:
                pubip = {
                    'id': rel.target.instance.runtime_properties['resource_id']
                }

    ip_configuration = {
        'name': utils.get_resource_name(ipc),
        'subnet': subnet,
        'public_ip_address': pubip
    }
    ip_configuration = \
        utils.handle_resource_config_params(ip_configuration,
                                            ipc.node.properties.get(
                                                "resource_config", {}))
    return ip_configuration
