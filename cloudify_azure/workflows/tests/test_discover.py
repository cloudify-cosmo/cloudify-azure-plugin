from unittest import TestCase
from mock import patch, call, MagicMock

from .. import resources, discover
from ..._compat import PY2


@patch('azure_sdk.common.ClientSecretCredential')
@patch('azure.mgmt.containerservice.ContainerServiceClient')
class AzureWorkflowTests(TestCase):

    def get_mock_rest_client(self):
        self.dummy_azure_credentials = {
            'client_id': 'dummy',
            'client_secret': 'dummy',
            'subscription_id': 'dummy',
            'tenant_id': 'dummy',
            'endpoint_verify': False
        }
        mock_node = MagicMock(node_id='foo',
                              type_hierarchy=discover.AZURE_TYPE)
        mock_node.id = mock_node.node_id
        mock_node.properties = {
            'client_config': self.dummy_azure_credentials,
            'resource_config': {},
            'locations': []
        }
        nodes_list = [mock_node]
        mock_nodes_client = MagicMock()
        mock_nodes_client.list = MagicMock(return_value=nodes_list)
        mock_instance = MagicMock(node_id='foo', state='started')
        mock_instance.node = mock_node
        mock_instance.node_id = mock_node.node_id
        mock_instance.runtime_properties = {}
        instances_list = [mock_instance]
        mock_instances_client = MagicMock()
        mock_instances_client.list = MagicMock(return_value=instances_list)
        mock_deployments_client = MagicMock()
        mock_deployments_client.create = MagicMock()
        mock_deployments_client.get.return_value = None
        mock_deployment_groups_client = MagicMock()
        mock_deployment_groups_client.put = MagicMock()
        mock_rest_client = MagicMock()
        mock_rest_client.nodes = mock_nodes_client
        mock_rest_client.node_instances = mock_instances_client
        mock_rest_client.deployments = mock_deployments_client
        mock_rest_client.deployment_groups = mock_deployment_groups_client
        return mock_rest_client

    @patch('cloudify_azure.workflows.discover.get_resources')
    def test_discover_resources(self, mock_get_resources, *_, **__):
        mock_ctx = MagicMock()
        node = MagicMock()
        node_instance = MagicMock()
        node_instance._node_instance = MagicMock(
            runtime_properties={'resources': {}})
        result = {'foo': 'bar'}
        mock_get_resources.return_value = result
        node_instances = [node_instance]
        node.instances = node_instances
        mock_ctx.get_node.return_value = node
        params = {
            'node_id': 'foo',
            'resource_types': ['bar', 'baz'],
            'locations': ['taco'],
            'ctx': mock_ctx
        }
        self.assertEqual(discover.discover_resources(**params), result)

    @patch('cloudify_common_sdk.utils.get_rest_client')
    def test_deploy_resources(self, get_rest_client, *_, **__):
        mock_rest_client = self.get_mock_rest_client()
        get_rest_client.return_value = mock_rest_client
        mock_ctx = MagicMock()
        params = {
            'group_id': 'foo',
            'blueprint_id': 'bar',
            'deployment_ids': ['taco'],
            'inputs': [{'winter': 'not fun'}],
            'labels': [{'beach': 'fun'}],
            'ctx': mock_ctx
        }
        discover.deploy_resources(**params)
        self.assertTrue(
            mock_rest_client.deployment_groups.put.called)
        self.assertTrue(
            mock_rest_client.deployment_groups.add_deployments.called)

    @patch('cloudify_common_sdk.utils.get_rest_client')
    @patch('cloudify_azure.workflows.discover.deploy_resources')
    @patch('cloudify_azure.workflows.discover.discover_resources')
    def test_discover_and_deploy(self, mock_discover, mock_deploy, *_, **__):
        mock_ctx = MagicMock()
        mock_ctx.deployment = MagicMock(id='foo')
        mock_ctx.blueprint = MagicMock(id='bar')
        params = {
            'node_id': 'foo',
            'resource_types': ['bar', 'baz'],
            'locations': ['taco'],
            'blueprint_id': 'foo',
            'ctx': mock_ctx
        }
        mock_discover.return_value = {
            'region1': {
                'resource_type1': {
                    'foo/bar/baz/taco/cheez/resource1': MagicMock(),
                    'foo/bar/baz/taco/cheez/resource2': MagicMock(),
                },
                'resource_type2': {
                    'foo/bar/baz/taco/cheez/resource3': MagicMock()
                },
            },
            'region2': {
                'resource_type1': {
                    'foo/bar/baz/taco/cheez/resource4': MagicMock()
                }
            }
        }
        discover.discover_and_deploy(**params)
        self.assertEqual(mock_deploy.call_count, 3)
        expected_calls = [
            call('foo', 'foo', ['foo-resource1', 'foo-resource2'],
                 [
                     {'resource_group_name': 'bar',
                      'managed_cluster_name': 'resource1'},
                     {'resource_group_name': 'bar',
                      'managed_cluster_name': 'resource2'}],
                 [
                     {'csys-env-type': 'environment'},
                     {'csys-obj-parent': 'foo'}], mock_ctx),
            call('foo', 'foo', ['foo-resource3'],
                 [
                     {'resource_group_name': 'bar',
                      'managed_cluster_name': 'resource3'}],
                 [{'csys-env-type': 'environment'},
                  {'csys-obj-parent': 'foo'}], mock_ctx),
            call('foo', 'foo', ['foo-resource4'],
                 [{
                     'resource_group_name': 'bar',
                     'managed_cluster_name': 'resource4'}],
                 [{'csys-env-type': 'environment'},
                  {'csys-obj-parent': 'foo'}], mock_ctx)]
        if PY2:
            return
        mock_deploy.assert_has_calls(expected_calls)

    @patch('azure_sdk.resources.compute.managed_cluster.ManagedCluster.list')
    def test_get_resources(self, cluster_list, *_, **__):
        mock_ctx = MagicMock()
        node = MagicMock()
        node_instance = MagicMock()
        node_instance._node_instance = MagicMock(
            runtime_properties={'resources': {}})
        node_instances = [node_instance]
        node.instances = node_instances
        mock_ctx.get_node.return_value = node
        mock_ctx.logger = MagicMock()
        params = {
            'node': node,
            'locations': ['region1', 'region2'],
            'resource_types': ['Microsoft.ContainerService/'
                               'ManagedClusters'],
            'logger': mock_ctx.logger
        }
        expected = {'region1': {'Microsoft.ContainerService/'
                                'ManagedClusters': {'foo': {'foo': 'bar'}}},
                    'region2': {'Microsoft.ContainerService/'
                                'ManagedClusters': {'foo': {'foo': 'bar'}}}}
        resource_1 = MagicMock(id='foo', location='region1')
        resource_1.as_dict.return_value = {'foo': 'bar'}
        resource_2 = MagicMock(id='foo', location='region2')
        resource_2.as_dict.return_value = {'foo': 'bar'}
        cluster_list.return_value = [resource_1, resource_2]
        print
        self.assertEqual(resources.get_resources(**params), expected)

    @patch('azure_sdk.resources.compute.managed_cluster.ManagedCluster.list')
    def test_initialize(self, *_, **__):
        mock_ctx = MagicMock()
        mock_ctx.instance = MagicMock(runtime_properties={'resources': {}})
        params = {
            'resource_config': {'resource_types': [
                'Microsoft.ContainerService/ManagedClusters']},
            'locations': ['region1', 'region2'],
            'ctx': mock_ctx,
            'logger': mock_ctx.logger
        }
        resources.initialize(**params)
        self.assertIn('resources',
                      mock_ctx.instance.runtime_properties)
