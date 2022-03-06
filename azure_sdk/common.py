# #######
# Copyright (c) 2020 - 2022 Cloudify Platform Ltd. All rights reserved
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

from os import path, environ

from azure.identity import DefaultAzureCredential
from azure.common.credentials import ServicePrincipalCredentials
from msrestazure.azure_active_directory import UserPassCredentials
from msrestazure.azure_cloud import AZURE_CHINA_CLOUD, AZURE_PUBLIC_CLOUD

from cloudify_azure import constants, utils
from cloudify_azure._compat import SafeConfigParser
from cloudify.exceptions import NonRecoverableError


class AzureResource(object):

    def __init__(self, azure_config):
        self.creds = self.handle_credentials(azure_config)
        azure_config_env_vars = azure_config.get('environment_variables')

        if self.creds.get("china"):
            self.creds['cloud_environment'] = AZURE_CHINA_CLOUD
        else:
            self.creds['cloud_environment'] = AZURE_PUBLIC_CLOUD

        subscription_id = azure_config.get("subscription_id") or \
                          azure_config_env_vars.get(
                              'AZURE_SUBSCRIPTION_ID')

        if azure_config_env_vars:
            for k, v in azure_config_env_vars.items():
                environ[k] = v
            self.credentials = DefaultAzureCredential()
        else:
            resource_default = 'https://management.core.windows.net/'

            # Traditional method
            client_id = self.creds.get('client_id')
            secret = self.creds.get('secret')
            tenant_id = self.creds.get('tenant_id')
            verify = self.creds.get("endpoint_verify", True)
            cloud_environment = self.creds.get("cloud_environment")
            endpoint_resource = self.creds.get(
                "endpoint_resource", resource_default)

            # AAD Method
            username = self.creds.get('username')
            password = self.creds.get('password')

            if username and password:
                self.credentials = UserPassCredentials(
                    username, password, client_id=client_id, secret=secret)
            else:
                self.credentials = ServicePrincipalCredentials(
                    client_id=client_id,
                    secret=secret,
                    tenant=tenant_id,
                    resource=endpoint_resource,
                    cloud_environment=cloud_environment,
                    verify=verify,
                )

        if not subscription_id:
            raise NonRecoverableError(
                'The subscription ID should either be provided in the '
                'client_config as subscription_id or '
                'in the environment_variables dict as AZURE_SUBSCRIPTION_ID.'
            )

        self.subscription_id = subscription_id
        self._client = None

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value

    def handle_credentials(self, azure_config):
        """
            Gets any Azure API access information from the
            current node properties or a provider context
            file created during manager bootstrapping.
        :returns: Azure credentials and access information
        :rtype: dict
        """
        def get_credentials_from_file(config_path=constants.CONFIG_PATH):
            """
                Gets Azure API access information from
                the provider context config file
            :returns: Azure credentials and access information
            :rtype: dict
            """
            cred_keys = [
                'client_id', 'client_secret', 'subscription_id', 'tenant_id',
                'endpoint_resource', 'endpoint_verify',
                'endpoints_resource_manager', 'endpoints_active_directory',
                'certificate', 'thumbprint', 'cloud_environment'
            ]
            config = SafeConfigParser()
            config.read(config_path)
            return {k: config.get('Credentials', k) for k in cred_keys}

        f_creds = dict()
        f_config_path = environ.get(constants.CONFIG_PATH_ENV_VAR_NAME,
                                    constants.CONFIG_PATH)
        if path.exists(f_config_path):
            f_creds = get_credentials_from_file(f_config_path)
        creds = utils.dict_update(f_creds, azure_config)
        if 'endpoint_verify' not in creds:
            creds['endpoint_verify'] = True
        return utils.cleanup_empty_params(creds)

    def get(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()
