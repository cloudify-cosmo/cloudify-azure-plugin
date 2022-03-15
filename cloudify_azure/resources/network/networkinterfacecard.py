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
    resources.network.NetworkInterfaceCard
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Network Interface Card interface
"""
from uuid import uuid4
from msrestazure.azure_exceptions import CloudError
from azure.core.exceptions import ResourceNotFoundError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation


from cloudify_azure import (constants, decorators, utils)
from cloudify_azure.resources.network.ipconfiguration \
    import get_ip_configurations
from cloudify_azure.resources.network.publicipaddress import PUBLIC_IP_PROPERTY
from azure_sdk.resources.network.network_interface_card \
    import NetworkInterfaceCard
from azure_sdk.resources.network.public_ip_address \
    import PublicIPAddress


def get_unique_ip_conf_name(nic, resource_group_name,
                            nic_name, name):
    if not name:
        for _ in range(0, 15):
            name = "{0}".format(uuid4())
            try:
                result = nic.get(resource_group_name, nic_name)
                for ip_conf in result.get("ip_configurations"):
                    if ip_conf.get("name") == name:  # found ipc with same name
                        name = ""
                        break
                if name:
                    return name
            except (CloudError, ResourceNotFoundError):  # no name yet
                return name
    else:
        return name


def get_connected_nsg(ctx):
    """Finds a connected Network Security Group"""
    nsg = None
    rel_type = constants.REL_NIC_CONNECTED_TO_NSG
    for rel in ctx.instance.relationships:
        if isinstance(rel_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_type):
                nsg = rel.target
        else:
            if rel_type in rel.type_hierarchy:
                nsg = rel.target
    return {
        'id': nsg.instance.runtime_properties.get("resource_id", "")
    } if nsg else None


@operation(resumable=True)
@decorators.with_generate_name(NetworkInterfaceCard)
def create(ctx, **_):
    """Uses an existing, or creates a new, Network Interface Card"""
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    ctx.logger.info("Created NIC with name {0} "
                    "inside ResourceGroup {1}".format(name,
                                                      resource_group_name))
    ctx.instance.runtime_properties['resource_group'] = resource_group_name


@operation(resumable=True)
@decorators.with_azure_resource(NetworkInterfaceCard)
def configure(ctx, **_):
    """
        Uses an existing, or creates a new, Network Interface Card

    .. warning::
        The "configure" operation is actually the second half of
        the "create" operation. This is necessary since IP
        Configuration nodes are treated as separate, stand-alone
        types and must be "connected" to the NIC before
        it's actually created.  The actual "create" operation
        simply assigns a UUID for the node and the "configure"
        operation creates the object
    """
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = ctx.instance.runtime_properties.get('name')
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_interface_card = NetworkInterfaceCard(azure_config, ctx.logger,
                                                  api_version)
    nic_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
        'primary': ctx.node.properties.get('primary'),
    }
    nic_params = \
        utils.handle_resource_config_params(nic_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    # Special Case network_security_group instead of networkSecurityGroups
    nic_params['network_security_group'] = \
        nic_params.pop('network_security_groups', None)
    # clean empty values from params
    nic_params = \
        utils.cleanup_empty_params(nic_params)
    nic_params = utils.dict_update(
        nic_params, {
            'network_security_group': get_connected_nsg(ctx),
            'ip_configurations': get_ip_configurations(ctx)
        }
    )
    # clean empty values from params
    nic_params = \
        utils.cleanup_empty_params(nic_params)

    try:
        result = \
            network_interface_card.create_or_update(
                resource_group_name,
                name,
                nic_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "configure nic '{0}' "
            "failed with this error : {1}".format(name, cr.message))

    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
def start(ctx, **_):
    """
        Stores NIC IPs in runtime properties.
    """

    azure_config = utils.get_client_config(ctx.node.properties)
    name = ctx.instance.runtime_properties.get('name')
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_interface_card = NetworkInterfaceCard(azure_config, ctx.logger,
                                                  api_version)
    nic_data = network_interface_card.get(resource_group_name, name)

    for ip_cfg in nic_data.get('ip_configurations', list()):

        # Get the Private IP Address endpoint
        ctx.instance.runtime_properties['ip'] = \
            ip_cfg.get('private_ip_address')

        public_ip = \
            ip_cfg.get('public_ip_address', {}).get('ip_address', None)
        if not public_ip:
            pip = PublicIPAddress(azure_config, ctx.logger)
            try:
                pip_name = ip_cfg.get(
                    'public_ip_address', {}).get('id').rsplit('/', 1)[1]
            except AttributeError:
                public_ip = ctx.instance.runtime_properties['ip']
            else:
                public_ip_data = pip.get(resource_group_name, pip_name)
                public_ip = public_ip_data.get("ip_address")
        # Get the Public IP Address endpoint
        ctx.instance.runtime_properties['public_ip'] = \
            public_ip
        # For consistency with other plugins.
        ctx.instance.runtime_properties[PUBLIC_IP_PROPERTY] = \
            public_ip

        # We should also consider that maybe there will be many
        # public ip addresses.
        public_ip_addresses = \
            ctx.instance.runtime_properties.get('public_ip_addresses', [])
        if public_ip not in public_ip_addresses:
            public_ip_addresses.append(public_ip)
        ctx.instance.runtime_properties['public_ip_addresses'] = \
            public_ip_addresses


@operation(resumable=True)
@decorators.with_azure_resource(NetworkInterfaceCard)
def delete(ctx, **_):
    """Deletes a Network Interface Card"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_interface_card = NetworkInterfaceCard(azure_config, ctx.logger,
                                                  api_version)
    utils.handle_delete(
        ctx, network_interface_card, resource_group_name, name)


@operation(resumable=True)
def attach_ip_configuration(ctx, **_):
    """Generates a usable UUID for the NIC's IP Configuration"""
    # Generate the IPConfiguration's name
    azure_config = utils.get_client_config(ctx.source.node.properties)
    resource_group_name = utils.get_resource_group(ctx.source)
    nic_name = ctx.source.instance.runtime_properties.get('name')
    network_interface_card = NetworkInterfaceCard(azure_config, ctx.logger)
    ip_configuration_name = ctx.target.node.properties.get('name')
    ip_configuration_name = \
        get_unique_ip_conf_name(network_interface_card, resource_group_name,
                                nic_name, ip_configuration_name)
    ctx.target.instance.runtime_properties['name'] = ip_configuration_name
