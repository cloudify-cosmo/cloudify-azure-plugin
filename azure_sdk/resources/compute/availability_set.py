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

from azure.mgmt.compute import ComputeManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class AvailabilitySet(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_COMPUTE):
        super(AvailabilitySet, self).__init__(azure_config)
        self.logger = logger
        self.api_version = api_version
        self.client = \
            ComputeManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, availability_set_name):
        self.logger.info(
            "Get availability_set...{0}".format(availability_set_name))
        availability_set = self.client.availability_sets.get(
            resource_group_name=group_name,
            availability_set_name=availability_set_name
        ).as_dict()
        self.logger.info(
            'Get availability_set result: {0}'.format(
                utils.secure_logging_content(availability_set)))
        return availability_set

    def create_or_update(self, group_name, availability_set_name, params):
        self.logger.info("Create/Updating availability_set...{0}".format(
            availability_set_name))
        old_naming = ['2015', '2016']
        # the above years the parameter is name - others availability_set_name
        if any(x in self.api_version for x in old_naming):
            availability_set = self.client.availability_sets.create_or_update(
                resource_group_name=group_name,
                name=availability_set_name,
                parameters=params,
            ).as_dict()
        else:
            availability_set = self.client.availability_sets.create_or_update(
                resource_group_name=group_name,
                availability_set_name=availability_set_name,
                parameters=params,
            ).as_dict()
        self.logger.info(
            'Create availability_set result: {0}'.format(
                utils.secure_logging_content(availability_set)))
        return availability_set

    def delete(self, group_name, availability_set_name):
        self.logger.info(
            "Deleting availability_set...{0}".format(availability_set_name))
        self.client.availability_sets.delete(
            resource_group_name=group_name,
            availability_set_name=availability_set_name
        )
        self.logger.debug(
            'Deleted availability_set {0}'.format(availability_set_name))
