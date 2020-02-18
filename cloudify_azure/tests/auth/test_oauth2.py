# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
    tests.auth.OAuth2
    ~~~~~~~~~~~~~~~~~
    Tests OAuth 2.0 authorization interface for the Microsoft Azure REST API
'''

from sys import stdout
import logging
import unittest
import mock
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
            endpoints_active_directory=constants.OAUTH2_ENDPOINT,
            certificate=None,
            thumbprint=None,
            cloud_environment=None
        )
        self.cert_credentials = oauth2.AzureCredentials(
            tenant_id='123456',
            client_id='1234567',
            client_secret=None,
            subscription_id='subscription_id',
            endpoint_resource=constants.OAUTH2_MGMT_RESOURCE,
            endpoint_verify=True,
            endpoints_resource_manager=constants.CONN_API_ENDPOINT,
            endpoints_active_directory=constants.OAUTH2_ENDPOINT,
            certificate='dummy certificate',
            thumbprint='27EFC095BFE002AF43A3F32D7C0DD725BB54717E',
            cloud_environment=None
        )
        current_ctx.set(self.ctx)

    def tearDown(self):
        current_ctx.clear()

    def test_bad_credentials_type(self):
        '''Send credentials in a non-AzureCredentials format'''
        self.assertRaises(
            exceptions.InvalidCredentials,
            oauth2.OAuth2, {'username': 'cloudify'})

    def test_certificate_credentials(self):
        sp_credentials_mock = mock.patch(
            'cloudify_azure.auth.oauth2.CustomServicePrincipalCredentials')
        sp_cert_credentials_mock = mock.patch(
            'cloudify_azure.auth.oauth2.ServicePrincipalCertificateAuth')
        ServicePrincipalCredentials = sp_credentials_mock.start()
        ServicePrincipalCertificateAuth = sp_cert_credentials_mock.start()

        oauth2.to_service_principle_credentials(
            client_id='aa22',
            certificate='123',
            thumbprint='27EFC095BFE002AF43A3F32D7C0DD725BB54717E')
        ServicePrincipalCertificateAuth.assert_called_once()
        ServicePrincipalCredentials.assert_not_called()
        oauth2.to_service_principle_credentials(
            client_id='aa22',
            client_secret='555')
        ServicePrincipalCertificateAuth.assert_called_once()
        ServicePrincipalCredentials.assert_called_once()

    @mock.patch('requests.sessions.Session.post')
    def test_auth_with_secret(self, post_mock):
        post_mock.return_value = mock.MagicMock()
        post_mock.return_value.json = mock.MagicMock(
            return_value={'access_token': '123'})
        post_mock.return_value.status_code = httplib.OK

        client = oauth2.OAuth2(self.credentials, logger=self.log)
        client.request_access_token()
        post_mock.assert_called_with('{0}/{1}/oauth2/token'.format(
            constants.OAUTH2_ENDPOINT,
            self.credentials.tenant_id), data={
            'client_id': self.credentials.client_id,
            'grant_type': constants.OAUTH2_GRANT_TYPE,
            'resource': self.credentials.endpoint_resource,
            'client_secret': self.credentials.client_secret,
        })

    @mock.patch('cloudify_azure.auth.oauth2.jwt.encode')
    @mock.patch('requests.sessions.Session.post')
    def test_auth_with_certificate(self, post_mock, jwt_encode_mock):
        post_mock.return_value = mock.MagicMock()
        jwt_encode_mock.return_value = "sample_client_assertion"
        post_mock.return_value.json = mock.MagicMock(
            return_value={'access_token': '123'})
        post_mock.return_value.status_code = httplib.OK

        client = oauth2.OAuth2(self.cert_credentials, logger=self.log)
        client.request_access_token()
        jwt_encode_mock.assert_called()
        post_mock.assert_called_with('{0}/{1}/oauth2/token'.format(
            constants.OAUTH2_ENDPOINT,
            self.cert_credentials.tenant_id), data={
            'client_id': self.cert_credentials.client_id,
            'grant_type': constants.OAUTH2_GRANT_TYPE,
            'resource': self.cert_credentials.endpoint_resource,
            'client_assertion_type': constants.OAUTH2_JWT_ASSERTION_TYPE,
            'client_assertion': 'sample_client_assertion'
        })

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
