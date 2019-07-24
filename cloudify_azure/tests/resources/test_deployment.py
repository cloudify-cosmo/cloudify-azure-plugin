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
import os
import mock
import unittest
import tempfile
import pathlib

from copy import deepcopy

from cloudify import exceptions as cfy_exc
from cloudify import mocks as cfy_mocks
from cloudify.state import current_ctx

from cloudify_azure.resources.deployment import Deployment

from azure.mgmt.resource.resources.models import DeploymentMode

from cloudify_azure import constants
import cloudify_azure.resources.deployment as deployment


class DeploymentTest(unittest.TestCase):

    def setUp(self):
        patch = mock.patch(
            'cloudify_azure.resources.deployment.ResourceManagementClient')
        self.Client = patch.start()
        self.client = self.Client.return_value
        self.addCleanup(patch.stop)

        patch = mock.patch('cloudify_azure.resources.deployment.'
                           'to_service_principle_credentials')
        self.Credentials = patch.start()
        self.addCleanup(patch.stop)

        self.fake_ctx, self.node, self.instance = \
            self._get_mock_context_for_run()
        current_ctx.set(self.fake_ctx)
        self.addCleanup(current_ctx.clear)

        self.azure_config = {
            'client_id': "client_id",
            'client_secret': "client_secret",
            'tenant_id': "tenant_id",
            'subscription_id': "subscription_id",
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

    def test_delete(self):
        self.instance.runtime_properties['resource_id'] = 'check_id'

        deployment.delete(ctx=self.fake_ctx,
                          name="check",
                          azure_config=self.azure_config)

        self.Credentials.assert_called_with(
            client_id='client_id',
            resource=constants.OAUTH2_MGMT_RESOURCE,
            secret='client_secret',
            certificate='',
            thumbprint='',
            cloud_environment='',
            endpoints_active_directory='',
            tenant='tenant_id',
            verify=True)
        self.Client.assert_called_with(self.Credentials.return_value,
                                       "subscription_id",
                                       base_url='https://management.azure.com')
        self.client.resource_groups.delete.assert_called_with('check_id',
                                                              verify=True)
        async_call = self.client.resource_groups.delete.return_value
        async_call.wait.assert_called_with(timeout=900)

    def test_delete_with_external_resource(self):
        self.node.properties['use_external_resource'] = True

        deployment.delete(ctx=self.fake_ctx,
                          name="check",
                          azure_config=self.azure_config)

        self.client.resource_groups.delete.assert_not_called()

    def test_init(self):
        deployment.create(
            ctx=self.fake_ctx,
            name="check",
            template="{}",
            location="west",
            timeout=10,
            azure_config=self.azure_config
        )

        self.Credentials.assert_called_with(
            client_id='client_id',
            resource=constants.OAUTH2_MGMT_RESOURCE,
            secret='client_secret',
            certificate='',
            thumbprint='',
            tenant='tenant_id',
            cloud_environment='',
            endpoints_active_directory='',
            verify=True)
        self.Client.assert_called_with(
            self.Credentials.return_value, "subscription_id",
            base_url='https://management.azure.com')

    def test_create_without_template(self):
        # call without templates
        with self.assertRaises(cfy_exc.NonRecoverableError) as ex:
            deployment.create(
                ctx=self.fake_ctx,
                name="check",
                azure_config=self.azure_config
            )
        self.assertTrue(
            "Deployment template not provided" in str(ex.exception))

    def test_create_with_template_string(self):
        deployment.create(
            ctx=self.fake_ctx,
            name="check",
            template="{}",
            location="west",
            timeout=10,
            azure_config=self.azure_config
        )

        self.client.deployments.create_or_update.assert_called_with(
            'check', 'check', {
                'parameters': {},
                'mode': DeploymentMode.incremental,
                'template': {}
            }, verify=True
        )
        async_call = self.client.deployments.create_or_update.return_value
        async_call.wait.assert_called_with(timeout=10)

    def test_create_with_template_file(self):
        self.node.properties['template_file'] = "check.json"
        self.fake_ctx.get_resource.return_value = '{"a":"b"}'

        deployment.create(
            ctx=self.fake_ctx,
            name="check",
            location="west",
            params={'c': 'd'},
            azure_config=self.azure_config
        )

        self.fake_ctx.get_resource.assert_called_with("check.json")
        self.client.deployments.create_or_update.assert_called_with(
            'check', 'check', {
                'parameters': {'c': {'value': 'd'}},
                'mode': DeploymentMode.incremental,
                'template': {'a': 'b'}
            }, verify=True
        )
        async_call = self.client.deployments.create_or_update.return_value
        async_call.wait.assert_called_with(timeout=900)

    def test_create_with_external_resource(self):
        self.node.properties['use_external_resource'] = True

        deployment.create(
            ctx=self.fake_ctx,
            name="check",
            location="west",
            azure_config=self.azure_config
        )
        self.client.deployments.create_or_update.assert_not_called()
        self.client.deployments.get.assert_called()

    def test_create_with_deployment_outputs(self):
        mock_outputs = {
            "exampleOutput": {
                "type": "String",
                "value": "exampleOutput",
            }
        }
        self.client.deployments.get.return_value.properties.outputs = \
            mock_outputs

        deployment.create(
            ctx=self.fake_ctx,
            name="check",
            location="west",
            template="{}",
            params={'c': 'd'},
            azure_config=self.azure_config
        )

        outputs = self.instance.runtime_properties['outputs']
        self.assertDictEqual(outputs, mock_outputs)

    def test_get_template_string(self):
        properties = {
            'template': '{"key": "value"}',
            'template_file': 'missing/file'
        }
        template = deployment.get_template(self.fake_ctx, properties)
        self.assertEqual(template, {
            'key': 'value'
        })

    def test_get_template_none(self):
        with self.assertRaises(cfy_exc.NonRecoverableError) as ex:
            deployment.get_template(self.fake_ctx, {})
        self.assertTrue("Deployment template not provided", str(ex.exception))

    def test_get_template_dict(self):
        properties = {
            'template': {
                'key': 'value'
            }
        }
        template = deployment.get_template(self.fake_ctx, properties)
        self.assertEquals(template, properties['template'])

    def test_get_template_url(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as tmp_file:
            tmp_file.write('{"key": "value"}')
            tmp_file.close()

        try:
            template = deployment.get_template(self.fake_ctx, {
                'template_file': pathlib.Path(tmp_file.name).as_uri()
            })
            self.assertEqual(template, {
                'key': 'value'
            })
        finally:
            os.remove(tmp_file.name)


class FormatParamsTest(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(Deployment.format_params(None), None)
        self.assertEqual(Deployment.format_params({}), {})

    def test_simple(self):
        d = {
            'key1': 4,
            'key2': False,
            'key3': 'hello'
        }
        result = Deployment.format_params(deepcopy(d))
        self.assertEqual(result, {
            'key1': {
                'value': 4
            },
            'key2': {
                'value': False
            },
            'key3': {
                'value': 'hello'
            }
        })

    def test_recursive(self):
        d = {
            'key1': 4,
            'key2': {
                'subkey1': 3,
                'subkey2': True,
                'subkey3': 'hello'
            }
        }
        result = Deployment.format_params(deepcopy(d))
        self.assertEqual(result, {
            'key1': {
                'value': 4
            },
            'key2': {
                'value': {
                    'subkey1': 3,
                    'subkey2': True,
                    'subkey3': 'hello'
                }
            }
        })


if __name__ == '__main__':
    unittest.main()
