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
    auth.OAuth2
    ~~~~~~~~~~~
    OAuth 2.0 authorization interface for the Microsoft Azure REST API
'''

# For credentials structuring
from collections import namedtuple
# Used for HTTP requests / verification
import httplib
import requests
# Used to implement connection retrying
from requests.packages import urllib3
# Exception handling, constants, logging
from cloudify_azure import \
    (constants, exceptions)
# Context
from cloudify import ctx

# pylint: disable=R0903


AzureCredentials = namedtuple(
    'AzureCredentials',
    ['tenant_id', 'client_id', 'client_secret', 'subscription_id',
     'endpoint_resource', 'endpoint_verify', 'endpoints_resource_manager',
     'endpoints_active_directory']
)
'''
    Microsoft Azure credentials and access information

:param string tenant_id: Azure tenant ID
:param string client_id: Azure client ID (AD username)
:param string client_secret: Azure client secret (AD password)
:param string subscription_id: Azure subscription ID
'''


class OAuth2(object):
    '''
        OAuth 2.0 interface for the Microsoft Azure REST API

    :param `AzureCredentials` credentials:
        Azure credentials and access information
    :param `logging.Logger` logger:
        Logger for the class to use. Defaults to `ctx.logger`
    '''

    def __init__(self, credentials, logger=None, _ctx=ctx):
        # Set the active context
        self.ctx = _ctx
        # Configure logger
        self.log = logger or ctx.logger
        # Validate credentials type
        if not isinstance(credentials, AzureCredentials):
            raise exceptions.InvalidCredentials(
                'OAuth2() recieved credentials not of type AzureCredentials')
        # Get user authorization data
        self.credentials = credentials

    def request_access_token(self):
        '''Tenant-specific access token request.

        .. note::

           This uses a separate requests.Session() object from
           the rest of the class methods.  This ensures the session
           data isn't polluting the request or response data.

        :returns: Access token information
        :rtype: dict
        :raises: :exc:`cloudify_azure.exceptions.UnauthorizedRequest`,
                 :exc:`cloudify_azure.exceptions.UnexpectedResponse`,
                 :exc:`requests.RequestException`
        '''
        payload = {
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'grant_type': constants.OAUTH2_GRANT_TYPE,
            'resource': self.credentials.endpoint_resource
        }
        data = dict()
        # Build a session object with some fault tolerance
        # Retry up to 10 times with increasing backoff time
        # up to 120 seconds.
        with requests.Session() as session:
            session.mount(
                self.credentials.endpoints_active_directory,
                requests.adapters.HTTPAdapter(
                    max_retries=urllib3.util.Retry(
                        total=10,
                        backoff_factor=0.4,
                        status_forcelist=[500, 501, 502, 503, 504]
                    )))
            # Make the request
            res = session.post('{0}/{1}/oauth2/token'.format(
                self.credentials.endpoints_active_directory,
                self.credentials.tenant_id
            ), data=payload)
            # Expecting valid JSON response
            try:
                if res.text:
                    data = res.json()
                    if not isinstance(data, dict):
                        raise exceptions.UnexpectedResponse(
                            'Expected response data of type JSON object')
            except ValueError:
                raise exceptions.UnexpectedResponse(
                    'Malformed, non-JSON response data')
        # Check for 401 Unauthorized
        if res.status_code == 401:
            # We received an explicit credentials rejection
            if data and 'error' in data and data['error'] == 'invalid_client':
                raise exceptions.InvalidCredentials(
                    'Azure rejected the provided credentials', data)
            # All other rejection reason will be caught here
            raise exceptions.UnauthorizedRequest(data)
        # Expecting HTTP/1.1 200 OK
        if res.status_code != httplib.OK:
            raise exceptions.UnexpectedResponse(
                'Bad response status code: {0}'
                .format(res.status_code))
        # Expecting an access_token object
        if not data or 'access_token' not in data:
            raise exceptions.UnexpectedResponse(
                'Access token not present in response', data)
        return data
