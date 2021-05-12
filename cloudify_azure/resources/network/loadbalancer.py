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
    resources.network.LoadBalancer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Load Balancer interface
"""
from uuid import uuid4
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from cloudify_azure.resources.network.ipconfiguration \
    import get_ip_configurations
from azure_sdk.resources.network.network_interface_card \
    import NetworkInterfaceCard
from azure_sdk.resources.network.public_ip_address \
    import PublicIPAddress
from azure_sdk.resources.network.load_balancer import\
    (LoadBalancer,
     LoadBalancerProbe,
     LoadBalancerLoadBalancingRule,
     LoadBalancerBackendAddressPool)


LB_ADDRPOOLS_KEY = 'load_balancer_backend_address_pools'


def get_unique_lb_prop_name(load_balancer, resource_group_name, lb_name,
                            prop_name, name):
    if not name:
        result = load_balancer.get(resource_group_name, lb_name)
        for _ in range(0, 15):
            name = "{0}".format(uuid4())
            try:
                for item in result.get(prop_name):
                    if item.get("name") == name:
                        name = ""
                        break
                if name:  # found a resource with unique name
                    return name
            except CloudError:  # if exception that means name is not used
                return name
    else:
        return name


@operation(resumable=True)
@decorators.with_generate_name(LoadBalancer)
def create(ctx, **_):
    """Uses an existing, or creates a new, Load Balancer"""
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    ctx.logger.info("Created Load Balancer with name {0} "
                    "inside ResourceGroup {1}".format(name,
                                                      resource_group_name))
    ctx.instance.runtime_properties['resource_group'] = resource_group_name


@operation(resumable=True)
@decorators.with_azure_resource(LoadBalancer)
def configure(ctx, **_):
    """Uses an existing, or creates a new, Load Balancer"""
    # Get the Frontend IP Configuration
    fe_ip_cfg = get_ip_configurations(rel=constants.REL_LB_CONNECTED_TO_IPC)
    ctx.logger.debug('fe_ip_cfg: {0}'.format(fe_ip_cfg))
    if not len(fe_ip_cfg):
        raise cfy_exc.NonRecoverableError(
            'At least 1 Frontend IP Configuration must be '
            'associated with the Load Balancer')
    # Remove the subnet if there's a public IP present
    for ip_cfg in fe_ip_cfg:
        if ip_cfg.get('public_ip_address'):
            if ip_cfg.get('subnet'):
                del ip_cfg['subnet']
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = ctx.instance.runtime_properties.get('name')
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    load_balancer = LoadBalancer(azure_config, ctx.logger, api_version)
    lb_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
    }
    lb_params = \
        utils.handle_resource_config_params(lb_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    lb_params = utils.dict_update(
        lb_params, {
            'frontend_ip_configurations': fe_ip_cfg
        }
    )
    # clean empty values from params
    lb_params = \
        utils.cleanup_empty_params(lb_params)
    try:
        result = \
            load_balancer.create_or_update(resource_group_name,
                                           name,
                                           lb_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create load_balancer '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )

    utils.save_common_info_in_runtime_properties(resource_group_name,
                                                 name,
                                                 result)

    for fe_ipc_data in result.get('frontend_ip_configurations', list()):
        ctx.instance.runtime_properties['ip'] = \
            fe_ipc_data.get('private_ip_address')
        public_ip = \
            fe_ipc_data.get('public_ip_address', {}).get('ip_address', None)
        if not public_ip:
            pip = PublicIPAddress(azure_config, ctx.logger)
            pip_name = \
                ip_cfg.get('public_ip_address').get('id').rsplit('/', 1)[1]
            public_ip_data = pip.get(resource_group_name, pip_name)
            public_ip = public_ip_data.get("ip_address")
        ctx.instance.runtime_properties['public_ip'] = public_ip


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Load Balancer"""
    # Delete the resource
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    load_balancer = LoadBalancer(azure_config, ctx.logger, api_version)
    try:
        load_balancer.get(resource_group_name, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        load_balancer.delete(resource_group_name, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete load_balancer '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def attach_ip_configuration(ctx, **_):
    """Generates a usable UUID for the NIC's IP Configuration"""
    # Generate the IPConfiguration's name
    azure_config = utils.get_client_config(ctx.source.node.properties)
    resource_group_name = \
        ctx.source.instance.runtime_properties.get('resource_group')
    load_balancer_name = ctx.source.instance.runtime_properties.get('name')
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    ip_configuration_name = ctx.target.node.properties.get('name')
    ip_configuration_name = \
        get_unique_lb_prop_name(load_balancer, resource_group_name,
                                load_balancer_name,
                                "frontend_ip_configurations",
                                ip_configuration_name)
    ctx.target.instance.runtime_properties['name'] = ip_configuration_name


@operation(resumable=True)
@decorators.with_generate_name(LoadBalancerBackendAddressPool)
@decorators.with_azure_resource(LoadBalancerBackendAddressPool)
def create_backend_pool(ctx, **_):
    """Uses an existing, or creates a new, Load Balancer Backend Pool"""
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise cfy_exc.NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    load_balancer_name = utils.get_load_balancer(ctx,
                                                 constants.REL_CONTAINED_IN_LB)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    backend_pool_name = utils.get_resource_name(ctx)

    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    # Get the existing pools
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_pools = lb_data.get('backend_address_pools', list())
    lb_pools.append({
        'name': backend_pool_name,
    })
    load_balancer_params = {
        'backend_address_pools': lb_pools,
        'location': lb_rel.target.node.properties.get('location')
    }
    # clean empty values from params
    load_balancer_params = \
        utils.cleanup_empty_params(load_balancer_params)
    try:
        result = load_balancer.create_or_update(resource_group_name,
                                                load_balancer_name,
                                                load_balancer_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create backend_pool '{0}' "
            "failed with this error : {1}".format(backend_pool_name,
                                                  cr.message)
            )
    for item in result.get("backend_address_pools"):
        if item.get("name") == backend_pool_name:
            ctx.instance.runtime_properties['resource_id'] = item.get("id")
            ctx.instance.runtime_properties['resource'] = item
    ctx.instance.runtime_properties["resource_group"] = resource_group_name


@operation(resumable=True)
def delete_backend_pool(ctx, **_):
    """Deletes a Load Balancer Backend Pool"""
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    name = ctx.instance.runtime_properties.get('name')
    # Get the existing pools
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_pools = lb_data.get('backend_address_pools', list())
    for idx, pool in enumerate(lb_pools):
        if pool.get('name') == name:
            del lb_pools[idx]
    # Update the Load Balancer with the new pool list
    lb_params = {
        'backend_address_pools': lb_pools,
        'location': lb_rel.target.node.properties.get('location')
    }
    try:
        load_balancer.create_or_update(resource_group_name, lb_name, lb_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete backend_pool '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
@decorators.with_generate_name(LoadBalancerProbe)
@decorators.with_azure_resource(LoadBalancerProbe)
def create_probe(ctx, **_):
    """Uses an existing, or creates a new, Load Balancer Probe"""
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise cfy_exc.NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    probe_name = utils.get_resource_name(ctx)
    ctx.instance.runtime_properties['name'] = probe_name
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    # Get the existing probes
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_probes = lb_data.get('probes', list())
    lb_probe = \
        utils.handle_resource_config_params({
            'name': probe_name,
        },
            ctx.node.properties.get(
                'resource_config', {}))
    lb_probes.append(lb_probe)
    # Update the Load Balancer with the new probe
    lb_params = {
        'probes': lb_probes,
        'location': lb_rel.target.node.properties.get('location')
    }
    # clean empty values from params
    lb_params = \
        utils.cleanup_empty_params(lb_params)
    try:
        result = load_balancer.create_or_update(resource_group_name, lb_name,
                                                lb_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create probe '{0}' "
            "failed with this error : {1}".format(probe_name,
                                                  cr.message)
            )
    for item in result.get("probes"):
        if item.get("name") == probe_name:
            ctx.instance.runtime_properties['resource_id'] = item.get("id")
            ctx.instance.runtime_properties['resource'] = item
    ctx.instance.runtime_properties["resource_group"] = resource_group_name


@operation(resumable=True)
def delete_probe(ctx, **_):
    """Deletes a Load Balancer Probe"""
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    name = ctx.instance.runtime_properties.get('name')
    # Get the existing probes
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_probes = lb_data.get('probes', list())
    for idx, probe in enumerate(lb_probes):
        if probe.get('name') == name:
            del lb_probes[idx]
    # Update the Load Balancer with the new probes list
    lb_params = {
        'probes': lb_probes,
        'location': lb_rel.target.node.properties.get('location')
    }
    try:
        load_balancer.create_or_update(resource_group_name, lb_name, lb_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete probe '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def create_incoming_nat_rule(ctx, **_):
    """Uses an existing, or creates a new, Load Balancer Incoming NAT Rule"""
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise cfy_exc.NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    load_balancer_name = ctx.node.properties.get('load_balancer_name') or \
        utils.get_resource_name_ref(constants.REL_CONTAINED_IN_LB,
                                    'load_balancer_name',
                                    _ctx=ctx)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    incoming_nat_rule_name = ctx.node.properties.get('name')
    incoming_nat_rule_name = \
        get_unique_lb_prop_name(load_balancer, resource_group_name,
                                load_balancer_name, "inbound_nat_rules",
                                incoming_nat_rule_name)
    ctx.instance.runtime_properties['name'] = incoming_nat_rule_name
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    # Get the existing rules
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_rules = lb_data.get('inbound_nat_rules', list())
    # Get the Load Balancer Frontend IP Configuration
    lb_fe_ipc_id = ""
    rel_type = constants.REL_CONNECTED_TO_IPC
    for rel in ctx.instance.relationships:
        if isinstance(rel_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_type):
                lb_fe_ipc_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
        else:
            if constants.REL_CONNECTED_TO_IPC in rel.type_hierarchy:
                lb_fe_ipc_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
    lb_rules.append({
        'name': incoming_nat_rule_name,
        'frontend_ip_configuration': {
            'id': lb_fe_ipc_id
        }
    })
    lb_rules = \
        utils.handle_resource_config_params(lb_rules,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    # Update the Load Balancer with the new NAT rule
    lb_params = {
        'inbound_nat_rules': lb_rules
    }
    # clean empty values from params
    lb_params = \
        utils.cleanup_empty_params(lb_params)
    try:
        result = load_balancer.create_or_update(resource_group_name, lb_name,
                                                lb_params)
        for item in result.get("inbound_nat_rules"):
            if item.get("name") == incoming_nat_rule_name:
                ctx.instance.runtime_properties['resource_id'] = item.get("id")
                ctx.instance.runtime_properties['resource'] = item
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create incoming_nat_rule '{0}' "
            "failed with this error : {1}".format(incoming_nat_rule_name,
                                                  cr.message)
            )


@operation(resumable=True)
def delete_incoming_nat_rule(ctx, **_):
    """Deletes a Load Balancer Incoming NAT Rule"""
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    name = ctx.instance.runtime_properties.get('name')
    # Get the existing probes
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_rules = lb_data.get('inbound_nat_rules', list())
    for idx, rule in enumerate(lb_rules):
        if rule.get('name') == name:
            del lb_rules[idx]
    # Update the Load Balancer with the new NAT rule list
    lb_params = {
        'inbound_nat_rules': lb_rules
    }
    try:
        load_balancer.create_or_update(resource_group_name, lb_name, lb_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete incoming_nat_rule '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
@decorators.with_generate_name(LoadBalancerLoadBalancingRule)
@decorators.with_azure_resource(LoadBalancerLoadBalancingRule)
def create_rule(ctx, **_):
    """Uses an existing, or creates a new, Load Balancer Rule"""
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise cfy_exc.NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    lb_rule_name = utils.get_resource_name(ctx)
    ctx.instance.runtime_properties['name'] = lb_rule_name
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    lb_data = load_balancer.get(resource_group_name, lb_name)
    # Get the Load Balancer Backend Pool/ Probe/ Frontend IP Configuration
    lb_be_pool_id = ""
    lb_probe_id = ""
    lb_fe_ipc_id = ""
    rel_pool_type = constants.REL_CONNECTED_TO_LB_BE_POOL
    rel_probe_type = constants.REL_CONNECTED_TO_LB_PROBE
    rel_fe_type = constants.REL_CONNECTED_TO_IPC
    for rel in ctx.instance.relationships:
        if isinstance(rel_pool_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_pool_type):
                lb_be_pool_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
        else:
            if rel_pool_type in rel.type_hierarchy:
                lb_be_pool_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
        if isinstance(rel_probe_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_probe_type):
                lb_probe_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
        else:
            if constants.REL_CONNECTED_TO_LB_PROBE in rel.type_hierarchy:
                lb_probe_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
        if isinstance(rel_fe_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_fe_type):
                lb_fe_ipc_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
        else:
            if constants.REL_CONNECTED_TO_IPC in rel.type_hierarchy:
                lb_fe_ipc_id = \
                    rel.target.instance.runtime_properties.get('resource_id')
    # Get the existing Load Balancer Rules
    lb_rules = lb_data.get('load_balancing_rules', list())
    lb_rule = \
        utils.handle_resource_config_params({
            'name': lb_rule_name,
            'frontend_ip_configuration': {'id': lb_fe_ipc_id},
            'backend_address_pool': {'id': lb_be_pool_id},
            'probe': {'id': lb_probe_id}
        },
            ctx.node.properties.get(
                'resource_config', {}))
    lb_rules.append(lb_rule)
    # Update the Load Balancer with the new rule
    lb_params = {
        'load_balancing_rules': lb_rules,
        'location': lb_rel.target.node.properties.get('location')
    }
    # clean empty values from params
    lb_params = \
        utils.cleanup_empty_params(lb_params)
    try:
        result = load_balancer.create_or_update(resource_group_name, lb_name,
                                                lb_params)

    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create load_balancing_rules '{0}' "
            "failed with this error : {1}".format(lb_rule_name,
                                                  cr.message)
            )
    for item in result.get("load_balancing_rules"):
        if item.get("name") == lb_rule_name:
            ctx.instance.runtime_properties['resource_id'] = item.get("id")
            ctx.instance.runtime_properties['resource'] = item
    ctx.instance.runtime_properties["resource_group"] = resource_group_name


@operation(resumable=True)
def delete_rule(ctx, **_):
    """
        Deletes a Load Balancer Rule
        TODO: Rewrite this to occur inside of a Relationship Operation
    """
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    load_balancer = LoadBalancer(azure_config, ctx.logger)
    name = ctx.instance.runtime_properties.get('name')
    # Get the existing rules
    lb_data = load_balancer.get(resource_group_name, lb_name)
    lb_rules = lb_data.get('load_balancing_rules', list())
    for idx, rule in enumerate(lb_rules):
        if rule.get('name') == name:
            del lb_rules[idx]
    # Update the Load Balancer with the new rules list
    lb_params = {
        'load_balancing_rules': lb_rules
    }
    try:
        load_balancer.create_or_update(resource_group_name, lb_name, lb_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete load_balancing_rules '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def attach_nic_to_backend_pool(ctx, **_):
    """
        Attaches a Network Interface Card's IPConfigurations
        to a Load Balancer Backend Pool
    """
    # Get the ID of the Backend Pool
    be_pool_id = {'id': ctx.target.instance.runtime_properties['resource_id']}
    # Get an interface to the Network Interface Card
    azure_config = utils.get_client_config(ctx.source.node.properties)
    resource_group_name = utils.get_resource_group(ctx.source)
    name = ctx.source.instance.runtime_properties['name']
    network_interface_card = NetworkInterfaceCard(azure_config, ctx.logger)
    # Get the existing NIC IPConfigurations
    nic_data = network_interface_card.get(resource_group_name, name)
    nic_ip_cfgs = nic_data.get('ip_configurations', list())
    # Add the Backend Pool to the NIC IPConfigurations
    for ip_idx, _ in enumerate(nic_ip_cfgs):
        nic_pools = nic_ip_cfgs[ip_idx].get(LB_ADDRPOOLS_KEY, list())
        nic_pools.append(be_pool_id)
        nic_ip_cfgs[ip_idx][LB_ADDRPOOLS_KEY] = nic_pools
    # Update the NIC IPConfigurations
    nic_params = {
        'ip_configurations': nic_ip_cfgs,
        'location': ctx.source.node.properties.get('location')
    }
    try:
        network_interface_card.create_or_update(resource_group_name, name,
                                                nic_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "attach nic_to_backend_pool '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )


@operation(resumable=True)
def detach_nic_from_backend_pool(ctx, **_):
    """
        Detaches a Network Interface Card's IPConfigurations
        from a Load Balancer Backend Pool
    """
    # Get the ID of the Backend Pool
    be_pool_id = {'id': ctx.target.instance.runtime_properties['resource_id']}
    # Get an interface to the Network Interface Card
    azure_config = utils.get_client_config(ctx.source.node.properties)
    resource_group_name = utils.get_resource_group(ctx.source)
    name = ctx.source.instance.runtime_properties['name']
    network_interface_card = NetworkInterfaceCard(azure_config, ctx.logger)
    # Get the existing NIC IPConfigurations
    nic_data = network_interface_card.get(resource_group_name, name)
    nic_ip_cfgs = nic_data.get('ip_configurations', list())
    # Remove the Backend Pool from the NIC IPConfigurations
    for ip_idx, _ in enumerate(nic_ip_cfgs):
        nic_pools = nic_ip_cfgs[ip_idx].get(LB_ADDRPOOLS_KEY, list())
        for pool_idx, nic_pool in enumerate(nic_pools):
            if nic_pool != be_pool_id:
                continue
            del nic_pools[pool_idx]
            nic_ip_cfgs[ip_idx][LB_ADDRPOOLS_KEY] = nic_pools
    # Update the NIC IPConfigurations
    nic_params = {
        'ip_configurations': nic_ip_cfgs,
        'location': ctx.source.node.properties.get('location')
    }
    try:
        network_interface_card.create_or_update(resource_group_name, name,
                                                nic_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "detach nic_to_backend_pool '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
