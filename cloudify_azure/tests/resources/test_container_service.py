# Copyright (c) 2015-2020 Cloudify Platform Ltd. All rights reserved
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
import mock
import unittest
import requests

from msrestazure.azure_exceptions import CloudError

from cloudify import mocks as cfy_mocks

from cloudify_azure.resources.compute import container_service
from cloudify_azure.utils import handle_resource_config_params


@mock.patch('azure_sdk.common.ClientSecretCredential')
@mock.patch('azure_sdk.resources.compute.'
            'container_service.ContainerServiceClient')
class ContainerServiceTest(unittest.TestCase):

    def _get_mock_context_for_run(self):
        operation = {'name': 'cloudify.interfaces.lifecycle.create'}
        fake_ctx = cfy_mocks.MockCloudifyContext(operation=operation)
        instance = mock.Mock()
        instance.runtime_properties = {}
        fake_ctx._instance = instance
        node = mock.Mock()
        fake_ctx._node = node
        node.properties = {}
        node.runtime_properties = {}
        node.type_hierarchy = ['ctx.nodes.Root']
        fake_ctx.get_resource = mock.MagicMock(
            return_value=""
        )
        return fake_ctx, node, instance

    def setUp(self):
        self.fake_ctx, self.node, self.instance = \
            self._get_mock_context_for_run()
        self.dummy_azure_credentials = {
            'client_id': 'dummy',
            'client_secret': 'dummy',
            'subscription_id': 'dummy',
            'tenant_id': 'dummy'
        }

    def test_create(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'cs_name'
        container_service_config = {
            'network_profile': None,
            'addon_profiles': None,
            'kubernetes_version': None,
            'dns_prefix': 'dummy-dns',
            'linux_profile': None,
            'agent_pool_profiles': None,
            'service_principal_profile': None,
            'location': 'westus',
            'enable_rbac': True,
            'tags': None
        }
        service_payload = {}
        service_payload = \
            handle_resource_config_params(service_payload,
                                          container_service_config)
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().container_services.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            container_service.create(self.fake_ctx, resource_group, name,
                                     container_service_config)
            client().container_services.get.assert_called_with(
                resource_group_name=resource_group,
                container_service_name=name
            )
            client().container_services.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                container_service_name=name,
                parameters=service_payload
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get("name"),
                name
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get(
                    "resource_group"),
                resource_group
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'cs_name'
        container_service_config = {
            'network_profile': None,
            'addon_profiles': None,
            'kubernetes_version': None,
            'dns_prefix': 'dummy-dns',
            'linux_profile': None,
            'agent_pool_profiles': None,
            'service_principal_profile': None,
            'location': 'westus',
            'enable_rbac': True,
            'tags': None
        }
        client().container_services.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            container_service.create(self.fake_ctx, resource_group, name,
                                     container_service_config)
            client().container_services.get.assert_called_with(
                resource_group_name=resource_group,
                container_service_name=name
            )
            client().container_services.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'cs_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            container_service.delete(self.fake_ctx)
            client().container_services.delete.assert_called_with(
                resource_group_name=resource_group,
                container_service_name=name
            )

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'cs_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().container_services.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            container_service.delete(self.fake_ctx)
            client().container_services.delete.assert_not_called()
