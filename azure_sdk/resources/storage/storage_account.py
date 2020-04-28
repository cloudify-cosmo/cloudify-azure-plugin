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

from azure.mgmt.storage import StorageManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class StorageAccount(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_STORAGE):
        super(StorageAccount, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            StorageManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, account_name):
        self.logger.info("Get Storage Account...{0}".format(account_name))
        storage_account = self.client.storage_accounts.get_properties(
            resource_group_name=group_name,
            account_name=account_name
        )
        self.logger.info(
            'Get storage_account result: {0}'.format(
                utils.secure_logging_content(storage_account.as_dict())))
        return storage_account.as_dict()

    def create(self, group_name, account_name, parameters):
        self.logger.info(
            "Create/Updating Storage Account...{0}".format(account_name))
        async_storage_account_creation = self.client.storage_accounts.create(
            resource_group_name=group_name,
            account_name=account_name,
            parameters=parameters
        )
        async_storage_account_creation.wait()
        storage_account = async_storage_account_creation.result()
        self.logger.info(
            'storage_account : {0}'.format(
                utils.secure_logging_content(storage_account.as_dict())))
        return storage_account.as_dict()

    def delete(self, group_name, account_name):
        self.logger.info("Deleting Storage Account...{0}".format(account_name))
        self.client.storage_accounts.delete(
            resource_group_name=group_name,
            account_name=account_name
        )
        self.logger.debug(
            'Deleted Storage Account {0}'.format(account_name))

    def list_keys(self, group_name, account_name):
        self.logger.info(
            "List Storage Account Keys...{0}".format(account_name))
        storage_keys = self.client.storage_accounts.list_keys(
            resource_group_name=group_name,
            account_name=account_name
        )
        self.logger.debug(
            'Storage Account Keys {0}'.format(
                utils.secure_logging_content(storage_keys.as_dict())))
        return storage_keys.as_dict()
