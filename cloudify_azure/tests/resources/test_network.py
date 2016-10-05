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
    tests.resources.network
    ~~~~~~~~~~~~~~~~~~~~~~~
    Tests Microsoft Azure Network interfaces
'''

from os import path
import unittest
import requests_mock

from cloudify.test_utils import workflow_test
from cloudify_azure.tests import common as tutils

# pylint: disable=R0201
# pylint: disable=R0913


class TestNetwork(unittest.TestCase):
    '''Tests Network interfaces'''
    blueprint_path = path.join('blueprints',
                               'test_network.yaml')

    def setUp(self):
        self.mock_rg_name = 'mockrg'
        self.params = {
            'tenant_id': '123456',
            'subscription_id': '12345-12345-12345',
            'oauth2_token': '12345-1234-12345678',
            'mock_retry_url': 'mock://mock-retry-url.com',
            'mock_rg_name': self.mock_rg_name
        }

    def mock_install_endpoints(self, mock):
        '''Mock install endpoints'''
        tutils.mock_oauth2_endpoint(mock, self.params)
        tutils.mock_retry_async_endpoint(mock, self.params)
        tutils.mock_resourcegroup_endpoint(mock, self.params)

    def mock_uninstall_endpoints(self, mock):
        '''Mock uninstall endpoints'''
        tutils.mock_oauth2_endpoint(mock, self.params)
        tutils.mock_retry_async_endpoint(mock, self.params)
        tutils.mock_resourcegroup_endpoint(mock, self.params)

    def mock_network_endpoints(self, mock):
        '''Mock network endpoints'''
        tutils.mock_network_endpoints(mock, self.params,
                                      'virtualNetworks', 'mockvnet')
        tutils.mock_network_endpoints(mock, self.params,
                                      'networkSecurityGroups', 'mocknsg')
        tutils.mock_network_endpoints(mock, self.params,
                                      'networkSecurityRule', 'mocknsr')
        tutils.mock_network_endpoints(mock, self.params,
                                      'routeTables', 'mockroutetable')
        tutils.mock_network_endpoints(
            mock, self.params,
            'routeTables/{0}/routes'.format('mockroutetable'),
            'mockroute')
        tutils.mock_network_endpoints(mock, self.params,
                                      'networkInterfaces', 'mocknic')
        tutils.mock_network_endpoints(mock, self.params,
                                      'publicIPAddresses', 'mocknicpip')
        tutils.mock_network_endpoints(
            mock, self.params,
            'virtualNetworks/{0}/subnets'.format('mockvnet'),
            'mocksubnet')
        tutils.mock_network_endpoints(
            mock, self.params,
            'networkSecurityGroups/{0}/securityRules'.format('mocknsg'),
            'mocknsr')
        # Load balancer endpoints
        tutils.mock_network_endpoints(mock, self.params,
                                      'loadBalancers', 'mocklb')
        tutils.mock_network_endpoints(
            mock, self.params,
            'loadBalancers/{0}/backendAddressPools'.format('mocklb'),
            'mocklbbepool')
        tutils.mock_network_endpoints(
            mock, self.params,
            'loadBalancers/{0}/probes'.format('mocklb'),
            'mocklbprobe')
        tutils.mock_network_endpoints(mock, self.params,
                                      'PublicIPAddresses', 'mocklbpip')

    @requests_mock.Mocker(real_http=True)
    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    def test_lifecycle_install(self, cfy_local, mock, *_):
        '''network install workflow'''
        self.mock_install_endpoints(mock)
        self.mock_network_endpoints(mock)
        cfy_local.execute('install', task_retries=1)
        vars(cfy_local)

    @requests_mock.Mocker(real_http=True)
    @workflow_test(blueprint_path, copy_plugin_yaml=True)
    def test_lifecycle_uninstall(self, cfy_local, mock, *_):
        '''network uninstall workflow'''
        self.mock_uninstall_endpoints(mock)
        self.mock_network_endpoints(mock)
        cfy_local.execute('uninstall', task_retries=2)
