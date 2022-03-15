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

from cloudify.state import current_ctx
from msrestazure.azure_exceptions import CloudError

from cloudify import mocks as cfy_mocks

from cloudify_azure.resources import resourcegroup


@mock.patch('azure_sdk.common.ClientSecretCredential')
@mock.patch('azure_sdk.resources.resource_group.ResourceManagementClient')
class ResourceGroupTest(unittest.TestCase):

    def _get_mock_context_for_run(self, operation=None):
        operation = operation or {
            'name': 'cloudify.interfaces.lifecycle.create'
        }
        node_props = {
            'resource_id': '',
            'use_external_resource': False,
            'create_if_missing': False,
            'use_if_exists': False,
            'modify_external_resource': False,
        }
        fake_ctx = cfy_mocks.MockCloudifyContext(
            properties=node_props,
            operation=operation,
        )
        instance = mock.Mock()
        instance.runtime_properties = {}
        fake_ctx._instance = instance
        node = mock.Mock(properties=node_props)
        node.properties = node_props
        fake_ctx._node = node
        node.runtime_properties = {}
        node.type_hierarchy = ['ctx.nodes.Root',
                               'cloudify.azure.nodes.ResourceGroup']
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
        self.node.properties['name'] = resource_group
        self.node.properties['location'] = 'westus'
        self.node.properties['tags'] = {
            'mode': 'testing'
        }
        resource_group_params = {
            'location': self.node.properties.get('location'),
            'tags': self.node.properties.get('tags')
        }
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().resource_groups.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            resourcegroup.create(ctx=self.fake_ctx)
            client().resource_groups.get.assert_called_with(
                resource_group_name=resource_group
            )
            client().resource_groups.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                parameters=resource_group_params
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get("name"),
                resource_group
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        self.node.properties['use_external_resource'] = True
        self.fake_ctx.node.properties['use_external_resource'] = True
        self.node.properties['name'] = 'sample_resource_group'
        self.fake_ctx.node.properties['name'] = 'sample_resource_group'
        self.node.properties['location'] = 'westus'
        self.fake_ctx.node.properties['location'] = 'westus'
        self.node.properties['tags'] = {
            'mode': 'testing'
        }
        self.fake_ctx.node.properties['tags'] = {
            'mode': 'testing'
        }
        client().resource_groups.get.return_value = mock.Mock()
        with mock.patch(
                'cloudify_azure.utils.secure_logging_content',
                mock.Mock()):
            resourcegroup.create(ctx=self.fake_ctx)
            client().resource_groups.get.assert_called_with(
                resource_group_name=resource_group
            )
            # client().resource_groups.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.delete'})
        resource_group = 'sample_resource_group'
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        fake_ctx.instance.runtime_properties['name'] = resource_group
        current_ctx.set(ctx=fake_ctx)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            resourcegroup.delete(ctx=fake_ctx)
            client().resource_groups.begin_delete.assert_called_with(
                resource_group_name=resource_group)

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        self.instance.runtime_properties['name'] = resource_group
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().resource_groups.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            resourcegroup.delete(ctx=self.fake_ctx)
            client().resource_groups.begin_delete.assert_not_called()
