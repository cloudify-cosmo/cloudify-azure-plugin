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
    resources.network.LoadBalancer
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Load Balancer interface
'''

# Node properties and logger
from cloudify import ctx
# Base resource class
from cloudify_azure.resources.base import Resource
# Lifecycle operation decorator
from cloudify.decorators import operation
# Exceptions
from cloudify.exceptions import NonRecoverableError
# Logger, API version
from cloudify_azure import (constants, utils)
# Relationship interfaces
from cloudify_azure.resources.network.ipconfiguration \
    import (get_ip_configurations, IPConfiguration, PublicIPAddress)
from cloudify_azure.resources.network.networkinterfacecard \
    import NetworkInterfaceCard

# pylint: disable=R0913
# Constants
LB_ADDRPOOLS_KEY = 'loadBalancerBackendAddressPools'


class LoadBalancer(Resource):
    '''
        Microsoft Azure Load Balancer interface

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
            'Load Balancer',
            '/{0}/{1}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network/loadBalancers'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


class BackendAddressPool(Resource):
    '''
        Microsoft Azure Backend Address Pool interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string load_balancer: Name of the parent Load Balancer
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 load_balancer_name=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        load_balancer_name = load_balancer_name or \
            utils.get_resource_name_ref(
                constants.REL_CONTAINED_IN_LB,
                'load_balancer_name',
                _ctx=_ctx)
        Resource.__init__(
            self,
            'Backend Address Pool',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network',
                'loadBalancers/{0}'.format(load_balancer_name),
                'backendAddressPools'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


class Probe(Resource):
    '''
        Microsoft Azure Probe interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string load_balancer: Name of the parent Load Balancer
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 load_balancer_name=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        load_balancer_name = load_balancer_name or \
            utils.get_resource_name_ref(
                constants.REL_CONTAINED_IN_LB,
                'load_balancer_name',
                _ctx=_ctx)
        Resource.__init__(
            self,
            'Probe',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network',
                'loadBalancers/{0}'.format(load_balancer_name),
                'probes'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


class InboundNATRule(Resource):
    '''
        Microsoft Azure Inbound NAT Rule interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string load_balancer: Name of the parent Load Balancer
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 load_balancer_name=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        load_balancer_name = load_balancer_name or \
            utils.get_resource_name_ref(
                constants.REL_CONTAINED_IN_LB,
                'load_balancer_name',
                _ctx=_ctx)
        Resource.__init__(
            self,
            'Inbound NAT Rule',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network',
                'loadBalancers/{0}'.format(load_balancer_name),
                'inboundNatRules'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


class LoadBalancerRule(Resource):
    '''
        Microsoft Azure Load Balancer Rule interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string load_balancer: Name of the parent Load Balancer
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 load_balancer_name=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        load_balancer_name = load_balancer_name or \
            utils.get_resource_name_ref(
                constants.REL_CONTAINED_IN_LB,
                'load_balancer_name',
                _ctx=_ctx)
        Resource.__init__(
            self,
            'Load Balancer Rule',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network',
                'loadBalancers/{0}'.format(load_balancer_name),
                'loadBalancerRules'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


class FrontendIPConfiguration(Resource):
    '''
        Microsoft Azure Frontend IP Configuration interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string resource_group: Name of the parent Resource Group
    :param string load_balancer: Name of the parent Load Balancer
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self,
                 resource_group=None,
                 load_balancer_name=None,
                 api_version=constants.API_VER_NETWORK,
                 logger=None,
                 _ctx=ctx):
        resource_group = resource_group or \
            utils.get_resource_group(_ctx=_ctx)
        load_balancer_name = load_balancer_name or \
            utils.get_resource_name_ref(
                constants.REL_CONTAINED_IN_LB,
                'load_balancer_name',
                _ctx=_ctx)
        Resource.__init__(
            self,
            'Frontend IP Configuration',
            '/{0}/{1}/{2}/{3}'.format(
                'resourceGroups/{0}'.format(resource_group),
                'providers/Microsoft.Network',
                'loadBalancers/{0}'.format(load_balancer_name),
                'frontendIPConfigurations'
            ),
            api_version=api_version,
            logger=logger,
            _ctx=_ctx)


@operation
def create(**_):
    '''Uses an existing, or creates a new, Load Balancer'''
    utils.generate_resource_name(LoadBalancer(
        api_version=ctx.node.properties.get('api_version',
                                            constants.API_VER_NETWORK)))


@operation
def configure(**_):
    '''Uses an existing, or creates a new, Load Balancer'''
    # Get the Frontend IP Configuration
    fe_ip_cfg = get_ip_configurations(rel=constants.REL_LB_CONNECTED_TO_IPC)
    ctx.logger.debug('fe_ip_cfg: {0}'.format(fe_ip_cfg))
    if not len(fe_ip_cfg):
        raise NonRecoverableError(
            'At least 1 Frontend IP Configuration must be '
            'associated with the Load Balancer')
    # Remove the subnet if there's a public IP present
    for ip_cfg in fe_ip_cfg:
        if ip_cfg.get('properties', dict()).get('publicIPAddress'):
            if ip_cfg.get('properties', dict()).get('subnet'):
                del ip_cfg['properties']['subnet']
    # Create a resource (if necessary)
    utils.task_resource_create(
        LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': utils.dict_update(
                utils.get_resource_config(),
                {
                    'frontendIPConfigurations': fe_ip_cfg
                })
        })
    # Get an interface to the Load Balancer
    lb_iface = LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK))
    lb_data = lb_iface.get(utils.get_resource_name())
    # Get the ID of the Frontend IP Configuration
    for fe_ipc_data in lb_data.get('properties', dict()).get(
            'frontendIPConfigurations', list()):
        ipc_iface = IPConfiguration()
        ipc_id = fe_ipc_data.get('id')
        if not ipc_id:
            break
        ipc_iface.endpoint = '{0}{1}'.format(
            constants.CONN_API_ENDPOINT, ipc_id)
        # Get the Frontend private IP address
        ipc_data = ipc_iface.get()
        ctx.instance.runtime_properties['ip'] = \
            ipc_data.get('properties', dict()).get('privateIPAddress')
        # Get the ID of the Frontend Public IP Configuration
        pipc_iface = PublicIPAddress()
        pipc_id = fe_ipc_data.get('properties', dict()).get(
            'publicIPAddress', dict()).get('id')
        if not pipc_id:
            break
        pipc_iface.endpoint = '{0}{1}'.format(
            constants.CONN_API_ENDPOINT, pipc_id)
        # Get the Frontend public IP address
        pipc_data = pipc_iface.get()
        ctx.instance.runtime_properties['public_ip'] = \
            pipc_data.get('properties', dict()).get('ipAddress')


@operation
def delete(**_):
    '''Deletes a Load Balancer'''
    # Delete the resource
    utils.task_resource_delete(
        LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)))


@operation
def attach_ip_configuration(**_):
    '''Generates a usable UUID for the NIC's IP Configuration'''
    # Generate the IPConfiguration's name
    utils.generate_resource_name(FrontendIPConfiguration(
        load_balancer_name=utils.get_resource_name(_ctx=ctx.source),
        _ctx=ctx.target
    ), _ctx=ctx.target)


@operation
def create_backend_pool(**_):
    '''Uses an existing, or creates a new, Load Balancer Backend Pool'''
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    utils.generate_resource_name(BackendAddressPool(
        api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)))
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK))
    # Get the existing pools
    lb_data = lb_iface.get(lb_name)
    lb_pools = lb_data.get('properties', dict()).get(
        'backendAddressPools', list())
    lb_pools.append({'name': utils.get_resource_name()})
    # Update the Load Balancer with the new pool
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'backendAddressPools': lb_pools
            }
        },
        name=lb_name)


@operation
def delete_backend_pool(**_):
    '''Deletes a Load Balancer Backend Pool'''
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(
        _ctx=lb_rel.target,
        api_version=ctx.node.properties.get('api_version',
                                            constants.API_VER_NETWORK))
    # Get the existing pools
    lb_data = lb_iface.get(lb_name)
    lb_pools = lb_data.get('properties', dict()).get(
        'backendAddressPools', list())
    for idx, pool in enumerate(lb_pools):
        if pool.get('name') == utils.get_resource_name():
            del lb_pools[idx]
    # Update the Load Balancer with the new pool list
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'backendAddressPools': lb_pools
            }
        },
        name=lb_name)


@operation
def create_probe(**_):
    '''Uses an existing, or creates a new, Load Balancer Probe'''
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    utils.generate_resource_name(Probe(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)))
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK))
    # Get the existing probes
    lb_data = lb_iface.get(lb_name)
    lb_probes = lb_data.get('properties', dict()).get(
        'probes', list())
    lb_probes.append({
        'name': utils.get_resource_name(),
        'properties': utils.get_resource_config()
    })
    # Update the Load Balancer with the new probe
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'probes': lb_probes
            }
        },
        name=lb_name)


@operation
def delete_probe(**_):
    '''Deletes a Load Balancer Probe'''
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(
        _ctx=lb_rel.target,
        api_version=ctx.node.properties.get('api_version',
                                            constants.API_VER_NETWORK))
    # Get the existing probes
    lb_data = lb_iface.get(lb_name)
    lb_probes = lb_data.get('properties', dict()).get(
        'probes', list())
    for idx, probe in enumerate(lb_probes):
        if probe.get('name') == utils.get_resource_name():
            del lb_probes[idx]
    # Update the Load Balancer with the new probes list
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'probes': lb_probes
            }
        },
        name=lb_name)


@operation
def create_incoming_nat_rule(**_):
    '''Uses an existing, or creates a new, Load Balancer Incoming NAT Rule'''
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    utils.generate_resource_name(InboundNATRule(
        api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)))
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK))
    # Get the resource config
    res_cfg = utils.get_resource_config()
    # Get the existing rules
    lb_data = lb_iface.get(lb_name)
    lb_rules = lb_data.get('properties', dict()).get(
        'inboundNatRules', list())
    # Get the Load Balancer Frontend IP Configuration
    lb_fe_ipc_name = utils.get_rel_node_name(constants.REL_CONNECTED_TO_IPC)
    lb_fe_ipc_id = utils.get_full_resource_id(
        FrontendIPConfiguration(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ), lb_fe_ipc_name)
    # Update the resource config
    res_cfg['frontendIPConfiguration'] = lb_fe_ipc_id
    lb_rules.append({
        'name': utils.get_resource_name(),
        'properties': res_cfg
    })
    # Update the Load Balancer with the new NAT rule
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'inboundNatRules': lb_rules
            }
        },
        name=lb_name)


@operation
def delete_incoming_nat_rule(**_):
    '''Deletes a Load Balancer Incoming NAT Rule'''
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(
        _ctx=lb_rel.target,
        api_version=ctx.node.properties.get('api_version',
                                            constants.API_VER_NETWORK))
    # Get the existing probes
    lb_data = lb_iface.get(lb_name)
    lb_rules = lb_data.get('properties', dict()).get(
        'inboundNatRules', list())
    for idx, rule in enumerate(lb_rules):
        if rule.get('name') == utils.get_resource_name():
            del lb_rules[idx]
    # Update the Load Balancer with the new NAT rule list
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'inboundNatRules': lb_rules
            }
        },
        name=lb_name)


@operation
def create_rule(**_):
    '''Uses an existing, or creates a new, Load Balancer Rule'''
    # Check if invalid external resource
    if ctx.node.properties.get('use_external_resource', False) and \
       not ctx.node.properties.get('name'):
        raise NonRecoverableError(
            '"use_external_resource" specified without a resource "name"')
    # Generate a name if it doesn't exist
    utils.generate_resource_name(LoadBalancerRule(
        api_version=ctx.node.properties.get('api_version',
                                            constants.API_VER_NETWORK)))
    # Get the resource config
    res_cfg = utils.get_resource_config()
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_iface = LoadBalancer(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK))
    lb_data = lb_iface.get(lb_name)
    # Get the Load Balancer Backend Pool
    lb_be_pool_id = utils.get_rel_id_reference(
        BackendAddressPool, constants.REL_CONNECTED_TO_LB_BE_POOL)
    # Get the Load Balancer Probe
    lb_probe_id = utils.get_rel_id_reference(
        Probe, constants.REL_CONNECTED_TO_LB_PROBE)
    # Get the Load Balancer Frontend IP Configuration
    lb_fe_ipc_name = utils.get_rel_node_name(constants.REL_CONNECTED_TO_IPC)
    lb_fe_ipc_id = utils.get_full_resource_id(
        FrontendIPConfiguration(api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK)
        ), lb_fe_ipc_name)
    # Get the existing Load Balancer Rules
    lb_rules = lb_data.get('properties', dict()).get(
        'loadBalancingRules', list())
    # Update the resource config
    res_cfg['backendAddressPool'] = lb_be_pool_id
    res_cfg['frontendIPConfiguration'] = lb_fe_ipc_id
    res_cfg['probe'] = lb_probe_id
    lb_rules.append({
        'name': utils.get_resource_name(),
        'properties': res_cfg
    })
    # Update the Load Balancer with the new rule
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'loadBalancingRules': lb_rules
            }
        },
        name=lb_name)


@operation
def delete_rule(**_):
    '''
        Deletes a Load Balancer Rule
        TODO: Rewrite this to occur inside of a Relationship Operation
    '''
    if ctx.node.properties.get('use_external_resource', False):
        return
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_name = utils.get_resource_name(lb_rel.target)
    lb_ctx = utils.get_relationship_subject_ctx(ctx, lb_rel.target)
    lb_iface = LoadBalancer(_ctx=lb_ctx, api_version=ctx.node.properties.get(
            'api_version', constants.API_VER_NETWORK))
    # Get the existing rules
    lb_data = lb_iface.get(lb_name)
    lb_rules = lb_data.get('properties', dict()).get(
        'loadBalancingRules', list())
    for idx, rule in enumerate(lb_rules):
        if rule.get('name') == utils.get_resource_name():
            del lb_rules[idx]
    # Update the Load Balancer with the new rules list
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'loadBalancingRules': lb_rules
            }
        },
        name=lb_name)


@operation
def attach_nic_to_backend_pool(**_):
    '''
        Attaches a Network Interface Card's IPConfigurations
        to a Load Balancer Backend Pool
    '''
    # Get the ID of the Backend Pool
    be_pool_id = utils.get_full_id_reference(
        BackendAddressPool, _ctx=ctx.target)
    # Get an interface to the Network Interface Card
    nic_iface = NetworkInterfaceCard(_ctx=ctx.source)
    # Get the existing NIC IPConfigurations
    nic_data = nic_iface.get(utils.get_resource_name(ctx.source))
    nic_ip_cfgs = nic_data.get('properties', dict()).get(
        'ipConfigurations', list())
    # Add the Backend Pool to the NIC IPConfigurations
    for ip_idx, _ in enumerate(nic_ip_cfgs):
        nic_pools = nic_ip_cfgs[ip_idx].get(
            'properties', dict()).get(
                LB_ADDRPOOLS_KEY, list())
        nic_pools.append(be_pool_id)
        nic_ip_cfgs[ip_idx]['properties'][LB_ADDRPOOLS_KEY] = nic_pools
    # Update the NIC IPConfigurations
    utils.task_resource_update(
        nic_iface,
        {
            'properties': {
                'ipConfigurations': nic_ip_cfgs
            }
        }, _ctx=ctx.source)


@operation
def detach_nic_from_backend_pool(**_):
    '''
        Detaches a Network Interface Card's IPConfigurations
        from a Load Balancer Backend Pool
    '''
    # Get the ID of the Backend Pool
    be_pool_id = utils.get_full_id_reference(
        BackendAddressPool, _ctx=ctx.target)
    # Get an interface to the Network Interface Card
    nic_iface = NetworkInterfaceCard(_ctx=ctx.source)
    # Get the existing NIC IPConfigurations
    nic_data = nic_iface.get(utils.get_resource_name(ctx.source))
    nic_ip_cfgs = nic_data.get('properties', dict()).get(
        'ipConfigurations', list())
    # Remove the Backend Pool from the NIC IPConfigurations
    for ip_idx, _ in enumerate(nic_ip_cfgs):
        nic_pools = nic_ip_cfgs[ip_idx].get(
            'properties', dict()).get(
                LB_ADDRPOOLS_KEY, list())
        for pool_idx, nic_pool in enumerate(nic_pools):
            if nic_pool != be_pool_id:
                continue
            del nic_pools[pool_idx]
            nic_ip_cfgs[ip_idx]['properties'][LB_ADDRPOOLS_KEY] = nic_pools
    # Update the NIC IPConfigurations
    utils.task_resource_update(
        nic_iface,
        {
            'properties': {
                'ipConfigurations': nic_ip_cfgs
            }
        }, _ctx=ctx.source)
