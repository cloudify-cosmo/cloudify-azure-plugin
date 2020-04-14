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
from azure.mgmt.web import WebSiteManagementClient
from msrestazure.azure_exceptions import CloudError

from cloudify.decorators import operation
from cloudify import exceptions as cfy_exc

from cloudify_azure.resources.base import ResourceSDK


class WebApp(ResourceSDK):
    def __init__(
            self, logger, credentials, group_name, app_name, app_config=None):
        self.group_name = group_name
        self.app_name = app_name
        self.logger = logger
        self.app_config = app_config
        self.resource_verify = bool(credentials.get('endpoint_verify', True))
        super(WebApp, self).__init__(credentials)
        self.client = WebSiteManagementClient(
            self.credentials, '{0}'.format(credentials['subscription_id']))
        self.logger.info("Use subscription: {}"
                         .format(credentials['subscription_id']))

    def create_or_update(self):
        """Deploy the template to a resource group."""
        self.logger.info("Create/Updating web app...")
        web_app_async = self.client.web_apps.create_or_update(
            self.group_name,
            self.app_name,
            self.app_config
        )
        return web_app_async.result()

    def get(self):
        return self.client.web_apps.get(
            resource_group_name=self.group_name, name=self.app_name)

    def delete(self):
        """Destroy the given resource group"""
        self.logger.info("Delete web app...")
        self.client.web_apps.delete(
            resource_group_name=self.group_name,
            name=self.app_name)


@operation(resumable=True)
def create(ctx, resource_group, name, app_config, **kwargs):
    azure_auth = ctx.node.properties['azure_config']
    webapp = WebApp(ctx.logger, azure_auth, resource_group, name,
                    app_config)
    if ctx.node.properties.get('use_external_resource', False):
        try:
            webapp.get()
            ctx.logger.info("Using external resource")
        except CloudError:
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing WebApp '{}'.".format(name)
            )
    else:
        webapp.create_or_update()
        ctx.instance.runtime_properties['resource_group'] = resource_group
        ctx.instance.runtime_properties['name'] = name


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_auth = ctx.node.properties['azure_config']
    resource_group = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    webapp = WebApp(ctx.logger, azure_auth, resource_group, name)
    webapp.delete()
