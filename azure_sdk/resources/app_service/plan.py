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

from azure.mgmt.web import WebSiteManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class ServicePlan(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_APP_SERVICE):
        super(ServicePlan, self).__init__(azure_config)
        self.logger = logger
        self.client = WebSiteManagementClient(self.credentials,
                                              self.subscription_id)

    def get(self, group_name, plan_name):
        self.logger.info("Get plan...{0}".format(plan_name))
        plan = self.client.app_service_plans.get(
            resource_group_name=group_name,
            name=plan_name)
        if plan:
            plan = plan.as_dict()
            self.logger.info(
                'Get plan result: {0}'.format(
                    utils.secure_logging_content(plan)))
        return plan

    def create_or_update(self, group_name, plan_name, params):
        self.logger.info("Create/Updating plan...{0}".format(plan_name))
        create_async_operation = \
            self.client.app_service_plans.create_or_update(
                resource_group_name=group_name,
                name=plan_name,
                app_service_plan=params,
            )
        create_async_operation.wait()
        plan = create_async_operation.result().as_dict()
        self.logger.info(
            'Create plan result: {0}'.format(
                utils.secure_logging_content(plan)))
        return plan

    def delete(self, group_name, plan_name):
        self.logger.info("Deleting plan...{0}".format(plan_name))
        self.client.app_service_plans.delete(
            resource_group_name=group_name,
            name=plan_name
        )
        self.logger.debug(
            'Deleted plan {0}'.format(plan_name))
