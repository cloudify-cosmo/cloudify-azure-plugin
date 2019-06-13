# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import unittest
import mock
from cloudify import mocks as cfy_mocks
from mock import patch
from cloudify_azure.resources.compute import container_service


class AzureSDKResourceTest(unittest.TestCase):
    def setUp(self):
        self.fake_ctx, self.node, self.instance = \
            self._get_mock_context_for_run()
        self.dummy_azure_credentials = {
            'client_id': 'dummy',
            'client_secret': 'dummy',
            'subscription_id': 'dummy',
            'tenant_id': 'dummy'
        }

    def _get_mock_context_for_run(self):
        fake_ctx = cfy_mocks.MockCloudifyContext()
        instance = mock.Mock()
        instance.runtime_properties = {}
        fake_ctx._instance = instance
        node = mock.Mock()
        fake_ctx._node = node
        node.properties = {}
        node.runtime_properties = {}
        fake_ctx.get_resource = mock.MagicMock(
            return_value=""
        )
        return fake_ctx, node, instance


@patch('cloudify_azure.auth.oauth2.CustomServicePrincipalCredentials')
@patch('cloudify_azure.resources.compute.'
       'container_service.ContainerServiceClient')
class ContainerServiceTest(AzureSDKResourceTest):
    def test_create(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        container_service_config = {
            'key': 'value'
        }
        container_service.create(self.fake_ctx, 'sample_resource_group',
                                 'cs_name', container_service_config)
        client().container_services.create_or_update.create_or_update(
            resource_group_name='sample_resource_group',
            container_service_name='cs_name',
            parameters=container_service_config)

    def test_delete(self, client, credentials):
        self.node.properties['azure_config'] = {
            'client_id': 'dummy',
            'client_secret': 'dummy',
            'subscription_id': 'dummy',
            'tenant_id': 'dummy'
        }
        self.instance.runtime_properties['resource_group'] = \
            'sample_resource_group'
        self.instance.runtime_properties['name'] = 'cs_name'
        container_service.delete(self.fake_ctx)
        client().container_services.delete.assert_called_with(
            resource_group_name='sample_resource_group',
            container_service_name='cs_name')
