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


class PublicIPAddress(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(PublicIPAddress, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, public_ip_address_name):
        self.logger.info(
            "Get public_ip_address...{0}".format(public_ip_address_name))
        public_ip_address = self.client.public_ip_addresses.get(
            resource_group_name=group_name,
            public_ip_address_name=public_ip_address_name
        ).as_dict()
        self.logger.info(
            'Get public_ip_address result: {0}'.format(
                utils.secure_logging_content(public_ip_address)))
        return public_ip_address

    def create_or_update(self, group_name, public_ip_address_name, params):
        self.logger.info(
            "Create/Updating public_ip_address...{0}".format(
                public_ip_address_name))
        async_public_ip_address_creation = \
            self.client.public_ip_addresses.create_or_update(
                resource_group_name=group_name,
                public_ip_address_name=public_ip_address_name,
                parameters=params,
            )
        async_public_ip_address_creation.wait()
        public_ip_address = async_public_ip_address_creation.result().as_dict()
        self.logger.info(
            'create public_ip_address result: {0}'.format(
                utils.secure_logging_content(public_ip_address)))
        return public_ip_address

    def delete(self, group_name, public_ip_address_name):
        self.logger.info(
            "Deleting public_ip_address...{0}".format(public_ip_address_name))
        delete_async_operation = self.client.public_ip_addresses.delete(
            resource_group_name=group_name,
            public_ip_address_name=public_ip_address_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted public_ip_address {0}'.format(public_ip_address_name))
