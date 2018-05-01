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
    tests.common
    ~~~~~~~~~~~~
    Test utilities
'''

import httplib
from cloudify_azure import constants

# pylint: disable=R0913


def mock_oauth2_endpoint(mock, params):
    '''Mock endpoint URLs'''
    mock.register_uri(
        'POST',
        '{0}/{1}/oauth2/token'.format(
            constants.OAUTH2_ENDPOINT,
            params['tenant_id']),
        json={'access_token': params['oauth2_token']},
        status_code=httplib.OK
    )


def mock_retry_async_endpoint(mock, params):
    '''Mock the Azure async "retry" endpoint'''
    mock.register_uri(
        'GET',
        params['mock_retry_url'],
        json={'response': 'ok'},
        status_code=httplib.OK
    )


def mock_resourcegroup_endpoint(mock, params):
    '''Mock ResourceGroup endpoint URLs'''
    mock.register_uri(
        'GET',
        '{0}/subscriptions/{1}{2}'.format(
            constants.CONN_API_ENDPOINT,
            params['subscription_id'],
            '{0}?api-version={1}'.format(
                '/resourceGroups/{0}'.format(params['mock_rg_name']),
                constants.API_VER_RESOURCES)),
        json={'response': 'ok'},
        status_code=httplib.OK
    )


def mock_storageaccount_endpoint(mock, params):
    '''Mock StorageAccount endpoint URLs'''
    mock.register_uri(
        'POST',
        '{0}/subscriptions/{1}{2}'.format(
            constants.CONN_API_ENDPOINT,
            params['subscription_id'],
            '/{0}/{1}/{2}?api-version={3}'.format(
                'resourceGroups/{0}'.format(params['mock_rg_name']),
                'providers/Microsoft.Storage',
                'storageAccounts/mocksa/listKeys',
                constants.API_VER_STORAGE)),
        json={
            'key1': 'asdklfjaskldfjaf88934==22jkl5',
            'key2': 'q3489hzdgodfgio===//4236'
        },
        status_code=httplib.OK
    )


def mock_endpoints(mock, params, res_type,
                   res_name, api_version, cls, get_json=None):
    '''Mock an endpoint'''
    endpoint = '{0}/subscriptions/{1}{2}'.format(
        constants.CONN_API_ENDPOINT,
        params['subscription_id'],
        '{0}/{1}?api-version={2}'.format(
            '/{0}/{1}'.format(
                'resourceGroups/{0}'.format(params['mock_rg_name']),
                'providers/{0}/{1}'.format(
                    cls, res_type)),
            res_name,
            api_version))

    mock.register_uri(
        'PUT',
        endpoint,
        headers={
            'Location': params['mock_retry_url'],
            'x-ms-request-id': '123412341234',
            'Retry-After': '1'
        },
        status_code=httplib.ACCEPTED
    )
    mock.register_uri(
        'DELETE',
        endpoint,
        status_code=httplib.OK
    )
    mock.register_uri(
        'GET',
        endpoint,
        json=get_json or {'response': 'ok'},
        status_code=httplib.OK
    )


def mock_network_endpoints(mock, params, res_type, res_name, get_json=None):
    '''Mock a network endpoint'''
    mock_endpoints(mock, params, res_type, res_name,
                   constants.API_VER_NETWORK, 'Microsoft.Network', get_json)


def mock_compute_endpoints(mock, params, res_type, res_name, get_json=None):
    '''Mock a compute endpoint'''
    mock_endpoints(mock, params, res_type, res_name,
                   constants.API_VER_COMPUTE, 'Microsoft.Compute', get_json)


def mock_storage_endpoints(mock, params, res_type, res_name, get_json=None):
    '''Mock a storage endpoint'''
    mock_endpoints(mock, params, res_type, res_name,
                   constants.API_VER_STORAGE, 'Microsoft.Storage', get_json)
