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

from cloudify.state import current_ctx
from cloudify import mocks as cfy_mocks

from . import compose_not_found_cloud_error
from cloudify_azure.resources.network import virtualnetwork


@mock.patch('azure_sdk.common.ClientSecretCredential')
@mock.patch('azure_sdk.resources.network.virtual_network.'
            'NetworkManagementClient')
class VirtualNetworkTest(unittest.TestCase):

    def _get_mock_context_for_run(self, operation=None):
        operation = operation or {
            'name': 'cloudify.interfaces.lifecycle.create'}
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
        current_ctx.set(self.fake_ctx)

    def test_create(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        vnet_name = 'sample_vnet'
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = vnet_name
        self.node.properties['location'] = 'westus'
        self.node.properties['tags'] = {
            'mode': 'testing'
        }
        vnet_params = {
            'location': self.node.properties.get('location'),
            'tags': self.node.properties.get('tags')
        }
        err = compose_not_found_cloud_error()
        client().virtual_networks.get.side_effect = err
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualnetwork.create(ctx=self.fake_ctx)
            client().virtual_networks.get.assert_called_with(
                resource_group_name=resource_group,
                virtual_network_name=vnet_name
            )
            client()\
                .virtual_networks.begin_create_or_update.assert_called_with(
                resource_group_name=resource_group,
                virtual_network_name=vnet_name,
                parameters=vnet_params
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get("name"),
                vnet_name
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get(
                    "resource_group"),
                resource_group
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        vnet_name = 'sample_vnet'
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = vnet_name
        self.node.properties['use_external_resource'] = True
        self.node.properties['location'] = 'westus'
        self.node.properties['tags'] = {
            'mode': 'testing'
        }
        client().virtual_networks.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualnetwork.create(ctx=self.fake_ctx)
            client().virtual_networks.get.assert_called_with(
                resource_group_name=resource_group,
                virtual_network_name=vnet_name
            )
            # client().virtual_networks.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        resource_group = 'sample_resource_group'
        vnet_name = 'sample_vnet'
        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.delete'})
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = vnet_name
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        current_ctx.set(fake_ctx)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualnetwork.delete(ctx=fake_ctx)
            client().virtual_networks.begin_delete.assert_called_with(
                resource_group_name=resource_group,
                virtual_network_name=vnet_name
            )

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        vnet_name = 'sample_vnet'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = vnet_name
        err = compose_not_found_cloud_error()
        client().virtual_networks.get.side_effect = err
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualnetwork.delete(ctx=self.fake_ctx)
            client().virtual_networks.begin_delete.assert_not_called()
