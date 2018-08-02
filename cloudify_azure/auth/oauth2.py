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
from msrestazure.azure_active_directory import (
    AADMixin, BackendApplicationClient)
from requests import RequestException
from oauthlib.oauth2.rfc6749.errors import (
    InvalidGrantError,
    OAuth2Error)
from msrest.exceptions import AuthenticationError, raise_with_traceback
from azure.common.credentials import ServicePrincipalCredentials

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
     'endpoints_active_directory', 'client_assertion']
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
            'grant_type': constants.OAUTH2_GRANT_TYPE,
            'resource': self.credentials.endpoint_resource
        }
        if self.credentials.client_assertion:
            # this is certificate based authentication
            payload.update({
                'client_assertion_type': constants.OAUTH2_JWT_ASSERTION_TYPE,
                'client_assertion': self.credentials.client_assertion,
            })
        else:
            # this is shared secret authentication
            payload.update({
                'client_secret': self.credentials.client_secret,
            })
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


class ServicePrincipalCertificateAuth(AADMixin):
    """Credentials object for Service Principle Authentication.
    Authenticates via a Client ID and Client Assertion.

    Optional kwargs may include:

    - cloud_environment (msrestazure.azure_cloud.Cloud):
            A targeted cloud environment
    - china (bool): Configure auth for China-based service,
      default is 'False'.
    - tenant (str): Alternative tenant, default is 'common'.
    - auth_uri (str): Alternative authentication endpoint.
    - token_uri (str): Alternative token retrieval endpoint.
    - resource (str): Alternative authentication resource, default
      is 'https://management.core.windows.net/'.
    - verify (bool): Verify secure connection, default is 'True'.
    - keyring (str): Name of local token cache, default is 'AzureAAD'.
    - timeout (int): Timeout of the request in seconds.
    - cached (bool): If true, will not attempt to collect a token,
      which can then be populated later from a cached token.
    - proxies (dict): Dictionary mapping protocol or protocol and
      hostname to the URL of the proxy.

    :param str client_id: Client ID.
    :param str assertion: Client assertion.
    """
    def __init__(self, client_id, client_assertion, **kwargs):
        super(ServicePrincipalCertificateAuth, self).__init__(client_id, None)
        self._configure(**kwargs)

        self.client_assertion = client_assertion
        self.client = BackendApplicationClient(self.id)
        if not kwargs.get('cached'):
            self.set_token()

    @classmethod
    def retrieve_session(cls, client_id):
        """Create ServicePrincipalCredentials from a cached token if it has not
        yet expired.
        """
        session = cls(client_id, None, cached=True)
        session._retrieve_stored_token()
        return session

    def set_token(self):
        """Get token using Client ID/Assertion credentials.

        :raises: AuthenticationError if credentials invalid, or call fails.
        """
        with self._setup_session() as session:
            try:
                token = session.fetch_token(
                    self.token_uri,
                    client_id=self.id,
                    resource=self.resource,
                    client_assertion=self.client_assertion,
                    response_type="client_credentials",
                    client_assertion_type='urn:ietf:params:oauth:'
                                          'client-assertion-type:jwt-bearer',
                    verify=self.verify,
                    timeout=self.timeout,
                    proxies=self.proxies)
            except (RequestException, OAuth2Error, InvalidGrantError) as err:
                raise_with_traceback(AuthenticationError, "", err)
            else:
                self.token = token
                self._default_token_cache(self.token)


def to_service_principle_credentials(**kwargs):
    if 'client_assertion' in kwargs:
        return ServicePrincipalCertificateAuth(**kwargs)
    else:
        return ServicePrincipalCredentials(**kwargs)
