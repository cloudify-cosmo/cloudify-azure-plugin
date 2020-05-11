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


class ManagedCluster(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_MANAGED_CLUSTER):
        super(ManagedCluster, self).__init__(azure_config)
        self.logger = logger
        self.client = ContainerServiceClient(self.credentials,
                                             self.subscription_id)

    def get(self, group_name, resource_name):
        self.logger.info("Get managed_cluster...{0}".format(resource_name))
        managed_cluster = self.client.managed_clusters.get(
            resource_group_name=group_name,
            resource_name=resource_name
        ).as_dict()
        self.logger.info(
            'Get managed_cluster result: {0}'.format(
                utils.secure_logging_content(managed_cluster)))
        return managed_cluster

    def create_or_update(self, group_name, resource_name, params):
        self.logger.info(
            "Create/Updating managed_cluster...{0}".format(resource_name))
        create_async_operation = self.client.managed_clusters.create_or_update(
            resource_group_name=group_name,
            resource_name=resource_name,
            parameters=params,
        )
        create_async_operation.wait()
        managed_cluster = create_async_operation.result().as_dict()
        self.logger.info(
            'Create managed_cluster result: {0}'.format(
                utils.secure_logging_content(managed_cluster))
            )
        return managed_cluster

    def delete(self, group_name, resource_name):
        self.logger.info(
            "Deleting managed_cluster...{0}".format(resource_name))
        delete_async_operation = self.client.managed_clusters.delete(
            resource_group_name=group_name,
            resource_name=resource_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted managed_cluster {0}'.format(resource_name))

    def get_admin_kubeconf(self, group_name, resource_name):
        self.logger.info(
            "Get Admin Kube Config...{0}".format(resource_name))
        admin_credentials = \
            self.client.managed_clusters.list_cluster_admin_credentials(
                resource_group_name=group_name,
                resource_name=resource_name
            ).as_dict()
        return admin_credentials.get("kubeconfigs")[0].get("value")
