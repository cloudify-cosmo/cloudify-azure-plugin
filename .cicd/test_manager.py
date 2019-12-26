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
from integration_tests.tests import utils as test_utils

PLUGIN_NAME = 'cloudify-azure-plugin'


class AzurePluginTestCase(PluginsTest):

    base_path = os.path.dirname(os.path.realpath(__file__))

    @property
    def plugin_root_directory(self):
        return os.path.abspath(os.path.join(self.base_path, '..'))

    @property
    def inputs(self):
        return {
            'subscription_id': os.getenv('azure_subscription_id'),
            'tenant_id': os.getenv('azure_tenant_id'),
            'client_id': os.getenv('azure_client_id'),
            'client_secret': os.getenv('azure_client_secret'),
            'agent_key_private': '',
            'agent_key_public': os.getenv('agent_key_public'),
            'location': os.getenv('azure_location'),
            'resource_prefix': os.getenv('CIRCLE_JOB', 'cfy'),
            'resource_suffix': os.getenv(
                'CIRCLE_BUILD_NUM', str(random())[-4:-1])
        }

    @property
    def wagon_build_time_limit(self):
        return 1800

    def check_main_blueprint(self):
        blueprint_id = 'azure_blueprint'
        self.addCleanup(self.undeploy_application, blueprint_id)
        dep, ex_id = self.deploy_application(
            test_utils.get_resource(
                os.path.join(
                    self.plugin_root_directory,
                    'examples/vm.yaml')),
            timeout_seconds=400,
            blueprint_id=blueprint_id,
            deployment_id=blueprint_id,
            inputs=self.inputs)
        self.undeploy_application(dep.id, timeout_seconds=400)

    def test_blueprints(self):
        self.upload_mock_plugin(PLUGIN_NAME, self.plugin_root_directory)
        self.check_main_blueprint()
