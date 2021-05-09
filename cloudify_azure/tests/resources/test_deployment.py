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
import json
import mock
import tempfile
import unittest

from azure.mgmt.resource.resources.models import DeploymentMode
from azure.mgmt.resource.resources.v2019_10_01.models import \
    DeploymentProperties, DeploymentWhatIfProperties

from azure.mgmt.resource.resources.v2019_10_01.models import \
    Deployment as AzDeployment

from cloudify import mocks as cfy_mocks
from cloudify import exceptions as cfy_exc
from cloudify.state import current_ctx


from . import compose_not_found_cloud_error
from cloudify_azure.resources import deployment
from cloudify_azure.resources.deployment import STATE, IS_DRIFTED

TEST_TEMPLATE = {
            '$schema': 'http://schema.management.azure.com/Template.json',
            'contentVersion': '1.0.0.0',
            'parameters': {
                'storageEndpoint': {
                  'type': 'string',
                  'defaultValue': 'core.windows.net',
                  'metadata': {
                    'description': 'Storage Endpoint.'
                  }
                },
            }
        }

RESOURCES_LIST = [
                    {
                        "id": "/fake/resource/id/1"
                    },
                    {
                        "id": "/fake/resource/id/2"
                    },
                ]
RUNTIME_PROPERTIES_AFTER_CREATE = {
    'resource': {
        'properties':
            {
                "output_resources": RESOURCES_LIST
            }
    },
    'template': TEST_TEMPLATE}

TEST_RESOURCE_GROUP_NAME = 'sample_deployment'


@mock.patch('azure_sdk.common.ServicePrincipalCredentials')
@mock.patch('azure_sdk.resources.deployment.ResourceManagementClient')
@mock.patch('azure_sdk.resources.resource_group.ResourceManagementClient')
class DeploymentTest(unittest.TestCase):

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
        node.type_hierarchy = ['ctx.nodes.Root', 'cloudify.azure.Deployment']
        fake_ctx.get_resource = mock.MagicMock(
            return_value=""
        )
        return fake_ctx, node, instance

    def setUp(self):
        self.fake_ctx, self.node, self.instance = \
            self._get_mock_context_for_run()
        current_ctx.set(self.fake_ctx)

        self.dummy_azure_credentials = {
            'client_id': 'dummy',
            'client_secret': 'dummy',
            'subscription_id': 'dummy',
            'tenant_id': 'dummy'
        }

    def test_create(self, rg_client, deployment_client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['template'] = TEST_TEMPLATE
        self.node.properties['location'] = 'westus'
        resource_group_params = {
            'location': self.node.properties.get('location'),
        }
        properties = self.node.properties
        template = deployment.get_template(self.fake_ctx, properties)
        deployment_params = {
            'mode': DeploymentMode.incremental,
            'template': template,
            'parameters': deployment.format_params(properties.get(
                'params', {}))
        }
        deployment_properties = DeploymentProperties(
            mode=deployment_params['mode'],
            template=deployment_params['template'],
            parameters=deployment_params['parameters'])

        err = compose_not_found_cloud_error()
        rg_client().resource_groups.get.side_effect = err
        deployment_client().deployments.get.side_effect = err
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(ctx=self.fake_ctx)
            deployment_client().deployments.get.assert_called_with(
                resource_group_name=resource_group,
                deployment_name=resource_group
            )
            rg_client().resource_groups.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                parameters=resource_group_params
            )
            deployment_client()\
                .deployments.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                deployment_name=resource_group,
                parameters=AzDeployment(properties=deployment_properties),
                verify=True
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get("name"),
                resource_group
            )

    def test_create_already_exists(self, rg_client, deployment_client,
                                   credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        self.node.properties['use_external_resource'] = True

        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['template'] = TEST_TEMPLATE
        self.node.properties['location'] = 'westus'
        properties = self.node.properties
        template = deployment.get_template(self.fake_ctx, properties)
        deployment_params = {
            'mode': DeploymentMode.incremental,
            'template': template,
            'parameters': deployment.format_params(properties.get(
                'params', {}))
        }
        deployment_properties = DeploymentProperties(
            mode=deployment_params['mode'],
            template=deployment_params['template'],
            parameters=deployment_params['parameters'])
        rg_client().resource_groups.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(ctx=self.fake_ctx)
            deployment_client().deployments.get.assert_called_with(
                resource_group_name=resource_group,
                deployment_name=resource_group
            )
            deployment_client()\
                .deployments.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                deployment_name=resource_group,
                parameters=AzDeployment(properties=deployment_properties),
                verify=True
            )

    def test_create_with_external_resource(self, rg_client, deployment_client,
                                           credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['location'] = 'westus'
        self.node.properties['use_external_resource'] = True
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(ctx=self.fake_ctx, template="{}")

    def test_create_without_template(self, rg_client, deployment_client,
                                     credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        self.node.properties['resource_group_name'] = resource_group
        err = compose_not_found_cloud_error()
        rg_client().resource_groups.get.side_effect = err
        deployment_client().deployments.get.side_effect = err
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            with self.assertRaises(cfy_exc.NonRecoverableError) as ex:
                deployment.create(ctx=self.fake_ctx)
            self.assertTrue(
                "Deployment template not provided" in '{0}'.format(
                    ex.exception))

    def test_create_with_template_string(self, rg_client, deployment_client,
                                         credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = TEST_RESOURCE_GROUP_NAME
        self.node.properties['name'] = resource_group
        self.node.properties['resource_group_name'] = resource_group
        err = compose_not_found_cloud_error()
        rg_client().resource_groups.get.side_effect = err
        deployment_client().deployments.get.side_effect = err
        deployment_properties = DeploymentProperties(
            mode=DeploymentMode.incremental,
            template={},
            parameters={})
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(
                ctx=self.fake_ctx,
                name="check",
                template="{}",
                location="west",
                timeout=10,
                azure_config=self.node.properties.get('azure_config')
            )

            deployment_client()\
                .deployments.create_or_update.assert_called_with(
                    resource_group_name=resource_group,
                    deployment_name=resource_group,
                    parameters=AzDeployment(properties=deployment_properties),
                    verify=True
                )
            async_call = \
                deployment_client().deployments.create_or_update.return_value
            async_call.wait.assert_called_with(timeout=10)

    def test_create_with_template_file(self, rg_client, deployment_client,
                                       credentials):
        fock = tempfile.NamedTemporaryFile(delete=False)
        fock.write(json.dumps({'a': 'b'}).encode('utf-8'))
        fock.close()

        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = TEST_RESOURCE_GROUP_NAME
        self.node.properties['name'] = resource_group
        self.node.properties['resource_group_name'] = resource_group

        self.node.properties['template'] = None
        self.node.properties['template_file'] = fock.name
        self.fake_ctx.get_resource.return_value = open(fock.name).read()

        err = compose_not_found_cloud_error()
        rg_client().resource_groups.get.side_effect = err
        deployment_client().deployments.get.side_effect = err
        deployment_properties = DeploymentProperties(
            mode=DeploymentMode.incremental,
            template={'a': 'b'},
            parameters={'c': {'value': 'd'}})
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(
                ctx=self.fake_ctx,
                name="check",
                location="west",
                params={'c': 'd'},
                azure_config=self.node.properties.get('azure_config')
            )

            self.fake_ctx.get_resource.assert_called_with(fock.name)

            deployment_client() \
                .deployments.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                deployment_name=resource_group,
                parameters=AzDeployment(properties=deployment_properties),
                verify=True
            )
            async_call = \
                deployment_client().deployments.create_or_update.return_value
            async_call.wait.assert_called_with(timeout=900)

    def test_delete(self, rg_client, deployment_client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = TEST_RESOURCE_GROUP_NAME
        self.instance.runtime_properties['name'] = resource_group
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.delete(ctx=self.fake_ctx)
            rg_client().resource_groups.delete.assert_called_with(
                resource_group_name=resource_group
            )

    def test_delete_do_not_exist(self, rg_client, deployment_client,
                                 credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = TEST_RESOURCE_GROUP_NAME
        self.instance.runtime_properties['name'] = resource_group
        err = compose_not_found_cloud_error()
        rg_client().resource_groups.get.side_effect = err
        deployment_client().deployments.get.side_effect = err
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.delete(ctx=self.fake_ctx)
            rg_client().resource_groups.delete.assert_not_called()
            deployment_client().deployments.get.assert_not_called()
            deployment_client().deployments.delete.assert_not_called()

    def test_delete_with_external_resource(self, rg_client, deployment_client,
                                           credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = TEST_RESOURCE_GROUP_NAME
        self.instance.runtime_properties['name'] = resource_group
        self.node.properties['use_external_resource'] = True
        deployment.delete(ctx=self.fake_ctx)
        rg_client().resource_groups.delete.assert_not_called()
        deployment_client().deployments.get.assert_not_called()
        deployment_client().deployments.delete.assert_not_called()

    def test_pull_no_resource_group(self, rg_client, deployment_client,
                                    credentials):
        """
        Test pull when resource group deleted, it means the state should
        be empty and is_drifted should be true.
        """
        self.node.properties['client_config'] = self.dummy_azure_credentials
        self.instance.runtime_properties['name'] = TEST_RESOURCE_GROUP_NAME
        rg_client().resource_groups.get.side_effect = \
            compose_not_found_cloud_error()
        deployment.pull(ctx=self.fake_ctx)
        self.assertEquals(self.fake_ctx.instance.runtime_properties[STATE], [])
        self.assertEquals(
            self.fake_ctx.instance.runtime_properties[IS_DRIFTED], True)

    @mock.patch('cloudify_azure.resources.deployment.calculate_state')
    @mock.patch(
        'azure_sdk.resources.resource_group.ResourceGroup.list_resources')
    def test_pull(self,
                  list_resources_mock,
                  calculate_state_mock,
                  rg_client,
                  deployment_client,
                  credentials,
                  ):
        self._test_pull_op(list_resources_mock,
                           calculate_state_mock,
                           rg_client,
                           deployment_client,
                           True)

    @mock.patch('cloudify_azure.resources.deployment.calculate_state')
    @mock.patch(
        'azure_sdk.resources.resource_group.ResourceGroup.list_resources')
    def test_pull_template_from_properties(self,
                                           list_resources_mock,
                                           calculate_state_mock,
                                           rg_client,
                                           deployment_client,
                                           credentials):
        self._test_pull_op(list_resources_mock,
                           calculate_state_mock,
                           rg_client,
                           deployment_client,
                           False)

    def _test_pull_op(self,
                      list_resources_mock,
                      calculate_state_mock,
                      rg_client,
                      deployment_client,
                      template_in_runtime_props):
        self.node.properties['client_config'] = self.dummy_azure_credentials
        self.instance.runtime_properties['name'] = TEST_RESOURCE_GROUP_NAME

        if template_in_runtime_props:
            self.instance.runtime_properties.update(
                RUNTIME_PROPERTIES_AFTER_CREATE)
        else:
            self.node.properties['template'] = TEST_TEMPLATE

        rg_client().resource_groups.get.return_value = mock.Mock()
        deployment_client().deployments.what_if.return_value = mock.Mock()
        what_if_properties = DeploymentWhatIfProperties(
            mode=DeploymentMode.incremental,
            template=TEST_TEMPLATE,
            parameters={})
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.pull(ctx=self.fake_ctx)
            rg_client().resource_groups.get.assert_called_with(
                resource_group_name=TEST_RESOURCE_GROUP_NAME)
            list_resources_mock.assert_called_with(TEST_RESOURCE_GROUP_NAME)
            deployment_client().deployments.what_if.assert_called_with(
                resource_group_name=TEST_RESOURCE_GROUP_NAME,
                deployment_name=TEST_RESOURCE_GROUP_NAME,
                properties=what_if_properties)
            calculate_state_mock.assert_called_once()

    def test_calculate_state_no_drifts(self, *_):
        deployment.calculate_state(ctx=self.fake_ctx,
                                   initial_resources=RESOURCES_LIST,
                                   actual_resources=RESOURCES_LIST,
                                   what_if_res={'status': 'Succeeded',
                                                'changes': []})
        self.assertEquals(self.fake_ctx.instance.runtime_properties[STATE],
                          ['/fake/resource/id/1', '/fake/resource/id/2'])
        self.assertEquals(
            self.fake_ctx.instance.runtime_properties[IS_DRIFTED], False)

    def test_calculate_state_no_drifts_with_what_if_result_check(self, *_):
        deployment.calculate_state(
            ctx=self.fake_ctx,
            initial_resources=RESOURCES_LIST,
            actual_resources=[],
            what_if_res={'status': 'Succeeded',
                         'changes': [
                             {
                                 'resource_id': '/fake/resource/id/1',
                                 'change_type': "NoChange"
                             },
                             {
                                 'resource_id': '/fake/resource/id/2',
                                 'change_type': "Modify"
                             }
                         ]
                         })
        self.assertEquals(self.fake_ctx.instance.runtime_properties[STATE],
                          ['/fake/resource/id/1', '/fake/resource/id/2'])
        self.assertEquals(
            self.fake_ctx.instance.runtime_properties[IS_DRIFTED], False)

    def test_calculate_state_with_drifts(self, *_):
        deployment.calculate_state(ctx=self.fake_ctx,
                                   initial_resources=RESOURCES_LIST,
                                   actual_resources=[],
                                   what_if_res={'status': 'Succeeded',
                                                'changes': []})
        self.assertEquals(self.fake_ctx.instance.runtime_properties[STATE],
                          [])
        self.assertEquals(
            self.fake_ctx.instance.runtime_properties[IS_DRIFTED], True)

    def test_calculate_state_with_drifts_from_what_if_res(self, *_):
        resource = {'id': '/fake/resource/id/1'}
        deployment.calculate_state(
            ctx=self.fake_ctx,
            initial_resources=RESOURCES_LIST,
            actual_resources=[resource],
            what_if_res={'status': 'Succeeded',
                         'changes': [{
                             'resource_id': '/fake/resource/id/2',
                             'change_type': 'Create'
                         }]})
        self.assertEquals(self.fake_ctx.instance.runtime_properties[STATE],
                          [resource['id']])
        self.assertEquals(
            self.fake_ctx.instance.runtime_properties[IS_DRIFTED], True)
