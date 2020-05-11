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

from azure.mgmt.containerservice import ContainerServiceClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class ContainerService(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_CONTAINER):
        super(ContainerService, self).__init__(azure_config)
        self.logger = logger
        self.client = ContainerServiceClient(self.credentials,
                                             self.subscription_id)

    def get(self, group_name, container_service_name):
        self.logger.info(
            "Get container_service...{0}".format(container_service_name))
        container_service = self.client.container_services.get(
            resource_group_name=group_name,
            container_service_name=container_service_name
        ).as_dict()
        self.logger.info(
            'Get container_service result: {0}'.format(
                utils.secure_logging_content(container_service)))
        return container_service

    def create_or_update(self, group_name, container_service_name, params):
        self.logger.info("Create/Updating container_service...{0}".format(
            container_service_name))
        create_async_operation = \
            self.client.container_services.create_or_update(
                resource_group_name=group_name,
                container_service_name=container_service_name,
                parameters=params,
            )
        create_async_operation.wait()
        container_service = create_async_operation.result().as_dict()
        self.logger.info(
            'Create container_service result: {0}'.format(
                utils.secure_logging_content(container_service)))
        return container_service

    def delete(self, group_name, container_service_name):
        self.logger.info("Deleting container_service...{0}".format(
            container_service_name))
        delete_async_operation = self.client.container_services.delete(
            resource_group_name=group_name,
            container_service_name=container_service_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted container_service {0}'.format(container_service_name))
