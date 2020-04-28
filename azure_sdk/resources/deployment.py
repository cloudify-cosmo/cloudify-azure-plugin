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

from azure.mgmt.resource import ResourceManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class Deployment(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_RESOURCES):
        super(Deployment, self).__init__(azure_config)
        self.logger = logger
        self.client = ResourceManagementClient(self.credentials,
                                               self.subscription_id)

    def get(self, group_name, deployment_name):
        self.logger.info("Get deployment...{0}".format(deployment_name))
        deployment = self.client.deployments.get(
            resource_group_name=group_name,
            deployment_name=deployment_name,
        )
        self.logger.info(
            'Get deployment result: {0}'.format(
                utils.secure_logging_content(deployment.as_dict())))
        return deployment.as_dict()

    def create_or_update(self, group_name, deployment_name, properties,
                         timeout):
        self.logger.info(
            "Create/Updating deployment...{0}".format(deployment_name))
        resource_verify = bool(self.credentials.get('endpoint_verify', True))
        timeout = timeout or 900
        async_deployment_creation = self.client.deployments.create_or_update(
            resource_group_name=group_name,
            deployment_name=deployment_name,
            properties=properties,
            verify=resource_verify,
        )
        async_deployment_creation.wait(timeout=timeout)
        deployment = async_deployment_creation.result()
        self.logger.info(
            'Create deployment result: {0}'.format(
                utils.secure_logging_content(deployment.as_dict())))
        return deployment.as_dict()

    def delete(self, group_name, deployment_name):
        self.logger.info("Deleting deployment...{0}".format(deployment_name))
        delete_async_operation = self.client.deployments.delete(
            resource_group_name=group_name,
            deployment_name=deployment_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted deployment {0}'.format(deployment_name))
