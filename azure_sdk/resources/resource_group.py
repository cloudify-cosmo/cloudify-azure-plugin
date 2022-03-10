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

from azure.mgmt.resource import ResourceManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class ResourceGroup(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_RESOURCES):
        self.logger = logger
        self.logger.info('Sending these credentials: {}'.format(azure_config))
        super(ResourceGroup, self).__init__(azure_config)
        self.client = \
            ResourceManagementClient(self.credentials, self.subscription_id,
                                     api_version=api_version)

    def get(self, group_name):
        self.logger.info("Get resource_group...{0}".format(group_name))
        resource_group = self.client.resource_groups.get(
            resource_group_name=group_name).as_dict()
        self.logger.info(
            'Get resource_group result: {0}'.format(
                utils.secure_logging_content(resource_group)))
        return resource_group

    def create_or_update(self, group_name, resource_group_params):
        self.logger.info(
            "Create/Updating resource_group...{0}".format(group_name))
        resource_group = self.client.resource_groups.create_or_update(
            resource_group_name=group_name,
            parameters=resource_group_params,
        ).as_dict()
        self.logger.info(
            'Create resource_group result: {0}'.format(
                utils.secure_logging_content(resource_group)))
        return resource_group

    def delete(self, group_name):
        self.logger.info("Deleting resource_group...{0}".format(group_name))
        delete_async_operation = self.client.resource_groups.begin_delete(
            resource_group_name=group_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted resource_group {0}'.format(group_name))

    def list_resources(self, group_name):
        """
        List resources of resource group by id.
        """
        self.logger.info(
            'List resources of resource_group...{0}'.format(group_name))
        resources_list_iter = self.client.resources.list_by_resource_group(
            resource_group_name=group_name,
            expand='createdTime,changedTime,ProvisioningState')
        resources_list = [{'id': resource.id,
                           'created_time': resource.created_time,
                           'changed_time': resource.changed_time,
                           'provisioning_state': resource.provisioning_state}
                          for resource in resources_list_iter]
        self.logger.info('List resources of resource group {0}'
                         ' result: {1}'.format(group_name, resources_list))
        return resources_list
