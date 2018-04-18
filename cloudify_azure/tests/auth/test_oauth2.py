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
    tests.auth.OAuth2
    ~~~~~~~~~~~~~~~~~
    Tests OAuth 2.0 authorization interface for the Microsoft Azure REST API
'''

from sys import stdout
import logging
import unittest
import httplib
import requests_mock

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx

from cloudify_azure.auth import oauth2
from cloudify_azure import constants, exceptions


class OAuth2TestCase(unittest.TestCase):
    '''Tests OAuth2 interface'''
    def setUp(self):
        self.ctx = MockCloudifyContext(node_id='test_oauth2',
                                       node_name='OAuth2TestCase',
                                       runtime_properties={},
                                       properties={})
        self.log = logging.getLogger('tests.OAuth2TestCase')
        stream = logging.StreamHandler(stdout)
        stream.setLevel(logging.INFO)
        self.log.addHandler(stream)
        self.credentials = oauth2.AzureCredentials(
            tenant_id='123456',
            client_id='1234567',
            client_secret='1234-1234-1234-1234',
            subscription_id='subscription_id',
            endpoint_resource=constants.OAUTH2_MGMT_RESOURCE,
            endpoint_verify=True,
            endpoints_resource_manager=constants.CONN_API_ENDPOINT,
            endpoints_active_directory=constants.OAUTH2_ENDPOINT
        )
        current_ctx.set(self.ctx)

    def tearDown(self):
        current_ctx.clear()

    def test_bad_credentials_type(self):
        '''Send credentials in a non-AzureCredentials format'''
        self.assertRaises(
            exceptions.InvalidCredentials,
            oauth2.OAuth2, {'username': 'cloudify'})

    @requests_mock.Mocker()
    def test_missing_return(self, mock):
        '''Test for missing return data'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json=None,
            status_code=httplib.OK
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.UnexpectedResponse,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_bad_return_type(self, mock):
        '''Test for wrong JSON return type'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json=['bad', 'data'],
            status_code=httplib.OK
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.UnexpectedResponse,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_non_json_return_type(self, mock):
        '''Test for invalid JSON return type'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            text='non-json',
            status_code=httplib.OK
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.UnexpectedResponse,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_bad_credentials(self, mock):
        '''Test for invalid credentials return'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json={
                'error': 'invalid_client'
            },
            status_code=httplib.UNAUTHORIZED
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.InvalidCredentials,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_unauthorized(self, mock):
        '''Test for general "unauthorized" return'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json={
                'error': 'unknown_code'
            },
            status_code=httplib.UNAUTHORIZED
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.UnauthorizedRequest,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_unexpected_http_code(self, mock):
        '''Test for unexpected HTTP status code'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json=None,
            status_code=httplib.SERVICE_UNAVAILABLE
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.UnexpectedResponse,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_missing_token(self, mock):
        '''Test for missing token response'''
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json={},
            status_code=httplib.OK
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        self.assertRaises(
            exceptions.UnexpectedResponse,
            client.request_access_token)

    @requests_mock.Mocker()
    def test_good_token(self, mock):
        '''Test for good token response'''
        token = '1234-1234-1234-1234'
        mock.register_uri(
            'POST',
            '{0}/{1}/oauth2/token'.format(
                constants.OAUTH2_ENDPOINT,
                self.credentials.tenant_id),
            json={'access_token': token},
            status_code=httplib.OK
        )
        client = oauth2.OAuth2(self.credentials, logger=self.log)
        data = client.request_access_token()
        self.assertEqual(data.get('access_token'), token)
