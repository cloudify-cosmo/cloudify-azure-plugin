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
from cloudify import exceptions as cfy_exc

from cloudify_azure.resources.app_service import plan, webapp, publishing_user


@mock.patch('azure_sdk.common.ServicePrincipalCredentials')
@mock.patch('azure_sdk.resources.app_service.'
            'plan.WebSiteManagementClient')
class PlanTest(unittest.TestCase):

    def _get_mock_context_for_run(self):
        operation = {'name': 'cloudify.interfaces.lifecycle.mock'}
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
        name = 'plan_name'
        plan_details = {
            'key': 'value'
        }
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().app_service_plans.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            plan.create(self.fake_ctx, resource_group, name, plan_details)
            client().app_service_plans.get.assert_called_with(
                resource_group_name=resource_group,
                name=name
            )
            client().app_service_plans.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                name=name,
                app_service_plan=plan_details
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'plan_name'
        plan_details = {
            'key': 'value'
        }
        client().app_service_plans.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            plan.create(self.fake_ctx, resource_group, name, plan_details)
            client().app_service_plans.get.assert_called_with(
                resource_group_name=resource_group,
                name=name
            )
            client().app_service_plans.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'plan_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            plan.delete(self.fake_ctx)
            client().app_service_plans.delete.assert_called_with(
                resource_group_name=resource_group,
                name=name
            )

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'plan_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().app_service_plans.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            plan.delete(self.fake_ctx)
            client().app_service_plans.delete.assert_not_called()


@mock.patch('azure_sdk.common.ServicePrincipalCredentials')
@mock.patch('azure_sdk.resources.app_service.'
            'web_app.WebSiteManagementClient')
class WebAppTest(unittest.TestCase):

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
        name = 'app_name'
        app_details = {
            'key': 'value'
        }
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().web_apps.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            webapp.create(self.fake_ctx, resource_group, name, app_details)
            client().web_apps.get.assert_called_with(
                resource_group_name=resource_group,
                name=name
            )
            client().web_apps.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                name=name,
                site_envelope=app_details
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
        name = 'app_name'
        app_details = {
            'key': 'value'
        }
        client().web_apps.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            webapp.create(self.fake_ctx, resource_group, name, app_details)
            client().web_apps.get.assert_called_with(
                resource_group_name=resource_group,
                name=name
            )
            client().web_apps.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'app_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            webapp.delete(self.fake_ctx)
            client().web_apps.delete.assert_called_with(
                resource_group_name=resource_group,
                name=name
            )

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'app_name'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().web_apps.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            webapp.delete(self.fake_ctx)
            client().web_apps.delete.assert_not_called()


@mock.patch('azure_sdk.common.ServicePrincipalCredentials')
@mock.patch('azure_sdk.resources.app_service.'
            'publishing_user.WebSiteManagementClient')
class PublishingUserTest(unittest.TestCase):

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

    def test_set_user(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        user_details = {
            'key': 'value'
        }
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            publishing_user.set_user(self.fake_ctx, user_details)
            client().update_publishing_user.assert_called_with(
                user_details=user_details
            )

    def test_set_user_empty_details(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        user_details = {}
        with self.assertRaises(cfy_exc.NonRecoverableError):
            with mock.patch('cloudify_azure.utils.secure_logging_content',
                            mock.Mock()):
                publishing_user.set_user(self.fake_ctx, user_details)
                client().update_publishing_user.assert_called_with(
                    user_details=user_details
                )
