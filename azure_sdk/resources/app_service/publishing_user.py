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


class PublishingUser(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_APP_SERVICE):
        super(PublishingUser, self).__init__(azure_config)
        self.logger = logger
        self.client = WebSiteManagementClient(self.credentials,
                                              self.subscription_id)

    def set_or_update(self, user_details):
        self.logger.info("Set/Updating publishing_user...")
        publishing_user = self.client.update_publishing_user(
            user_details=user_details
        ).as_dict()
        self.logger.info(
            'Set/Update publishing_user result: {0}'.format(
                utils.secure_logging_content(publishing_user)))
        return publishing_user
