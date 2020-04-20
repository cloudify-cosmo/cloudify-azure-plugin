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
"""
    auth.OAuth2
    ~~~~~~~~~~~
    OAuth 2.0 authorization interface for the Microsoft Azure REST API
"""

# pylint: disable=R0903

import re
import jwt
import time
import uuid
import base64
import datetime
import requests
import binascii
import importlib
from collections import namedtuple

import adal
from adal.constants import Jwt
from requests.packages import urllib3

from msrestazure.azure_active_directory import AADMixin
from msrestazure.azure_cloud import (AZURE_PUBLIC_CLOUD, AZURE_CHINA_CLOUD)
from msrest.exceptions import AuthenticationError, raise_with_traceback
from azure.common.credentials import ServicePrincipalCredentials

from cloudify import ctx
from cloudify._compat import httplib
from cloudify.exceptions import NonRecoverableError

from cloudify_azure import \
    (constants, exceptions)


AzureCredentials = namedtuple(
    'AzureCredentials',
    ['tenant_id', 'client_id', 'client_secret', 'subscription_id',
     'endpoint_resource', 'endpoint_verify', 'endpoints_resource_manager',
     'endpoints_active_directory', 'certificate', 'thumbprint',
     'cloud_environment']
)


def generate_jwt_token(certificate, thumbprint, client_id, talent_id):
    x5t = base64.urlsafe_b64encode(
        binascii.a2b_hex(thumbprint)).decode()
    now = datetime.datetime.now()
    minutes = datetime.timedelta(0, 0, 0, 0, Jwt.SELF_SIGNED_JWT_LIFETIME)
    expires = now + minutes
    header = {
        'typ': 'JWT',
        'alg': 'RS256',
        'x5t': x5t
    }
    payload = {
        Jwt.AUDIENCE:
            "https://login.microsoftonline.com/{}/oauth2/token".format(
                talent_id),
        Jwt.EXPIRES_ON: int(time.mktime(expires.timetuple())),
        Jwt.ISSUER: client_id,
        Jwt.JWT_ID: '{0}'.format(uuid.uuid4()),
        Jwt.NOT_BEFORE: int(time.mktime(now.timetuple())),
        Jwt.SUBJECT: client_id
    }
    jwt_token = jwt.encode(
        payload, certificate, algorithm='RS256', headers=header).decode()
    return jwt_token


"""
    Microsoft Azure credentials and access information

:param string tenant_id: Azure tenant ID
:param string client_id: Azure client ID (AD username)
:param string client_secret: Azure client secret (AD password)
:param string subscription_id: Azure subscription ID
"""


class OAuth2(object):
    """
        OAuth 2.0 interface for the Microsoft Azure REST API

    :param `AzureCredentials` credentials:
        Azure credentials and access information
    :param `logging.Logger` logger:
        Logger for the class to use. Defaults to `ctx.logger`
    """

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
        """Tenant-specific access token request.

        .. note::

           This uses a separate requests.Session() object from
           the rest of the class methods.  This ensures the session
           data isn't polluting the request or response data.

        :returns: Access token information
        :rtype: dict
        :raises: :exc:`cloudify_azure.exceptions.UnauthorizedRequest`,
                 :exc:`cloudify_azure.exceptions.UnexpectedResponse`,
                 :exc:`requests.RequestException`
        """
        payload = {
            'client_id': self.credentials.client_id,
            'grant_type': constants.OAUTH2_GRANT_TYPE,
            'resource': self.credentials.endpoint_resource
        }
        if self.credentials.certificate and self.credentials.thumbprint:
            # this is certificate based authentication
            client_assertion = generate_jwt_token(
                self.credentials.certificate, self.credentials.thumbprint,
                self.credentials.client_id, self.credentials.tenant_id)
            payload.update({
                'client_assertion_type': constants.OAUTH2_JWT_ASSERTION_TYPE,
                'client_assertion': client_assertion,
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


class CustomAADMixin(object):
    VALID_CLOUD_ENVS = (
        'AZURE_PUBLIC_CLOUD',
        'AZURE_CHINA_CLOUD',
        'AZURE_US_GOV_CLOUD',
        'AZURE_GERMAN_CLOUD',
    )

    def _configure(self, **kwargs):
        """Configure authentication endpoint.

        Optional kwargs may include:

            - cloud_environment (msrestazure.azure_cloud.Cloud):
            A targeted cloud environment
            - china (bool): Configure auth for China-based service,
              default is 'False'.
            - tenant (str): Alternative tenant, default is 'common'.
            - resource (str): Alternative authentication resource, default
              is 'https://management.core.windows.net/'.
            - verify (bool): Verify secure connection, default is 'True'.
            - timeout (int): Timeout of the request in seconds.
            - proxies (dict): Dictionary mapping protocol or protocol and
              hostname to the URL of the proxy.
            - cache (adal.TokenCache): A adal.TokenCache,
              see ADAL configuration
              for details. This parameter is not used here and directly
              passed to ADAL.
        """
        def _import_cloud_cls(name):
            module = importlib.import_module('msrestazure.azure_cloud')
            env_cls = getattr(module, name)
            return env_cls

        self._endpoints_active_directory = None
        if kwargs.get('china'):
            err_msg = ("china parameter is deprecated, "
                       "please use "
                       "cloud_environment"
                       "=msrestazure.azure_cloud.AZURE_CHINA_CLOUD")
            ctx.logger.error(err_msg)
            self._cloud_environment = AZURE_CHINA_CLOUD
        else:
            self._cloud_environment = AZURE_PUBLIC_CLOUD

        # First check if the "cloud_environment" is specified by user so
        # that we can use it instead of the default cloud environment
        if kwargs.get('cloud_environment'):
            cloud_env = kwargs['cloud_environment']
            if cloud_env not in self.VALID_CLOUD_ENVS:
                raise NonRecoverableError(
                    'cloud_environment {0} is not '
                    'valid'.format(cloud_env))

            cloud_env_cls = _import_cloud_cls(cloud_env)
            self._cloud_environment = cloud_env_cls
        else:
            # Check to see if "endpoints_active_directory" is specified or not
            if kwargs.get('endpoints_active_directory'):
                self._endpoints_active_directory =\
                    kwargs['endpoints_active_directory']

        if self._endpoints_active_directory:
            auth_endpoint = self._endpoints_active_directory
        else:
            auth_endpoint = self._cloud_environment.endpoints.active_directory
        resource = \
            self._cloud_environment.endpoints.active_directory_resource_id

        self._tenant = kwargs.get('tenant', "common")
        self._verify = kwargs.get('verify')
        # 'None' will honor ADAL_PYTHON_SSL_NO_VERIFY
        self.resource = kwargs.get('resource', resource)
        self._proxies = kwargs.get('proxies')
        self._timeout = kwargs.get('timeout')
        self._cache = kwargs.get('cache')
        self.store_key = "{}_{}".format(
            auth_endpoint.strip('/'), self.store_key)
        self.secret = None
        self._context = None  # Future ADAL context

    def _create_adal_context(self):
        if self._endpoints_active_directory:
            authority_url = self._endpoints_active_directory
        else:
            authority_url = self.cloud_environment.endpoints.active_directory
        is_adfs = bool(re.match('.+(/adfs|/adfs/)$', authority_url, re.I))
        if is_adfs:
            authority_url = authority_url.rstrip('/')
            # workaround: ADAL is known to reject auth urls with trailing /
        else:
            authority_url = authority_url + '/' + self._tenant

        self._context = adal.AuthenticationContext(
            authority_url,
            timeout=self._timeout,
            verify_ssl=self._verify,
            proxies=self._proxies,
            validate_authority=not is_adfs,
            cache=self._cache,
            api_version=None
        )


class CustomServicePrincipalCredentials(CustomAADMixin,
                                        ServicePrincipalCredentials):
    pass


class ServicePrincipalCertificateAuth(CustomAADMixin, AADMixin):
    """Credentials object for Service Principle Authentication.
    Authenticates via a Client ID and Certificate.

    Optional kwargs may include:

    - cloud_environment (msrestazure.azure_cloud.Cloud):
                        A targeted cloud environment
    - china (bool): Configure auth for China-based service,
      default is 'False'.
    - tenant (str): Alternative tenant, default is 'common'.
    - resource (str): Alternative authentication resource, default
      is 'https://management.core.windows.net/'.
    - verify (bool): Verify secure connection, default is 'True'.
    - timeout (int): Timeout of the request in seconds.
    - proxies (dict): Dictionary mapping protocol or protocol and
      hostname to the URL of the proxy.
    - cache (adal.TokenCache): A adal.TokenCache, see ADAL configuration
    for details. This parameter is not used here and directly passed to ADAL.

    :param str client_id: Client ID.
    :param str certificate: Certificate private key part.
    :param str thumbprint: Certificate part thumbprint.
    """
    def __init__(self,
                 client_id,
                 certificate,
                 thumbprint,
                 **kwargs):

        super(ServicePrincipalCertificateAuth, self).__init__(client_id, None)
        self._configure(**kwargs)
        self.certificate = certificate
        self.thumbprint = thumbprint
        self.set_token()

    def set_token(self):
        """Get token using Client ID/Secret credentials.

        :raises: AuthenticationError if credentials invalid, or call fails.
        """
        super(ServicePrincipalCertificateAuth, self).set_token()
        try:
            token = self._context.acquire_token_with_client_certificate(
                self.resource,
                self.id,
                self.certificate,
                self.thumbprint,
                self.cloud_environment
            )
            self.token = self._convert_token(token)
        except adal.AdalError as err:
            raise_with_traceback(AuthenticationError, "", err)


def to_service_principle_credentials(**kwargs):
    for k, v in list(kwargs.items()):
        if not v:
            del kwargs[k]
    if 'certificate' in kwargs:
        return ServicePrincipalCertificateAuth(**kwargs)
    else:
        return CustomServicePrincipalCredentials(**kwargs)
