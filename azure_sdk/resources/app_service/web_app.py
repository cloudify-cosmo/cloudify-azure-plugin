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

from azure.mgmt.web import WebSiteManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class WebApp(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_APP_SERVICE):
        super(WebApp, self).__init__(azure_config)
        self.logger = logger
        self.client = WebSiteManagementClient(self.credentials,
                                              self.subscription_id)

    def get(self, group_name, web_app_name):
        self.logger.info("Get web_app...{0}".format(web_app_name))
        web_app = self.client.web_apps.get(
            resource_group_name=group_name,
            name=web_app_name)
        if web_app:
            web_app = web_app.as_dict()
            self.logger.info(
                'Get web_app result: {0}'.format(
                    utils.secure_logging_content(web_app)))
        return web_app

    def create_or_update(self, group_name, web_app_name, params):
        self.logger.info("Create/Updating web_app...{0}".format(web_app_name))
        create_async_operation = self.client.web_apps.create_or_update(
            resource_group_name=group_name,
            name=web_app_name,
            site_envelope=params,
        )
        create_async_operation.wait()
        web_app = create_async_operation.result().as_dict()
        self.logger.info(
            'Create web_app result: {0}'.format(
                utils.secure_logging_content(web_app)))
        return web_app

    def delete(self, group_name, web_app_name):
        self.logger.info("Deleting web_app...{0}".format(web_app_name))
        self.client.web_apps.delete(
            resource_group_name=group_name,
            name=web_app_name
        )
        self.logger.debug(
            'Deleted web_app {0}'.format(web_app_name))
