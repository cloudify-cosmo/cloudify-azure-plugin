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


class LoadBalancer(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(LoadBalancer, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, load_balancer_name):
        self.logger.info("Get load_balancer...{0}".format(load_balancer_name))
        load_balancer = self.client.load_balancers.get(
            resource_group_name=group_name,
            load_balancer_name=load_balancer_name
        ).as_dict()
        self.logger.info(
            'Get load_balancer result: {0}'.format(
                utils.secure_logging_content(load_balancer))
            )
        return load_balancer

    def create_or_update(self, group_name, load_balancer_name, params):
        self.logger.info(
            "Create/Updating load_balancer...{0}".format(load_balancer_name))
        async_load_balancer_creation = \
            self.client.load_balancers.create_or_update(
                resource_group_name=group_name,
                load_balancer_name=load_balancer_name,
                parameters=params,
            )
        async_load_balancer_creation.wait()
        load_balancer = async_load_balancer_creation.result().as_dict()
        self.logger.info(
            'create load_balancer result: {0}'.format(
                utils.secure_logging_content(load_balancer))
            )
        return load_balancer

    def delete(self, group_name, load_balancer_name):
        self.logger.info(
            "Deleting load_balancer...{0}".format(load_balancer_name))
        delete_async_operation = self.client.load_balancers.delete(
            resource_group_name=group_name,
            load_balancer_name=load_balancer_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted load_balancer {0}'.format(load_balancer_name))


class LoadBalancerBackendAddressPool(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(LoadBalancer, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, load_balancer_name, backend_address_pool_name):
        pass
