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

from azure.mgmt.network import NetworkManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class Subnet(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(Subnet, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, virtual_network_name, subnet_name):
        self.logger.info("Get subnet...{0}".format(subnet_name))
        subnet = self.client.subnets.get(
            resource_group_name=group_name,
            virtual_network_name=virtual_network_name,
            subnet_name=subnet_name
        )
        self.logger.info(
            'Get subnet result: {0}'.format(
                utils.secure_logging_content(subnet.as_dict())))
        return subnet.as_dict()

    def create_or_update(self, group_name, vnet_name, subnet_name, params):
        self.logger.info("Create/Updating subnet...{0}".format(subnet_name))
        async_subnet_creation = self.client.subnets.create_or_update(
            resource_group_name=group_name,
            virtual_network_name=vnet_name,
            subnet_name=subnet_name,
            subnet_parameters=params,
        )
        async_subnet_creation.wait()
        subnet = async_subnet_creation.result()
        self.logger.info(
            'create subnet result: {0}'.format(
                utils.secure_logging_content(subnet.as_dict())))
        return subnet.as_dict()

    def delete(self, group_name, vnet_name, subnet_name):
        self.logger.info("Deleting subnet...{0}".format(subnet_name))
        delete_async_operation = self.client.subnets.delete(
            resource_group_name=group_name,
            virtual_network_name=vnet_name,
            subnet_name=subnet_name
        )
        delete_async_operation.wait()
        self.logger.debug('Deleted subnet {0}'.format(subnet_name))
