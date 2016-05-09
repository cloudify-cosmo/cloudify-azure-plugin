########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import os
from cosmo_tester.framework.testenv import TestCase

from cloudify.workflows import local


class AzureSystemTests(TestCase):

    @property
    def ignored_local_workflow_modules(self):
        return (
            'worker_installer.tasks',
            'plugin_installer.tasks',
            'cloudify_agent.operations',
            'cloudify_agent.installer.operations',
        )

    @property
    def blueprint_path(self):
        return os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)
            ), 'manager/resources', 'local-blueprint.yaml')

    @property
    def clean_inputs(self):
        return {
            'subscription_id': self.env.subscription_id,
            'tenant_id': self.env.tenant_id,
            'client_id': self.env.client_id,
            'client_secret': self.env.client_secret,
            'location': self.env.location,
            'retry_after': self.env.retry_after,
            'subnet_private_cidr': self.env.subnet_private_cidr,
            'public_keys': self.env.agent_public_key,
            'public_key_auth_only': self.env.public_key_auth_only,
            'size': self.env.standard_a2_size,
            'linux_os_family': self.env.linux_os_family,
            'ubuntu_image_publisher': self.env.canonical_image_publisher,
            'ubuntu_image_offer': self.env.ubuntu_server_14_04_image_offer,
            'ubuntu_image_sku': self.env.ubuntu_server_14_04_image_sku,
            'ubuntu_image_version': self.env.ubuntu_server_14_04_image_version,
            'ubuntu_agent_user': self.env.ubuntu_server_ubuntu_user,
            'ubuntu_os_password': self.env.ubuntu_server_ubuntu_user_password,
            'ubuntu_public_key_path': self.env.ubuntu_public_key_path,
            'centos_image_publisher': self.env.openlogic_image_publisher,
            'centos_image_offer': self.env.centos_image_offer,
            'centos_image_sku': self.env.centos_7_0_image_sku,
            'centos_image_version': self.env.centos_image_version,
            'centos_agent_user': self.env.centos_user,
            'centos_os_password': self.env.centos_user_password,
            'centos_public_key_path': self.env.centos_public_key_path,
            'windows_os_family': self.env.windows_os_family,
            'windows_image_publisher': self.env.microsoft_image_publisher,
            'windows_image_offer': self.env.microsoft_2012_image_offer,
            'windows_image_sku': self.env.microsoft_2012_image_sku,
            'windows_image_version': self.env.microsoft_2012_image_version,
            'windows_agent_user': self.env.microsoft_2012_user,
            'windows_os_password': self.env.microsoft_2012_user_password,
            'webserver_port': self.env.demo_webserver_port
        }

    def install_workflow(self, test_name):

        cfy_local = local.init_env(
            self.blueprint_path,
            name=test_name,
            inputs=self.clean_inputs,
            ignored_modules=self.ignored_local_workflow_modules)

        cfy_local.execute('install', task_retries=10)

        return cfy_local

    def uninstall_workflow(self, cfy_local):
        cfy_local.execute('uninstall', task_retries=10)

    def infrastructure_assertions(self):
        pass

    def application_assertions(self):
        pass

    def post_install_assertions(self):
        self.infrastructure_assertions()
        self.application_assertions()

    def post_uninstall_assertions(self):
        pass

    def test_local(self):

        cfy = self.install_workflow('test_local')
        self.post_install_assertions()
        self.uninstall_workflow(cfy)
        self.post_uninstall_assertions()

