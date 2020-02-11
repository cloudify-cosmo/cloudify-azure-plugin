# #######
# Copyright (c) 2019 Cloudify Platform Ltd. All rights reserved
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

import os
from random import random

from integration_tests.tests.test_cases import PluginsTest

PLUGIN_NAME = 'cloudify-azure-plugin'
DEVELOPMENT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '../..'))
TEST_KEY_PATH = '/tmp/foo.rsa'
TEST_PUB_PATH = '/tmp/foo.rsa.pub'


class AzurePluginTestCase(PluginsTest):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def plugin_root_directory(self):
        return os.path.abspath(os.path.join(self.base_path, '..'))

    @property
    def inputs(self):
        return {
            'location': os.getenv('azure_location', 'westeurope'),
            'resource_prefix': os.getenv('CIRCLE_JOB', 'cfy'),
            'resource_suffix': os.getenv(
                'CIRCLE_BUILD_NUM', str(random())[-4:-1])
        }

    def create_secrets(self):
        secrets = {
            'agent_key_private': os.getenv('agent_key_private',
                                           open(TEST_KEY_PATH).read()),
            'agent_key_public': os.getenv('agent_key_public',
                                          open(TEST_PUB_PATH).read()),
            'azure_subscription_id': os.getenv('azure_subscription_id'),
            'azure_tenant_id': os.getenv('azure_tenant_id'),
            'azure_client_id': os.getenv('azure_client_id'),
            'azure_client_secret': os.getenv('azure_client_secret'),
            'azure_location': os.getenv('azure_location', 'westeurope'),
        }
        self._create_secrets(secrets)

    @property
    def wagon_build_time_limit(self):
        return 1800

    def upload_plugins(self):
        self.upload_mock_plugin(
            PLUGIN_NAME, self.plugin_root_directory)
        self.upload_mock_plugin(
            'cloudify-utilities-plugin',
            os.path.join(DEVELOPMENT_ROOT, 'cloudify-utilities-plugin'))
        self.upload_mock_plugin(
            'cloudify-ansible-plugin',
            os.path.join(DEVELOPMENT_ROOT, 'cloudify-ansible-plugin'))

    def test_blueprints(self):
        self.upload_plugins()
        self.create_secrets()
        self.check_hello_world_blueprint(
            'azure', self.inputs, self.wagon_build_time_limit)
        self.check_db_lb_app_blueprint('azure', self.wagon_build_time_limit)
