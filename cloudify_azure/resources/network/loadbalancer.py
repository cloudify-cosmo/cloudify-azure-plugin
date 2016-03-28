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
    import get_ip_configurations
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
            utils.get_resource_name(
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


@operation
def create(**_):
    '''Uses an existing, or creates a new, Load Balancer'''
    # Get the Frontend IP Configuration
    # Despite the Azure docs show this as a dict, it's really a list
    fe_ip_cfg = get_ip_configurations()
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
        LoadBalancer(),
        {
            'location': ctx.node.properties.get('location'),
            'tags': ctx.node.properties.get('tags'),
            'properties': utils.dict_update(
                utils.get_resource_config(),
                {
                    'frontendIPConfigurations': fe_ip_cfg
                })
        })


@operation
def delete(**_):
    '''Deletes a Load Balancer'''
    # Delete the resource
    utils.task_resource_delete(
        LoadBalancer())


@operation
def create_backend_pool(**_):
    '''Uses an existing, or creates a new, Load Balancer Backend Pool'''
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_props = lb_rel.target.node.properties
    lb_iface = LoadBalancer()
    # Get the existing pools
    lb_data = lb_iface.get(lb_props.get('name'))
    lb_pools = lb_data.get('properties', dict()).get(
        'backendAddressPools', list())
    lb_pools.append({'name': ctx.node.properties.get('name')})
    # Update the Load Balancer with the new pool
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'backendAddressPools': lb_pools
            }
        },
        name=lb_props.get('name'),
        use_external=lb_props.get('use_external_resource'))


@operation
def delete_backend_pool(**_):
    '''Deletes a Load Balancer Backend Pool'''
    # Get an interface to the Load Balancer
    lb_rel = utils.get_relationship_by_type(
        ctx.instance.relationships,
        constants.REL_CONTAINED_IN_LB)
    lb_props = lb_rel.target.node.properties
    lb_iface = LoadBalancer(_ctx=lb_rel.target)
    # Get the existing pools
    lb_data = lb_iface.get(lb_props.get('name'))
    lb_pools = lb_data.get('properties', dict()).get(
        'backendAddressPools', list())
    for idx, pool in enumerate(lb_pools):
        if pool.get('name') == ctx.node.properties.get('name'):
            del lb_pools[idx]
    # Update the Load Balancer with the new pool
    utils.task_resource_update(
        lb_iface,
        {
            'properties': {
                'backendAddressPools': lb_pools
            }
        },
        name=lb_props.get('name'),
        use_external=lb_props.get('use_external_resource'))


@operation
def attach_nic_to_backend_pool(**_):
    '''
        Attaches a Network Interface Card's IPConfigurations
        to a Load Balancer Backend Pool
    '''
    # Get the ID of the Backend Pool
    be_pool_id = utils.get_full_id_reference(
        BackendAddressPool, _ctx=ctx.source)
    # Get an interface to the Network Interface Card
    nic_iface = NetworkInterfaceCard(_ctx=ctx.target)
    # Get the existing NIC IPConfigurations
    nic_data = nic_iface.get(
        ctx.target.node.properties.get('name'))
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
        }, _ctx=ctx.target)


@operation
def detach_nic_from_backend_pool(**_):
    '''
        Detaches a Network Interface Card's IPConfigurations
        from a Load Balancer Backend Pool
    '''
    # Get the ID of the Backend Pool
    be_pool_id = utils.get_full_id_reference(
        BackendAddressPool, _ctx=ctx.source)
    # Get an interface to the Network Interface Card
    nic_iface = NetworkInterfaceCard(_ctx=ctx.target)
    # Get the existing NIC IPConfigurations
    nic_data = nic_iface.get(
        ctx.target.node.properties.get('name'))
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
        }, _ctx=ctx.target)
