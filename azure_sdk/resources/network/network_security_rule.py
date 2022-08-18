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


class NetworkSecurityRule(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(NetworkSecurityRule, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, network_security_group_name, security_rule_name):
        self.logger.info(
            "Get network_security_rule...{0}".format(security_rule_name))
        network_security_rule = self.client.security_rules.get(
            resource_group_name=group_name,
            network_security_group_name=network_security_group_name,
            security_rule_name=security_rule_name
        ).as_dict()
        self.logger.info(
            'Get network_security_rule result: {0}'.format(
                utils.secure_logging_content(network_security_rule))
            )
        return network_security_rule

    def create_or_update(self, group_name, network_security_group_name,
                         security_rule_name, params):
        self.logger.info(
            "Create/Updating network_security_rule...{0}".format(
                security_rule_name))
        async_nsr_creation = self.client.security_rules.begin_create_or_update(
            resource_group_name=group_name,
            network_security_group_name=network_security_group_name,
            security_rule_name=security_rule_name,
            security_rule_parameters=params,
        )
        async_nsr_creation.wait()
        network_security_rule = async_nsr_creation.result().as_dict()
        self.logger.info(
            'create network_security_rule result: {0}'.format(
                utils.secure_logging_content(network_security_rule))
            )
        return network_security_rule

    def delete(self, group_name, network_security_group_name,
               security_rule_name):
        self.logger.info(
            "Deleting network_security_rule...{0}".format(security_rule_name))
        delete_async_operation = self.client.security_rules.begin_delete(
            resource_group_name=group_name,
            network_security_group_name=network_security_group_name,
            security_rule_name=security_rule_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted network_security_rule {0}'.format(
                network_security_group_name))
