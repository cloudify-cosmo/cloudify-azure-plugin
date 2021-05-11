# #######
# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
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
import random
import string

from uuid import uuid4
from functools import wraps

from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc

from cloudify_azure import utils
from azure_sdk.resources.network.route import Route
from azure_sdk.resources.network.subnet import Subnet
from azure_sdk.resources.deployment import Deployment
from azure_sdk.resources.resource_group import ResourceGroup
from azure_sdk.resources.storage.storage_account import StorageAccount
from azure_sdk.resources.network.network_security_rule \
    import NetworkSecurityRule
from azure_sdk.resources.compute.virtual_machine_extension \
    import VirtualMachineExtension
from azure_sdk.resources.network.load_balancer import \
    LoadBalancerBackendAddressPool


def sa_name_generator():
    """Generates a unique SA resource name"""
    return ''.join(random.choice(
        string.ascii_lowercase + string.digits) for i in range(3, 24))


def get_unique_name(resource, resource_group_name, name, **kwargs):
    if not name:
        for _ in range(0, 15):
            # special naming handling
            if isinstance(resource, StorageAccount):
                name = sa_name_generator()
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
                elif isinstance(resource, LoadBalancerBackendAddressPool):
                    lb_name = kwargs['lb_name']
                    result = resource.get(resource_group_name, lb_name, name)
                else:
                    result = resource.get(resource_group_name, name)
                if result:  # found a resource with same name
                    name = ""
                    continue
            except CloudError:  # this means name is not used
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
                azure_config = ctx.node.properties.get('azure_config')
                if not azure_config.get("subscription_id"):
                    azure_config = ctx.node.properties.get('client_config')
                else:
                    ctx.logger.warn("azure_config is deprecated "
                                    "please use client_config, "
                                    "in later version it will be removed")
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
                    elif isinstance(resource, LoadBalancerBackendAddressPool):
                        lb_name = utils.get_load_balancer(ctx)
                        name = get_unique_name(
                            resource=resource,
                            resource_group_name=resource_group_name,
                            name=name,
                            lb_name=lb_name)
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
            exists = resource_factory.get_resource(resource_class_name)
            # There is now a good idea whether the desired resource exists.
            # Now find out if it is expected and if it does or doesn't.
            expected = ctx.node.properties.get(
                'use_external_resource', False)
            create_anyway = ctx.node.properties.get('create_if_missing', False)
            use_anyway = ctx.node.properties.get('use_if_exists', False)
            # We should use and existing resource.
            use_existing = (exists and expected) or \
                           (exists and not expected and use_anyway)
            # We should create a new resource.
            create = (not exists and not expected) or \
                     (not exists and expected and create_anyway)
            # ARM deployments are idempotent. This logic should be expanded
            # to other idempotent deployments.
            arm_deployment = 'cloudify.azure.Deployment' in \
                             ctx.node.type_hierarchy
            create_op = 'create' in ctx.operation.name.split('.')[-1]

            if not exists and expected and not create_anyway:
                raise cfy_exc.NonRecoverableError(
                    "Can't use non-existing {0} '{1}'.".format(
                        resource_class_name, name))
            elif use_existing and not (create_op and arm_deployment):
                ctx.logger.info("Using external resource")
                utils.save_common_info_in_runtime_properties(
                    resource_group_name=resource_factory.resource_group_name,
                    resource_name=name,
                    resource_get_create_result=exists)
                return
            elif not create and not (create_op and arm_deployment):
                raise cfy_exc.NonRecoverableError(
                    "Can't use non-existing {0} '{1}'.".format(
                        resource_class_name, name))
            elif create and exists and ctx.workflow_id not in \
                    ['update', 'execute_operation']:
                ctx.logger.warn("Resource with name {0} exists".format(name))
                if not arm_deployment:
                    ctx.logger.warn('Not updating new resource.')
                    return
            ctx.logger.info('Creating or updating resource: {name}'.format(
                name=name))
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
            if not isinstance(resource, ResourceGroup):
                resource_group_name = utils.get_resource_group(self.ctx)
                self.resource_group_name = resource_group_name
                # handle speical cases
                # resource_group
            if isinstance(resource, ResourceGroup):
                exists = resource.get(self.name)
                self.resource_group_name = self.name
            elif isinstance(resource, Deployment):
                exists = resource.get(resource_group_name, self.name)
                # virtual_machine_extension
            elif isinstance(resource, VirtualMachineExtension):
                vm_name = \
                    self.ctx.node.properties.get('virtual_machine_name')
                exists = resource.get(resource_group_name, vm_name, self.name)
                # subnet
            elif isinstance(resource, Subnet):
                vnet_name = utils.get_virtual_network(self.ctx)
                exists = resource.get(resource_group_name, vnet_name,
                                      self.name)
                # route
            elif isinstance(resource, Route):
                rtbl_name = utils.get_route_table(self.ctx)
                exists = resource.get(resource_group_name, rtbl_name,
                                      self.name)
                # network_security_rule
            elif isinstance(resource, NetworkSecurityRule):
                nsg_name = utils.get_network_security_group(self.ctx)
                exists = resource.get(resource_group_name, nsg_name, self.name)
                # load_balancer_backend_address_pool
            elif isinstance(resource, LoadBalancerBackendAddressPool):
                lb_name = utils.get_load_balancer(self.ctx)
                exists = resource.get(resource_group_name,
                                      lb_name,
                                      self.name)
            else:
                exists = resource.get(resource_group_name, self.name)
        except CloudError:
            exists = None
        return exists
