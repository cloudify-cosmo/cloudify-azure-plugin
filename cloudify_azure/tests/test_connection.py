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
    tests.Connection
    ~~~~~~~~~~~~~~~~
    Tests Microsoft Azure REST API connection helpers
'''

from sys import stdout
import logging
import unittest
import httplib
import requests_mock

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from cloudify_azure import constants, exceptions, connection


class ConnectionTestCase(unittest.TestCase):
    '''Tests connection interface'''
    def setUp(self):
        self.tenant_id = '123456'
        self.subscription_id = '12345-12345-12345'
        self.node_properties = {
            'azure_config': {
                'tenant_id': self.tenant_id,
                'client_id': '1234567',
                'client_secret': '1234-1234-1234-1234',
                'subscription_id': self.subscription_id,
                'endpoint_resource': constants.OAUTH2_MGMT_RESOURCE,
                'endpoint_verify': True,
                'endpoints_resource_manager': constants.CONN_API_ENDPOINT,
                'endpoints_active_directory': constants.OAUTH2_ENDPOINT
            }
        }
        self.ctx = MockCloudifyContext(node_id='test_connection',
                                       node_name='ConnectionTestCase',
                                       runtime_properties={},
                                       properties=self.node_properties)

        self.log = logging.getLogger('tests.ConnectionTestCase')
        stream = logging.StreamHandler(stdout)
        stream.setLevel(logging.INFO)
        self.log.addHandler(stream)
        current_ctx.set(self.ctx)

    def tearDown(self):
        current_ctx.clear()

    @requests_mock.Mocker()
    def test_good_init(self, mock):
        '''Test for a successful init'''
        token = '1234-1234-1234-1234'
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.tenant_id),
            json={'access_token': token},
            status_code=httplib.OK
        )
        connection.AzureConnection(logger=self.log)

    @requests_mock.Mocker()
    def test_good_request(self, mock):
        '''Test for a successful request'''
        token = '1234-1234-1234-1234'
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.tenant_id),
            json={'access_token': token},
            status_code=httplib.OK
        )
        mock.register_uri(
            'GET',
            '{0}/subscriptions/{1}{2}'.format(
                constants.CONN_API_ENDPOINT,
                self.subscription_id,
                '/some/resource'),
            json={
                'data': 'stuff'
            },
            status_code=httplib.OK
        )
        conn = connection.AzureConnection(logger=self.log)
        res = conn.request(url='/some/resource', method='get')
        self.assertEqual(res.status_code, httplib.OK)
        self.assertEqual(res.json().get('data'), 'stuff')

    @requests_mock.Mocker()
    def test_bad_credentials_request(self, mock):
        '''Test for a request using bad credentials'''
        token = '1234-1234-1234-1234'
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.tenant_id),
            json={'access_token': token},
            status_code=httplib.OK
        )
        mock.register_uri(
            'GET',
            '{0}/subscriptions/{1}{2}'.format(
                constants.CONN_API_ENDPOINT,
                self.subscription_id,
                '/some/resource'),
            json={
                'error': 'invalid_client'
            },
            status_code=httplib.UNAUTHORIZED
        )
        conn = connection.AzureConnection(logger=self.log)
        self.assertRaises(
            exceptions.InvalidCredentials,
            conn.request, url='/some/resource', method='get')

    @requests_mock.Mocker()
    def test_unauthorized_request(self, mock):
        '''Test for an unauthorized request'''
        token = '1234-1234-1234-1234'
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.tenant_id),
            json={'access_token': token},
            status_code=httplib.OK
        )
        mock.register_uri(
            'GET',
            '{0}/subscriptions/{1}{2}'.format(
                constants.CONN_API_ENDPOINT,
                self.subscription_id,
                '/some/resource'),
            json={
                'error': 'unknown_code'
            },
            status_code=httplib.UNAUTHORIZED
        )
        conn = connection.AzureConnection(logger=self.log)
        self.assertRaises(
            exceptions.UnauthorizedRequest,
            conn.request, url='/some/resource', method='get')
