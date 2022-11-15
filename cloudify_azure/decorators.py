# #######
# Copyright (c) 2020 - 2022 Cloudify Platform Ltd. All rights reserved
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

import re
import random
import string

from uuid import uuid4
from functools import wraps

from msrest.exceptions import ValidationError
from msrestazure.azure_exceptions import CloudError
from azure.core.exceptions import ResourceNotFoundError

from cloudify import exceptions as cfy_exc
from cloudify_common_sdk.utils import \
    skip_creative_or_destructive_operation as skip

from . import utils, constants
from azure_sdk.resources.network.route import Route
from azure_sdk.resources.network.subnet import Subnet
from azure_sdk.resources.deployment import Deployment
from azure_sdk.resources.resource_group import ResourceGroup
from azure_sdk.resources.storage.file_share import FileShare
from azure_sdk.resources.storage.storage_account import StorageAccount
from azure_sdk.resources.network.network_security_rule \
    import NetworkSecurityRule
from azure_sdk.resources.compute.virtual_machine_extension \
    import VirtualMachineExtension
from azure_sdk.resources.network.load_balancer import \
    (LoadBalancerProbe,
     LoadBalancerInboundNatRule,
     LoadBalancerLoadBalancingRule,
     LoadBalancerBackendAddressPool
     )


def sa_name_generator():
    """Generates a unique SA resource name"""
    return ''.join(random.choice(
        string.ascii_lowercase + string.digits) for i in range(3, 24))


def file_share_name_generator():
    """Generates a unique File Share resource name"""
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for i in range(random.randint(24, 63)))


def get_unique_name(resource, resource_group_name, name, **kwargs):
    if not name:
        for _ in range(0, 15):
            # special naming handling
            if isinstance(resource, StorageAccount):
                name = sa_name_generator()
            elif isinstance(resource, FileShare):
                name = file_share_name_generator()
            else:
                name = "{0}".format(uuid4())
            try:
                # handle speical cases
                # resource_group
                if isinstance(resource, ResourceGroup):
                    result = resource.get(name)
                # virtual_machine_extension
                elif isinstance(resource, VirtualMachineExtension):
                    vm_name = kwargs['vm_name']
                    result = resource.get(resource_group_name, vm_name, name)
                # subnet
                elif isinstance(resource, Subnet):
                    vnet_name = kwargs['vnet_name']
                    result = resource.get(resource_group_name, vnet_name, name)
                # route
                elif isinstance(resource, Route):
                    rtbl_name = kwargs['rtbl_name']
                    result = resource.get(resource_group_name, rtbl_name, name)
                # network_security_rule
                elif isinstance(resource, NetworkSecurityRule):
                    nsg_name = kwargs['nsg_name']
                    result = resource.get(resource_group_name, nsg_name, name)
                elif isinstance(resource, (LoadBalancerBackendAddressPool,
                                           LoadBalancerLoadBalancingRule,
                                           LoadBalancerInboundNatRule,
                                           LoadBalancerProbe)):
                    lb_name = kwargs['lb_name']
                    result = resource.get(resource_group_name, lb_name, name)
                elif isinstance(resource, FileShare):
                    sa_name = kwargs['sa_name']
                    result = resource.get(resource_group_name, sa_name, name)
                else:
                    result = resource.get(resource_group_name, name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except (CloudError, ResourceNotFoundError):  # name is not used
                return name
    else:
        return name


def with_generate_name(resource_class_name):
    def wrapper_outer(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            ctx = kwargs['ctx']
            try:
                # check if name is set or not and generate one if it wasn't set
                plugin_props = getattr(ctx.plugin, 'properties', {})
                azure_config = utils.get_client_config(plugin_props,
                                                       ctx.node.properties)
                resource = resource_class_name(azure_config, ctx.logger)
                name = utils.get_resource_name(ctx)
                resource_group_name = name
                if not isinstance(resource, ResourceGroup):
                    resource_group_name = utils.get_resource_group(ctx)
                if not name:
                    ctx.logger.info(
                        "Generating unique name for {0}".format(
                            resource_class_name))
                    # handle special cases
                    # virtual_machine_extension
                    if isinstance(resource, VirtualMachineExtension):
                        vm_name = \
                            ctx.node.properties.get('virtual_machine_name')
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            vm_name=vm_name)
                    # subnet
                    elif isinstance(resource, Subnet):
                        vnet_name = utils.get_virtual_network(ctx)
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            vnet_name=vnet_name)
                    # route
                    elif isinstance(resource, Route):
                        rtbl_name = utils.get_route_table(ctx)
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            rtbl_name=rtbl_name)
                    # network_security_rule
                    elif isinstance(resource, NetworkSecurityRule):
                        nsg_name = utils.get_network_security_group(ctx)
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            nsg_name=nsg_name)
                    elif isinstance(resource, Deployment):
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name)
                    elif isinstance(resource, (LoadBalancerBackendAddressPool,
                                               LoadBalancerLoadBalancingRule,
                                               LoadBalancerInboundNatRule,
                                               LoadBalancerProbe)):
                        lb_name = utils.get_load_balancer(ctx)
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            lb_name=lb_name)
                    elif isinstance(resource, FileShare):
                        sa_name = utils.get_storage_account(ctx)
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            sa_name=sa_name)
                    else:
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name)
                ctx.instance.runtime_properties['name'] = name
            except CloudError:
                raise cfy_exc.NonRecoverableError(
                    "Can't generate name for {0}".format(
                        resource_class_name))
            return func(*args, **kwargs)
        return wrapper_inner
    return wrapper_outer


def get_create_op(op_name, node_type):
    """ Determine if we are dealing with a creation operation.
    Normally we just do the logic in the last return. However, we may want
    special behavior for some types.

    :param op_name: ctx.operation.name.
    :param node_type: ctx.node.type_hierarchy
    :return: bool
    """
    op = op_name.split('.')[-1]
    if utils.check_types_in_hierarchy(constants.NIC_NODE_TYPE, node_type):
        if 'configure' in op:  # We do want to fall back on 'create' as well.
            return True
    elif utils.check_types_in_hierarchy(constants.VM_NODE_TYPE, node_type):
        if 'configure' in op:
            return True
    elif utils.check_types_in_hierarchy(constants.LB_NODE_TYPE, node_type):
        if 'configure' in op:
            return True
    return 'create' in op


def get_delete_op(op_name, node_type=None):
    """ Determine if we are dealing with a deletion operation.
    Normally we just do the logic in the last return. However, we may want
    special behavior for some types.

    :param op_name: ctx.operation.name.
    :param node_type: ctx.node.type_hierarchy
    :return: bool
    """
    op = op_name.split('.')[-1]
    return 'delete' in op


def get_special_condition(type_list, op_name):
    op = op_name.split('.')[-1]
    if 'cloudify.azure.Deployment' in type_list:
        return True
    elif op not in ['create', 'delete']:
        return True
    return False


def with_azure_resource(resource_class_name):
    def wrapper_outer(func):
        @wraps(func)
        def wrapper_inner(*args, **kwargs):
            ctx = kwargs['ctx']
            name = utils.get_resource_name(ctx)
            # check if azure_config is given and if the resource
            # is external or not
            azure_config = utils.get_client_config(ctx.node.properties)
            resource_factory = ResourceGetter(ctx, azure_config, name)
            try:
                exists = resource_factory.get_resource(resource_class_name)
            except ResourceNotFoundError:
                exists = False
            special_condition = get_special_condition(ctx.node.type_hierarchy,
                                                      ctx.operation.name)
            create_op = get_create_op(ctx.operation.name,
                                      ctx.node.type_hierarchy)
            delete_op = get_delete_op(ctx.operation.name,
                                      ctx.node.type_hierarchy)
            # There is now a good idea whether the desired resource exists.
            # Now find out if it is expected and if it does or doesn't.
            if not skip(
                    resource_class_name,
                    name,
                    _ctx_node=ctx.node,
                    exists=exists,
                    special_condition=special_condition,
                    create_operation=create_op,
                    delete_operation=delete_op):
                return func(*args, **kwargs)
        return wrapper_inner
    return wrapper_outer


class ResourceGetter(object):

    def __init__(self, ctx, azure_config, resource_name):
        self.azure_config = azure_config
        self.ctx = ctx
        self.name = resource_name
        self.resource_group_name = None

    def get_resource(self, resource_class_name):
        try:
            resource = resource_class_name(self.azure_config, self.ctx.logger)
            name = self.name
            parent = {}
            if not isinstance(resource, ResourceGroup):
                resource_group_name = utils.get_resource_group(self.ctx)
                self.resource_group_name = resource_group_name
                # handle speical cases
                # resource_group
            if isinstance(resource, ResourceGroup):
                exists = resource.get(self.name)
                resource_group_name = \
                    self.resource_group_name = self.name
            elif isinstance(resource, Deployment):
                exists = resource.get(resource_group_name, self.name)
                # virtual_machine_extension
            elif isinstance(resource, VirtualMachineExtension):
                vm_name = self.ctx.node.properties.get('virtual_machine_name')
                parent.update({'virtual_machine': vm_name})
                exists = resource.get(resource_group_name, vm_name, self.name)
                # subnet
            elif isinstance(resource, Subnet):
                vnet_name = utils.get_virtual_network(self.ctx)
                parent.update({'virtual_network': vnet_name})
                exists = resource.get(resource_group_name, vnet_name,
                                      self.name)
                # route
            elif isinstance(resource, Route):
                rtbl_name = utils.get_route_table(self.ctx)
                parent.update({'route_table': rtbl_name})
                exists = resource.get(resource_group_name, rtbl_name,
                                      self.name)
                # network_security_rule
            elif isinstance(resource, NetworkSecurityRule):
                nsg_name = utils.get_network_security_group(self.ctx)
                parent.update({'network_security_group': nsg_name})
                exists = resource.get(resource_group_name, nsg_name, self.name)
                # load_balancer_backend_address_pool
            elif isinstance(resource, (LoadBalancerBackendAddressPool,
                                       LoadBalancerLoadBalancingRule,
                                       LoadBalancerInboundNatRule,
                                       LoadBalancerProbe)):
                lb_name = utils.get_load_balancer(self.ctx)
                parent.update({'load_balancer': lb_name})
                exists = resource.get(resource_group_name,
                                      lb_name,
                                      self.name)
            # file share
            elif isinstance(resource, FileShare):
                sa_name = utils.get_storage_account(self.ctx)
                parent.update({'storage_account': sa_name})
                exists = resource.get(resource_group_name, sa_name, self.name)
            else:
                exists = resource.get(resource_group_name, self.name)
            if 'resource' not in self.ctx.instance.runtime_properties:

                utils.save_common_info_in_runtime_properties(
                    resource_group_name,
                    name,
                    exists,
                    parent
                )
        except CloudError:
            exists = None
        return exists


def get_operation_config(op, runtime_properties, properties):
    op_config = runtime_properties.get('operation_config', {})
    if 'create' in op:
        if 'create' in op_config:
            return op_config['create']
        return properties['operation_config']['create']
    elif 'start' in op:
        if 'update' in op_config:
            return op_config['update']
        return properties['operation_config']['update']
    elif 'delete' in op:
        if 'delete' in op_config:
            return op_config['delete']
        return properties['operation_config']['delete']
    raise cfy_exc.NonRecoverableError(
        'The operation config provided is invalid.')


def get_custom_resource_config(runtime_properties, properties):
    resource_config = runtime_properties.get('resource_config', {})
    if not resource_config:
        return properties['resource_config']
    return resource_config


def configure_custom_resource(func):
    @wraps(func)
    def wrapper(**kwargs):
        ctx = kwargs['ctx']
        op_name = ctx.operation.name.split('.')[-1]
        runprops = ctx.instance.runtime_properties
        props = ctx.node.properties
        resource = kwargs.pop(
            'resource_config',
            get_custom_resource_config(runprops, props))
        operation = kwargs.pop(
            'operation_config',
            get_operation_config(op_name, runprops, props)
        )
        client = utils.get_client_config(ctx.node.properties)
        api = ctx.node.properties.get('api_version')
        try:
            return func(ctx, resource, operation, client, api)
        except (TypeError, AttributeError) as e:
            raise cfy_exc.NonRecoverableError(str(e))
        except ValidationError as e:
            raise cfy_exc.NonRecoverableError(str(e))
        except NotImplementedError as e:
            bad_api_regex = re.compile(
                r'APIVersion\s([\d]{2,4}\-){2}[\d]{2}\sis\snot\savailable')
            if bad_api_regex.search(str(e)):
                raise cfy_exc.NonRecoverableError(
                    'Invalid API version for current Azure Plugin wagon.')
            raise e

    return wrapper
