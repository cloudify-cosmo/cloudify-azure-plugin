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

from azure.mgmt.network import NetworkManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class VirtualNetwork(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(VirtualNetwork, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, virtual_network_name):
        self.logger.info(
            "Get virtual_network...{0}".format(virtual_network_name))
        virtual_network = self.client.virtual_networks.get(
            resource_group_name=group_name,
            virtual_network_name=virtual_network_name
        ).as_dict()
        self.logger.info(
            'Get virtual_network result: {0}'.format(
                utils.secure_logging_content(virtual_network)))
        return virtual_network

    def create_or_update(self, group_name, virtual_network_name, params):
        self.logger.info(
            "Create/Updating virtual_network...{0}".format(
                virtual_network_name))
        async_vnet_creation = self.client.virtual_networks.create_or_update(
            resource_group_name=group_name,
            virtual_network_name=virtual_network_name,
            parameters=params,
        )
        async_vnet_creation.wait()
        virtual_network = async_vnet_creation.result().as_dict()
        self.logger.info(
            'create virtual_network result: {0}'.format(
                utils.secure_logging_content(virtual_network)))
        return virtual_network

    def delete(self, group_name, virtual_network_name):
        self.logger.info(
            "Deleting virtual_network...{0}".format(virtual_network_name))
        delete_async_operation = self.client.virtual_networks.delete(
            resource_group_name=group_name,
            virtual_network_name=virtual_network_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted virtual_network {0}'.format(virtual_network_name))
