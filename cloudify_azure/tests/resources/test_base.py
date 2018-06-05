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
    tests.resources.Base
    ~~~~~~~~~~~~~~~~~~~~
    Tests Microsoft Azure API abstraction layer
'''

from sys import stdout
import logging
import unittest
import httplib
import requests_mock

from cloudify.mocks import MockCloudifyContext
from cloudify.state import current_ctx
from cloudify.exceptions import RecoverableError

from cloudify_azure import constants
from cloudify_azure.resources.base import Resource

# pylint: disable=R0913


class ResourcesBaseTestCase(unittest.TestCase):
    '''Tests base interface'''
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
        self.ctx = MockCloudifyContext(node_id='test_resources_base',
                                       node_name='ResourcesBaseTestCase',
                                       runtime_properties={},
                                       operation={
                                           'retry_number': 0
                                       },
                                       properties=self.node_properties)
        self.log = logging.getLogger('tests.ResourcesBaseTestCase')
        stream = logging.StreamHandler(stdout)
        stream.setLevel(logging.INFO)
        self.log.addHandler(stream)
        current_ctx.set(self.ctx)

    def tearDown(self):
        current_ctx.clear()

    def mock_endpoints(self, mock, endpoint, res_name,
                       json=None, status_code=httplib.OK,
                       headers=None):
        '''Mock endpoint URLs'''
        token = '1234-1234-1234-1234'
        endpoint = '/{0}/{1}/{2}'.format(
            'resourceGroups/test_resource_group',
            'providers/Microsoft.Compute',
            'virtualMachines')
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
                '{0}/{1}?api-version={2}'.format(
                    endpoint, res_name, constants.API_VER_COMPUTE)),
            json=json,
            headers=headers or dict(),
            status_code=status_code
        )

    @requests_mock.Mocker()
    def test_good_get(self, mock):
        '''Test for a successful get request'''
        name = 'Virtual Machine'
        res_name = 'testvm'
        endpoint = '/{0}/{1}/{2}'.format(
            'resourceGroups/test_resource_group',
            'providers/Microsoft.Compute',
            'virtualMachines')
        self.mock_endpoints(mock, endpoint, res_name,
                            json={'response': 'ok'})
        res = Resource(
            name,
            endpoint,
            api_version=constants.API_VER_COMPUTE,
            logger=self.log)
        self.assertEqual(res.name, name)
        self.assertEqual(res.endpoint, endpoint)
        data = res.get(name=res_name)
        self.assertTrue(isinstance(data, dict))

    @requests_mock.Mocker()
    def test_accepted_no_location(self, mock):
        '''Test for ACCEPTED without request URL'''
        name = 'Virtual Machine'
        res_name = 'testvm'
        endpoint = '/{0}/{1}/{2}'.format(
            'resourceGroups/test_resource_group',
            'providers/Microsoft.Compute',
            'virtualMachines')
        headers = {
            'x-ms-request-id': 'test-id-string',
            'Retry-After': '1'
        }
        self.mock_endpoints(mock, endpoint, res_name,
                            json={'response': 'ok'},
                            status_code=httplib.ACCEPTED,
                            headers=headers)
        res = Resource(
            name,
            endpoint,
            api_version=constants.API_VER_COMPUTE,
            logger=self.log)
        self.assertEqual(res.name, name)
        self.assertEqual(res.endpoint, endpoint)
        self.assertRaises(
            RecoverableError,
            res.get, name=res_name)
        self.assertEqual(
            self.ctx.instance.runtime_properties.get('async_op'),
            None)

    @requests_mock.Mocker()
    def test_accepted_no_id(self, mock):
        '''Test for ACCEPTED without request ID'''
        name = 'Virtual Machine'
        res_name = 'testvm'
        endpoint = '/{0}/{1}/{2}'.format(
            'resourceGroups/test_resource_group',
            'providers/Microsoft.Compute',
            'virtualMachines')
        headers = {
            'Location': 'https://test.com/test',
            'Retry-After': '1'
        }
        self.mock_endpoints(mock, endpoint, res_name,
                            json={'response': 'ok'},
                            status_code=httplib.ACCEPTED,
                            headers=headers)
        res = Resource(
            name,
            endpoint,
            api_version=constants.API_VER_COMPUTE,
            logger=self.log)
        self.assertEqual(res.name, name)
        self.assertEqual(res.endpoint, endpoint)
        res.get(name=res_name)
        self.assertEqual(
            self.ctx.instance.runtime_properties.get('async_op'),
            dict((k.lower(), v) for k, v in headers.items()))

    @requests_mock.Mocker()
    def test_accepted(self, mock):
        '''Test for ACCEPTED with proper headers'''
        name = 'Virtual Machine'
        res_name = 'testvm'
        endpoint = '/{0}/{1}/{2}'.format(
            'resourceGroups/test_resource_group',
            'providers/Microsoft.Compute',
            'virtualMachines')
        headers = {
            'Location': 'https://test.com/test',
            'x-ms-request-id': 'test-id-string',
            'Retry-After': '1'
        }
        self.mock_endpoints(mock, endpoint, res_name,
                            json={'response': 'ok'},
                            status_code=httplib.ACCEPTED,
                            headers=headers)
        res = Resource(
            name,
            endpoint,
            api_version=constants.API_VER_COMPUTE,
            logger=self.log)
        self.assertEqual(res.name, name)
        self.assertEqual(res.endpoint, endpoint)
        res.get(name=res_name)
        self.assertEqual(
            self.ctx.instance.runtime_properties.get('async_op'),
            dict((k.lower(), v) for k, v in headers.items()))
