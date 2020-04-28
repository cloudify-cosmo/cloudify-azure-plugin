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

from cloudify_azure.resources.compute import managed_cluster
from cloudify_azure.utils import handle_resource_config_params


@mock.patch('azure_sdk.common.ServicePrincipalCredentials')
@mock.patch('azure_sdk.resources.compute.'
            'managed_cluster.ContainerServiceClient')
class ManagedClusterTest(unittest.TestCase):

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
        cluster_name = 'mc_name'
        self.node.properties['store_kube_config_in_runtime'] = False
        managed_cluster_config = {
            'network_profile': None,
            'addon_profiles': None,
            'windows_profile': None,
            'dns_prefix': 'dummy-dns',
            'linux_profile': None,
            'agent_pool_profiles': None,
            'service_principal_profile': None,
            'location': 'westus',
            'enable_rbac': True,
            'kubernetes_version': None,
            'tags': None
        }
        cluster_payload = {}
        cluster_payload = \
            handle_resource_config_params(cluster_payload,
                                          managed_cluster_config)
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().managed_clusters.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            managed_cluster.create(self.fake_ctx, resource_group,
                                   cluster_name, managed_cluster_config)
            client().managed_clusters.get.assert_called_with(
                resource_group_name=resource_group,
                resource_name=cluster_name,
            )
            client().managed_clusters.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                resource_name=cluster_name,
                parameters=cluster_payload
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get("name"),
                cluster_name
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get(
                    "resource_group"),
                resource_group
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        cluster_name = 'mc_name'
        self.node.properties['store_kube_config_in_runtime'] = False
        managed_cluster_config = {
            'network_profile': None,
            'addon_profiles': None,
            'windows_profile': None,
            'dns_prefix': 'dummy-dns',
            'linux_profile': None,
            'agent_pool_profiles': None,
            'service_principal_profile': None,
            'location': 'westus',
            'enable_rbac': True,
            'kubernetes_version': None,
            'tags': None
        }
        client().managed_clusters.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            managed_cluster.create(self.fake_ctx, resource_group,
                                   cluster_name, managed_cluster_config)
            client().managed_clusters.get.assert_called_with(
                resource_group_name=resource_group,
                resource_name=cluster_name,
            )
            client().managed_clusters.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        cluster_name = 'mc_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = cluster_name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            managed_cluster.delete(self.fake_ctx)
            client().managed_clusters.delete.assert_called_with(
                resource_group_name=resource_group,
                resource_name=cluster_name
            )

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        cluster_name = 'mc_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = cluster_name
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().managed_clusters.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            managed_cluster.delete(self.fake_ctx)
            client().managed_clusters.delete.assert_not_called()
