# #######
# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
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

import sys
from os import path, environ

from msrestazure.azure_cloud import AZURE_CHINA_CLOUD, AZURE_PUBLIC_CLOUD
from azure.common.credentials import ServicePrincipalCredentials
try:
    from cloudify._compat import SafeConfigParser
except ImportError:
    PY2 = sys.version_info[0] == 2
    if PY2:
        from ConfigParser import SafeConfigParser
    else:
        from configparser import SafeConfigParser

from cloudify_azure import (constants, utils)


class AzureResource(object):

    def __init__(self, azure_config):
        creds = self.handle_credentials(azure_config)
        if creds.get("china"):
            creds['cloud_environment'] = AZURE_CHINA_CLOUD
        else:
            creds['cloud_environment'] = AZURE_PUBLIC_CLOUD
        resource_default = 'https://management.core.windows.net/'
        self.credentials = ServicePrincipalCredentials(
            client_id=creds.get("client_id"),
            secret=creds.get("client_secret"),
            tenant=creds.get("tenant_id"),
            resource=creds.get("endpoint_resource", resource_default),
            cloud_environment=creds.get("cloud_environment"),
            verify=creds.get("endpoint_verify", True),
        )
        self.subscription_id = azure_config.get("subscription_id")
        self.client = None

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
