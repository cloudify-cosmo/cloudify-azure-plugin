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


class Route(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_NETWORK):
        super(Route, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            NetworkManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, route_table_name, route_name):
        self.logger.info("Get route...{0}".format(route_name))
        route = self.client.routes.get(
            resource_group_name=group_name,
            route_table_name=route_table_name,
            route_name=route_name
        ).as_dict()
        self.logger.info(
            'Get route result: {0}'.format(
                utils.secure_logging_content(route)))
        return route

    def create_or_update(self, group_name, route_table_name, route_name,
                         params):
        self.logger.info("Create/Updating route...{0}".format(route_name))
        async_route_creation = self.client.routes.create_or_update(
            resource_group_name=group_name,
            route_table_name=route_table_name,
            route_name=route_name,
            route_parameters=params,
        )
        async_route_creation.wait()
        route = async_route_creation.result().as_dict()
        self.logger.info(
            'create route result: {0}'.format(
                utils.secure_logging_content(route)))
        return route

    def delete(self, group_name, route_table_name, route_name):
        self.logger.info("Deleting route...{0}".format(route_name))
        delete_async_operation = self.client.routes.delete(
            resource_group_name=group_name,
            route_table_name=route_table_name,
            route_name=route_name
        )
        delete_async_operation.wait()
        self.logger.debug('Deleted route {0}'.format(route_name))
