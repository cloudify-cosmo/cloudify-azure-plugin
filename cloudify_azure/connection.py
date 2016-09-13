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
    Connection
    ~~~~~~~~~~
    Microsoft Azure REST API connection helpers
'''

# Used for HTTP requests
import requests
# Used for parsing URL parameters
import urlparse
# Used to implement connection retrying
from requests.packages import urllib3
# Used for pretty-printing JSON
import json
# Constants, exceptions, logging
from cloudify_azure import (constants, exceptions, utils)
# Used to get a Azure access token
from cloudify_azure.auth.oauth2 import OAuth2
# Context
from cloudify import ctx


class AzureConnection(object):
    '''
        Connection handler for the Microsoft Azure REST API

    :param `logging.Logger` logger:
        Logger for the class to use. Defaults to `ctx.logger`
    '''
    def __init__(self, api_version=None, logger=None, _ctx=ctx):
        # Set the active context
        self.ctx = _ctx
        # Configure logger
        self.log = utils.create_child_logger(
            'connection',
            plogger=logger)
        # API version
        self.api_version = api_version
        # Get an access token for the session
        self.access_token = self.get_access_token()
        # Get a pre-configured requests.Session object
        self.session = self.get_session_connection()

    def __del__(self):
        # Clean up any Session connections
        if self.session:
            self.session.close()

    def request(self, **kwargs):
        '''
            Builds, and executes, a request to the
            Microsoft Azure API service.  The parameters
            are passed as-is (with one exception, see notes)
            to the underlying requests.Session.request() function.

        .. note::

           The *url* parameter should be passed in as a root path
           starting AFTER the base endpoint
           https://management.azure.com/subscriptions/{subscription-id}.
           For example, to send a request to provision a Resource Group,
           the URL parameter should be */resourcegroups/{rg-name}*.  Also,
           *api-version* request parameter will be added automatically if
           not provided.

           If a full URL is passed in (any string not starting with a
           forward slash), it will be passed as-is to the underlying
           request() function.

        :returns: A configured requests.Session instance
        :rtype: :class:`requests.Response`
        '''
        # Get current credentials
        creds = utils.get_credentials(_ctx=self.ctx)
        # Rework the URL
        url = kwargs.pop('url', '')
        # Check if this is a relative operation
        if url.startswith('/'):
            # Add the endpoint and subscription ID
            url = '{0}/subscriptions/{1}{2}'.format(
                constants.CONN_API_ENDPOINT,
                creds.subscription_id,
                url)
        kwargs['url'] = url
        # Update the params list with the api version
        url_params = urlparse.parse_qs(urlparse.urlparse(url).query)
        if not url_params.get('api-version'):
            params = kwargs.pop('params', dict())
            params['api-version'] = params.get('api-version', self.api_version)
            kwargs['params'] = params
        # Log the request details
        self.log.info('request({0})'.format(utils.secure_logging_content(
            kwargs)))
        res = self.session.request(**kwargs)
        # Only get data if there's data to be gotten
        data = None
        if res.text:
            data = res.json()
        self.log.debug('response: '
                       '(status={0}, data={1})'.format(
                           res.status_code,
                           json.dumps(data, indent=2)))
        # Check for 401 Unauthorized
        if res.status_code == 401:
            # We received an explicit credentials rejection
            if 'error' in data and data['error'] == 'invalid_client':
                raise exceptions.InvalidCredentials(
                    'Azure rejected the provided credentials', data)
            # All other rejection reason will be caught here
            raise exceptions.UnauthorizedRequest(data)
        return res

    def get_session_connection(self):
        '''
            Creates a `requests.Session` instance with
            an Azure API access token and includes basic
            connection fault tolerance.

        :returns: A configured requests.Session instance
        :rtype: :class:`requests.Session`
        '''
        # Build a session object with some fault tolerance
        # Retry up to 10 times with increasing backoff time
        # up to 120 seconds.
        session = requests.Session()
        session.mount(
            constants.CONN_API_ENDPOINT,
            requests.adapters.HTTPAdapter(
                max_retries=urllib3.util.Retry(
                    total=10,
                    backoff_factor=0.4,
                    status_forcelist=[500, 501, 502, 503, 504]
                )))
        # Set the Azure API access token for the session
        session.headers = {
            'Authorization': 'Bearer {0}'.format(
                self.access_token['access_token']),
            'Content-Type': 'application/json'
        }
        return session

    def get_access_token(self):
        '''
            Requests a new access token from the Azure
            authorization service

        :returns: An Azure API access token
        :rtype: string
        '''
        # Load the credentials
        creds = utils.get_credentials(_ctx=self.ctx)
        # Prepare the OAuth 2.0 client
        oauth2_client = OAuth2(creds, logger=self.log)
        # Retrieve an API access token
        return oauth2_client.request_access_token()
