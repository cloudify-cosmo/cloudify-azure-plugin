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
import mock
import unittest

from cloudify import exceptions as cfy_exc
from cloudify import mocks as cfy_mocks
from cloudify.state import current_ctx

from azure.mgmt.resource.resources.models import DeploymentMode

from cloudify_azure import constants
import cloudify_azure.resources.deployment as deployment


class DeploymentTest(unittest.TestCase):

    def tearDown(self):
        current_ctx.clear()

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
        fake_ctx, _, instance = self._get_mock_context_for_run()
        current_ctx.set(fake_ctx)

        instance.runtime_properties['resource_id'] = 'check_id'

        credentials = mock.MagicMock()
        async_call = mock.MagicMock()
        async_call.wait = mock.MagicMock()
        client = mock.MagicMock()
        client.resource_groups = mock.MagicMock()
        client.resource_groups.delete = mock.MagicMock(
            return_value=async_call
        )

        with mock.patch(
            'cloudify_azure.resources.deployment.ServicePrincipalCredentials',
            mock.MagicMock(return_value=credentials)
        ) as credentials_call:
            with mock.patch(
                'cloudify_azure.resources.deployment.ResourceManagementClient',
                mock.MagicMock(return_value=client)
            ) as client_call:
                deployment.delete(ctx=fake_ctx, name="check", azure_config={
                    'client_id': "client_id",
                    'client_secret': "client_secret",
                    'tenant_id': "tenant_id",
                    'subscription_id': "subscription_id",
                })

        credentials_call.assert_called_with(
            client_id='client_id',
            resource=constants.OAUTH2_MGMT_RESOURCE,
            secret='client_secret',
            tenant='tenant_id',
            verify=True)
        client_call.assert_called_with(credentials, "subscription_id",
                                       base_url='https://management.azure.com')

        async_call.wait.assert_called_with(timeout=None)
        client.resource_groups.delete.assert_called_with('check_id',
                                                         verify=True)

    def test_create(self):
        fake_ctx, node, _ = self._get_mock_context_for_run()
        current_ctx.set(fake_ctx)

        credentials = mock.MagicMock()
        async_call = mock.MagicMock()
        async_call.wait = mock.MagicMock()
        client = mock.MagicMock()
        client.deployments = mock.MagicMock()
        client.deployments.create_or_update = mock.MagicMock(
            return_value=async_call
        )

        with mock.patch(
            'cloudify_azure.resources.deployment.ServicePrincipalCredentials',
            mock.MagicMock(return_value=credentials)
        ) as credentials_call:
            with mock.patch(
                'cloudify_azure.resources.deployment.ResourceManagementClient',
                mock.MagicMock(return_value=client)
            ) as client_call:
                # call without templates
                with self.assertRaises(cfy_exc.NonRecoverableError) as ex:
                    deployment.create(
                        ctx=fake_ctx,
                        name="check",
                        azure_config={
                            'client_id': "client_id",
                            'client_secret': "client_secret",
                            'tenant_id': "tenant_id",
                            'subscription_id': "subscription_id",
                        }
                    )
                self.assertEqual(str(ex.exception),
                                 "Template does not defined.")

                credentials_call.assert_called_with(
                    client_id='client_id',
                    resource=constants.OAUTH2_MGMT_RESOURCE,
                    secret='client_secret',
                    tenant='tenant_id',
                    verify=True)
                client_call.assert_called_with(
                    credentials, "subscription_id",
                    base_url='https://management.azure.com')

                deployment.create(
                    ctx=fake_ctx,
                    name="check",
                    template="{}",
                    location="west",
                    timeout=10,
                    azure_config={
                        'client_id': "client_id",
                        'client_secret': "client_secret",
                        'tenant_id': "tenant_id",
                        'subscription_id': "subscription_id",
                    }
                )

                async_call.wait.assert_called_with(timeout=10)
                client.deployments.create_or_update.assert_called_with(
                    'check', 'check', {
                        'parameters': {},
                        'mode': DeploymentMode.incremental,
                        'template': {}
                    }, verify=True
                )

                node.properties['template_file'] = "check.json"
                fake_ctx.get_resource = mock.MagicMock(
                    return_value='{"a":"b"}'
                )

                deployment.create(
                    ctx=fake_ctx,
                    name="check",
                    location="west",
                    params={'c': 'd'},
                    azure_config={
                        'client_id': "client_id",
                        'client_secret': "client_secret",
                        'tenant_id': "tenant_id",
                        'subscription_id': "subscription_id",
                    }
                )

                fake_ctx.get_resource.assert_called_with("check.json")
                async_call.wait.assert_called_with(timeout=None)
                client.deployments.create_or_update.assert_called_with(
                    'check', 'check', {
                        'parameters': {'c': {'value': 'd'}},
                        'mode': DeploymentMode.incremental,
                        'template': {'a': 'b'}
                    }, verify=True
                )


if __name__ == '__main__':
    unittest.main()
