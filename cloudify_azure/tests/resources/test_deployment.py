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
import requests
import tempfile
import unittest

from msrestazure.azure_exceptions import CloudError
from azure.mgmt.resource.resources.models import DeploymentMode

from cloudify import mocks as cfy_mocks
from cloudify import exceptions as cfy_exc

from cloudify_azure.resources import deployment


@mock.patch('azure_sdk.common.ServicePrincipalCredentials')
@mock.patch('azure_sdk.resources.deployment.ResourceManagementClient')
@mock.patch('azure_sdk.resources.resource_group.ResourceManagementClient')
class DeploymentTest(unittest.TestCase):

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

    def test_create(self, rg_client, deployment_client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        self.node.properties['template'] = {
            "$schema": "http://schema.management.azure.com/Template.json",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "storageEndpoint": {
                  "type": "string",
                  "defaultValue": "core.windows.net",
                  "metadata": {
                    "description": "Storage Endpoint."
                  }
                },
            }
        }
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
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        rg_client().resource_groups.get.side_effect = \
            CloudError(response, message)
        deployment_client().deployments.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(ctx=self.fake_ctx)
            rg_client().resource_groups.get.assert_called_with(
                resource_group_name=resource_group
            )
            rg_client().resource_groups.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                parameters=resource_group_params
            )
            deployment_client()\
                .deployments.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                deployment_name=resource_group,
                properties=deployment_params,
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
        self.node.properties['location'] = 'westus'
        rg_client().resource_groups.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(ctx=self.fake_ctx)
            rg_client().resource_groups.get.assert_called_with(
                resource_group_name=resource_group
            )
            rg_client().resource_groups.create_or_update.assert_not_called()
            deployment_client().deployments.get.assert_not_called()
            deployment_client()\
                .deployments.create_or_update.assert_not_called()

    def test_create_with_external_resource(self, rg_client, deployment_client,
                                           credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        self.node.properties['location'] = 'westus'
        self.node.properties['use_external_resource'] = True
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.create(ctx=self.fake_ctx, template="{}")
            deployment_client()\
                .deployments.create_or_update.assert_not_called()

    def test_create_without_template(self, rg_client, deployment_client,
                                     credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        rg_client().resource_groups.get.side_effect = \
            CloudError(response, message)
        deployment_client().deployments.get.side_effect = \
            CloudError(response, message)
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
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        rg_client().resource_groups.get.side_effect = \
            CloudError(response, message)
        deployment_client().deployments.get.side_effect = \
            CloudError(response, message)
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
                    properties={
                        'parameters': {},
                        'mode': DeploymentMode.incremental,
                        'template': {}
                    },
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
        resource_group = 'sample_deployment'
        self.node.properties['name'] = resource_group

        self.node.properties['template'] = None
        self.node.properties['template_file'] = fock.name
        self.fake_ctx.get_resource.return_value = open(fock.name).read()

        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        rg_client().resource_groups.get.side_effect = \
            CloudError(response, message)
        deployment_client().deployments.get.side_effect = \
            CloudError(response, message)
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

            deployment_client()\
                .deployments.create_or_update.assert_called_with(
                    resource_group_name=resource_group,
                    deployment_name=resource_group,
                    properties={
                        'parameters': {'c': {'value': 'd'}},
                        'mode': DeploymentMode.incremental,
                        'template': {'a': 'b'}
                    },
                    verify=True
                )
            async_call = \
                deployment_client().deployments.create_or_update.return_value
            async_call.wait.assert_called_with(timeout=900)

    def test_delete(self, rg_client, deployment_client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
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
        resource_group = 'sample_deployment'
        self.instance.runtime_properties['name'] = resource_group
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        rg_client().resource_groups.get.side_effect = \
            CloudError(response, message)
        deployment_client().deployments.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            deployment.delete(ctx=self.fake_ctx)
            rg_client().resource_groups.delete.assert_not_called()
            deployment_client().deployments.get.assert_not_called()
            deployment_client().deployments.delete.assert_not_called()

    def test_delete_with_external_resource(self, rg_client, deployment_client,
                                           credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_deployment'
        self.instance.runtime_properties['name'] = resource_group
        self.node.properties['use_external_resource'] = True
        deployment.delete(ctx=self.fake_ctx)
        rg_client().resource_groups.delete.assert_not_called()
        deployment_client().deployments.get.assert_not_called()
        deployment_client().deployments.delete.assert_not_called()
