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
from time import sleep
from random import random

from integration_tests.tests import utils as test_utils
from integration_tests.tests.test_cases import PluginsTest

PLUGIN_NAME = 'cloudify-azure-plugin'
DEVELOPMENT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(
        os.path.realpath(__file__)), '../..'))


class AzurePluginTestCase(PluginsTest):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def plugin_root_directory(self):
        return os.path.abspath(os.path.join(self.base_path, '..'))

    @property
    def inputs(self):
        return {
            'location': os.getenv('azure_location'),
            'resource_prefix': os.getenv('CIRCLE_JOB', 'cfy'),
            'resource_suffix': os.getenv(
                'CIRCLE_BUILD_NUM', str(random())[-4:-1])
        }

    def create_secrets(self):
        secrets = {
            'azure_subscription_id': os.getenv('azure_subscription_id'),
            'azure_tenant_id': os.getenv('azure_tenant_id'),
            'azure_client_id': os.getenv('azure_client_id'),
            'azure_client_secret': os.getenv('azure_client_secret'),
            'agent_key_private': os.getenv('agent_key_private'),
            'agent_key_public': os.getenv('agent_key_public'),
        }
        self._create_secrets(secrets)

    @property
    def wagon_build_time_limit(self):
        return 1800

    def check_main_blueprint(self):
        blueprint_path = os.path.join(
            self.examples.git_location,
            'hello-world-example', 'azure.yaml')
        blueprint_id = 'hello-world-azure'
        self.addCleanup(self.undeploy_application, blueprint_id)
        dep, ex_id = self.deploy_application(
            test_utils.get_resource(blueprint_path),
            timeout_seconds=600,
            blueprint_id=blueprint_id,
            deployment_id=blueprint_id,
            inputs=self.inputs)
        self.undeploy_application(dep.id, timeout_seconds=600)

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
        self.check_main_blueprint()
