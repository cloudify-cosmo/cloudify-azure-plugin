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
from azure.core.exceptions import ResourceNotFoundError

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class VirtualMachine(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_COMPUTE):
        super(VirtualMachine, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            ComputeManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, vm_name):
        self.logger.info("Get virtual_machine...{0}".format(vm_name))
        virtual_machine = self.client.virtual_machines.get(
            resource_group_name=group_name,
            vm_name=vm_name
        ).as_dict()
        self.logger.info(
            'Get virtual_machine result: {0}'.format(
                utils.secure_logging_content(virtual_machine))
            )
        return virtual_machine

    def get_instance_view(self, group_name, vm_name):
        self.logger.info("Get virtual_machine instance_view...{0}".format(
            vm_name))
        virtual_machine = self.client.virtual_machines.get(
            resource_group_name=group_name,
            vm_name=vm_name,
            expand='instanceView'
        ).as_dict()
        self.logger.info(
            'Get virtual_machine instance_view result: {0}'.format(
                utils.secure_logging_content(virtual_machine))
            )
        return virtual_machine

    def create_or_update(self, group_name, vm_name, params):
        self.logger.info(
            "Create/Updating virtual_machine...{0}".format(vm_name))
        create_async_operation = \
            self.client.virtual_machines.begin_create_or_update(
                resource_group_name=group_name,
                vm_name=vm_name,
                parameters=params,
            )
        create_async_operation.wait()
        virtual_machine = create_async_operation.result().as_dict()
        self.logger.info(
            'Create virtual_machine result: {0}'.format(
                utils.secure_logging_content(virtual_machine))
            )
        return virtual_machine

    def delete(self, group_name, vm_name):
        self.logger.info(
            "Deleting virtual_machine...{0}".format(vm_name))
        try:
            delete_async_operation = self.client.virtual_machines.begin_delete(
                resource_group_name=group_name,
                vm_name=vm_name
            )
        except ResourceNotFoundError:
            self.logger.debug('Deleted machine not found.')
        else:
            delete_async_operation.wait()
        self.logger.debug(
            'Deleted virtual_machine {0}'.format(vm_name))

    def start(self, group_name, vm_name):
        self.logger.info(
            "Starting virtual_machine...{0}".format(vm_name))
        start_async_operation = self.client.virtual_machines.begin_start(
            resource_group_name=group_name,
            vm_name=vm_name
        )
        start_async_operation.wait()
        self.logger.debug(
            'Started virtual_machine {0}'.format(vm_name))

    def power_off(self, group_name, vm_name):
        self.logger.info(
            "Stopping virtual_machine...{0}".format(vm_name))
        stop_async_operation = self.client.virtual_machines.begin_power_off(
            resource_group_name=group_name,
            vm_name=vm_name
        )
        stop_async_operation.wait()
        self.logger.debug(
            'Stopped virtual_machine {0}'.format(vm_name))

    def restart(self, group_name, vm_name):
        self.logger.info(
            "Restarting virtual_machine...{0}".format(vm_name))
        restart_async_operation = self.client.virtual_machines.begin_restart(
            resource_group_name=group_name,
            vm_name=vm_name
        )
        restart_async_operation.wait()
        self.logger.debug(
            'Restarted virtual_machine {0}'.format(vm_name))

    def run_command(self, group_name, vm_name, cmd_params):
        self.logger.info(
            "Running command on virtual_machine...{0}".format(vm_name))
        run_cmd_async_operation = \
            self.client.virtual_machines.begin_run_command(
                resource_group_name=group_name,
                vm_name=vm_name,
                parameters=cmd_params)
        run_cmd_async_operation.wait()
        run_cmd = run_cmd_async_operation.result().as_dict()
        self.logger.info(
            'Run command result: {0}'.format(
                utils.secure_logging_content(run_cmd))
            )
        self.logger.debug(
            'Finished running command on virtual_machine {0}'.format(vm_name))
