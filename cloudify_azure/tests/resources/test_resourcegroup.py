# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.
'''
    tests.resources.ResourceGroup
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Tests Microsoft Azure Resource Group interface
'''

from os import path
import unittest
import httplib
import requests_mock

from cloudify.test_utils import workflow_test

from cloudify_azure import constants

# pylint: disable=R0201
# pylint: disable=R0913


class TestResourceGroup(unittest.TestCase):
    '''Tests Resource Group interface'''
    blueprint_path = path.join('blueprints',
                               'test_resourcegroup.yaml')

    def setUp(self):
        self.tenant_id = '123456'
        self.subscription_id = '12345-12345-12345'
        self.mock_retry_url = 'http://mock-retry-url.com'
        self.mock_res_name = 'testrg'
        self.mock_endpoint = '/resourceGroups'

    def mock_oauth2_endpoint(self, mock):
        '''Mock endpoint URLs'''
        token = '1234-1234-1234-1234'
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.tenant_id),
            json={'access_token': token},
            status_code=httplib.OK
        )

    @requests_mock.Mocker(real_http=True)
    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    def test_lifecycle_install(self, cfy_local, mock, *_):
        '''ResourceGroup install workflow'''
        self.mock_oauth2_endpoint(mock)
        # Mock the Azure async "retry" endpoint
        mock.register_uri(
            'GET',
            self.mock_retry_url,
            json={'response': 'ok'},
            status_code=httplib.OK
        )
        # Mock endpoint to start an async Azure operation
        mock.register_uri(
            'PUT',
            '{0}/subscriptions/{1}{2}'.format(
                constants.CONN_API_ENDPOINT,
                self.subscription_id,
                '{0}/{1}?api-version={2}'.format(
                    self.mock_endpoint,
                    self.mock_res_name,
                    constants.API_VER_RESOURCES)),
            headers={
                'Location': self.mock_retry_url,
                'x-ms-request-id': '123412341234',
                'Retry-After': '1'
            },
            status_code=httplib.ACCEPTED
        )
        cfy_local.execute('install', task_retries=1)
        vars(cfy_local)

    @requests_mock.Mocker(real_http=True)
    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    def test_lifecycle_uninstall(self, cfy_local, mock, *_):
        '''ResourceGroup uninstall workflow'''
        self.mock_oauth2_endpoint(mock)
        mock.register_uri(
            'DELETE',
            '{0}/subscriptions/{1}{2}'.format(
                constants.CONN_API_ENDPOINT,
                self.subscription_id,
                '{0}/{1}?api-version={2}'.format(
                    self.mock_endpoint,
                    self.mock_res_name,
                    constants.API_VER_RESOURCES)),
            status_code=httplib.OK
        )
        cfy_local.execute('uninstall', task_retries=1)
