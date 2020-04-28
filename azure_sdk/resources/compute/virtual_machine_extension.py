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

from azure.mgmt.compute import ComputeManagementClient

from cloudify_azure import (constants, utils)
from azure_sdk.common import AzureResource


class VirtualMachineExtension(AzureResource):

    def __init__(self, azure_config, logger,
                 api_version=constants.API_VER_COMPUTE):
        super(VirtualMachineExtension, self).__init__(azure_config)
        self.logger = logger
        self.client = \
            ComputeManagementClient(self.credentials, self.subscription_id,
                                    api_version=api_version)

    def get(self, group_name, vm_name, vm_extension_name):
        self.logger.info("Get vm_extension...{0}".format(vm_extension_name))
        virtual_machine_extension = self.client.virtual_machine_extensions.get(
            resource_group_name=group_name,
            vm_name=vm_name,
            vm_extension_name=vm_extension_name
        )
        self.logger.info(
            'Get virtual_machine_extension result: {0}'.format(
                utils.secure_logging_content(
                    virtual_machine_extension.as_dict())
                )
            )
        return virtual_machine_extension.as_dict()

    def create_or_update(self, group_name, vm_name, vm_extension_name, params):
        self.logger.info("Create/Updating vm_extension...{0}".format(
            vm_extension_name))
        create_async_operation = \
            self.client.virtual_machine_extensions.create_or_update(
                resource_group_name=group_name,
                vm_name=vm_name,
                vm_extension_name=vm_extension_name,
                extension_parameters=params,
            )
        create_async_operation.wait()
        virtual_machine_extension = create_async_operation.result()
        self.logger.info(
            'Create virtual_machine_extension result: {0}'.format(
                utils.secure_logging_content(
                    virtual_machine_extension.as_dict())
                )
            )
        return virtual_machine_extension.as_dict()

    def delete(self, group_name, vm_name, vm_extension_name):
        self.logger.info("Deleting vm_extension...{0}".format(
            vm_extension_name))
        delete_async_operation = self.client.virtual_machine_extensions.delete(
            resource_group_name=group_name,
            vm_name=vm_name,
            vm_extension_name=vm_extension_name
        )
        delete_async_operation.wait()
        self.logger.debug(
            'Deleted virtual_machine_extension {0}'.format(vm_extension_name))
