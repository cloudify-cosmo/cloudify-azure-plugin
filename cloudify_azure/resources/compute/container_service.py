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

from cloudify._compat import text_type
from cloudify.decorators import operation
from azure.mgmt.containerservice import ContainerServiceClient

from cloudify_azure.resources.base import ResourceSDK


class ContainerService(ResourceSDK):

    def __init__(
            self, logger, credentials, group_name,
            container_service_name, container_params={}):
        self.group_name = group_name
        self.container_service_name = container_service_name
        self.logger = logger
        self.container_params = container_params
        self.resource_verify = bool(credentials.get('endpoint_verify', True))
        super(ContainerService, self).__init__(credentials)
        self.client = ContainerServiceClient(
            self.credentials, '{0}'.format(credentials['subscription_id']))

        self.logger.info("Use subscription: {}"
                         .format(credentials['subscription_id']))

    def create_or_update(self):
        """Deploy the template to a resource group."""
        self.logger.info("Create/Updating container service...")

        service_plan_async = self.client.container_services.create_or_update(
            resource_group_name=self.group_name,
            container_service_name=self.container_service_name,
            parameters=self.container_params,
        )
        return service_plan_async.result()

    def get(self):
        return self.client.container_services.get(
            resource_group_name=self.group_name,
            container_service_name=self.container_service_name)

    def delete(self):
        """Destroy the given resource group"""
        self.logger.info("Delete container service...")
        self.client.container_services.delete(
            resource_group_name=self.group_name,
            container_service_name=self.container_service_name)
        self.logger.info("Wait for deleting container service...")


@operation(resumable=True)
def create(ctx, resource_group, name, container_service_config, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        ctx.logger.info("Using external resource")
    else:
        azure_auth = ctx.node.properties['azure_config']
        plan = ContainerService(
            ctx.logger, azure_auth, resource_group, name,
            container_service_config)
        plan.create_or_update()
        ctx.instance.runtime_properties['resource_group'] = resource_group
        ctx.instance.runtime_properties['name'] = name


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_auth = ctx.node.properties['azure_config']
    resource_group = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    plan = ContainerService(ctx.logger, azure_auth, resource_group, name)
    plan.delete()
