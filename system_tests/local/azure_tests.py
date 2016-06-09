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

IGNORED_LOCAL_WORKFLOW_MODULES = (
    'worker_installer.tasks',
    'plugin_installer.tasks',
    'cloudify_agent.operations',
    'cloudify_agent.installer.operations',
)


class AzureSystemTests(TestCase):

    def _set_up(self,
                inputs=None,
                directory='manager/resources',
                filename='local-blueprint.yaml'):

        blueprint_path = os.path.join(
            os.path.dirname(
                os.path.dirname(__file__)), directory, filename)

        if not inputs:
            inputs = self.clean_inputs

        # setup local workflow execution environment
        self.localenv = local.init_env(
            blueprint_path,
            name=self.test_id,
            inputs=inputs,
            ignored_modules=IGNORED_LOCAL_WORKFLOW_MODULES)

    def setUp(self):
        super(AzureSystemTests, self).setUp()
        self._set_up()

    def tearDown(self):
        super(AzureSystemTests, self).tearDown()

    @property
    def clean_inputs(self):
        return {
            'subscription_id': self.env.subscription_id,
            'tenant_id': self.env.tenant_id,
            'client_id': self.env.client_id,
            'client_secret': self.env.client_secret,
            'resource_prefix': self.short_test_id,
            'location': self.env.location,
            'retry_after': self.env.retry_after,
            'standard_a2_size': self.env.standard_a2_size,
            'os_family_linux': self.env.os_family_linux,
            'image_publisher_ubuntu_trusty':
                self.env.image_publisher_ubuntu_trusty,
            'image_offer_ubuntu_trusty': self.env.image_offer_ubuntu_trusty,
            'image_sku_ubuntu_trusty': self.env.image_sku_ubuntu_trusty,
            'image_version_ubuntu_trusty':
                self.env.image_version_ubuntu_trusty,
            'username_ubuntu_trusty': self.env.username_ubuntu_trusty,
            'password': self.env.password,
            'authorized_keys_ubuntu': self.env.authorized_keys_ubuntu,
            'image_publisher_centos_final':
                self.env.image_publisher_centos_final,
            'image_offer_centos_final': self.env.image_offer_centos_final,
            'image_sku_centos_final': self.env.image_sku_centos_final,
            'image_version_centos_final': self.env.image_version_centos_final,
            'username_centos_final': self.env.username_centos_final,
            'authorized_keys_centos': self.env.authorized_keys_centos,
            'os_family_windows': self.env.os_family_windows,
            'image_publisher_windows': self.env.image_publisher_windows,
            'image_offer_windows': self.env.image_offer_windows,
            'image_sku_windows': self.env.image_sku_windows,
            'image_version_windows': self.env.image_version_windows,
            'username_windows': self.env.username_windows,
            'keydata': self.env.keydata
        }

    def post_install_assertions(self):
        self.assertEquals(len(self.resources_in_group()), 21)

    def post_uninstall_assertions(self):

        try:
            output = self.resource_group.properties.provisioning_state
        except AttributeError:
            output = '*'

        self.assertNotIn(output, 'Succeeded')

    def test_local(self):

        self.localenv.execute('install', task_retries=40)
        self.post_install_assertions()
        self.localenv.execute('uninstall', task_retries=40)
        self.post_uninstall_assertions()

    @property
    def azure_client(self):

        from azure.common.credentials import \
            ServicePrincipalCredentials

        from azure.mgmt.resource.resources import (
            ResourceManagementClient,
            ResourceManagementClientConfiguration
        )

        return ResourceManagementClient(
            ResourceManagementClientConfiguration(
                ServicePrincipalCredentials(
                    client_id=self.env.client_id,
                    secret=self.env.client_secret,
                    tenant=self.env.tenant_id
                ),
                self.env.subscription_id
            )
        )

    @property
    def resource_group(self):

        from azure.common.exceptions import CloudError

        try:
            return self.azure_client.resource_groups.get(
                '{0}{1}'.format(
                    self.short_test_id,
                    'rg'
                )
            )
        except CloudError:
            return None

    @property
    def short_test_id(self):
        bad_chars = [
            '`', '~', '!', '@', '#', '$', '%', '^', '&', '*',
            '(', ')', '=', '+', '_', '[', ']', '{', '}', '\\',
            '|', ';', ':', '.', '\'', ',', '<', '>', '/', '?', '-']
        id = self.test_id.translate(None, ''.join(bad_chars))
        id = id.replace('2016', '')
        id = id.replace('test', '')
        id = id.replace('local', '')
        return id.replace('system', '')

    def resources_in_group(self):
        return [r for r in
                self.azure_client.resources.list(
                    filter="location eq '{0}'".format(
                        self.env.location)
                ) if self.resource_group.name in r.id]
