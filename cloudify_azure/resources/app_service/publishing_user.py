# #######
# Copyright (c) 2018 GigaSpaces Technologies Ltd. All rights reserved
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
from cloudify.decorators import operation

from cloudify_azure.resources.base import ResourceSDK


class PublishingUser(ResourceSDK):
    def __init__(self, logger, credentials, user_details):
        self.logger = logger
        self.user_details = user_details
        self.resource_verify = bool(credentials.get('endpoint_verify', True))
        super(PublishingUser, self).__init__(credentials)
        self.client = WebSiteManagementClient(
            self.credentials, str(credentials['subscription_id']))
        self.logger.info("Use subscription: {}"
                         .format(credentials['subscription_id']))

    def set_or_update(self):
        self.logger.info("Setting/Updating deployment user...")
        user = self.client.update_publishing_user(self.user_details)
        return user


@operation
def set_user(ctx, user_details, **kwargs):
    azure_auth = ctx.node.properties['azure_config']
    webapp = PublishingUser(ctx.logger, azure_auth, user_details)
    webapp.set_or_update()
