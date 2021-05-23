from azure.mgmt.storage import StorageManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class FileShare(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_STORAGE_FILE_SHARE):
        super(FileShare, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            StorageManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, account_name, share_name):
        self.logger.info("Get File Share...{0}".format(share_name))
        file_share = self.client.file_shares.get(
            resource_group_name=group_name,
            account_name=account_name,
            share_name=share_name
        ).as_dict()
        self.logger.info(
            'Get File Share result: {0}'.format(
                utils.secure_logging_content(file_share)))
        return file_share

    def create(self,
               group_name,
               account_name,
               share_name,
               metadata=None,
               share_quota=None):
        self.logger.info(
            "Create File Share...{0}".format(share_name))
        file_share = self.client.file_shares.create(
            resource_group_name=group_name,
            account_name=account_name,
            share_name=share_name,
            metadata=metadata,
            share_quota=share_quota,
        ).as_dict()
        self.logger.info(
            'Create File Share result  : {0}'.format(
                utils.secure_logging_content(file_share)))
        return file_share

    def delete(self, group_name, account_name, share_name):
        self.logger.info("Deleting File Share...{0}".format(share_name))
        self.client.file_shares.delete(
            resource_group_name=group_name,
            account_name=account_name,
            share_name=share_name
        )
        self.logger.debug(
            'Deleted File Share {0}'.format(share_name))
