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

import copy
import string
from random import choice
from contextlib import contextmanager

# Cloudify System Tests
from cosmo_tester.framework.handlers import (
    BaseHandler,
    BaseCloudifyInputsConfigReader
)

API_VERSION = '2016-03-30'
STORAGE_API_VERSION = '2015-06-15'
DELETING = 'Deleting'


class AzureCleanupContext(BaseHandler.CleanupContext):

    def __init__(self, context_name, env):
        super(AzureCleanupContext, self).__init__(context_name, env)
        self.before_run = self.env.handler.azure_infra_state()

    @classmethod
    def clean_resources(cls, env, resources):

        cls.logger.info('Performing cleanup: will try removing these '
                        'resources: {0}'.format(resources))

        failed_to_remove = {}

        for segment in range(3):
            failed_to_remove = \
                env.handler.remove_azure_resources(resources)
            if not failed_to_remove:
                break

        cls.logger.info('Leftover resources after cleanup: {0}'
                        .format(failed_to_remove))

        return failed_to_remove

    def cleanup(self):
        super(AzureCleanupContext, self).cleanup()

        resources_to_teardown = self.get_resources_to_teardown()

        if self.skip_cleanup:
            self.logger.warn('[{0}] SKIPPING cleanup: of the resources: {1}'
                             .format(self.context_name, resources_to_teardown))
            return

        self.clean_resources(self.env, resources_to_teardown)

    def get_resources_to_teardown(self):
        current_state = self.env.handler.azure_infra_state()
        self.logger.info('resources_to_teardown: {}'.format(current_state))
        return self.env.handler.azure_infra_state_delta(
            before=self.before_run, after=current_state)

    @classmethod
    def clean_all(cls, env):
        resources_to_be_removed = env.handler.azure_infra_state()
        cls.logger.info(
            "Current resources in account:"
            " {0}".format(resources_to_be_removed))

        failed_to_remove = cls.clean_resources(env, resources_to_be_removed)

        errorflag = not (
            len(failed_to_remove['resource_group']) == 0 and
            len(failed_to_remove['virtualNetworks']) == 0 and
            len(failed_to_remove['storageAccounts']) == 0 and
            len(failed_to_remove['publicIPAddresses']) == 0 and
            len(failed_to_remove['networkSecurityGroups']) == 0 and
            len(failed_to_remove['networkInterfaces']) == 0 and
            len(failed_to_remove['virtualMachines']) == 0 and
            len(failed_to_remove['routeTables']) == 0 and
            len(failed_to_remove['availabilitySets']) == 0
        )

        if errorflag:
            raise Exception(
                "Unable to clean up Environment, "
                "resources remaining: {0}".format(failed_to_remove))


class CloudifyAzureInputsConfigReader(BaseCloudifyInputsConfigReader):

    @property
    def resource_prefix(self):
        return self.config['resource_prefix']

    @property
    def resource_suffix(self):
        return self.config['resource_suffix']

    @property
    def subscription_id(self):
        return self.config['subscription_id']

    @property
    def tenant_id(self):
        return self.config['tenant_id']

    @property
    def client_id(self):
        return self.config['client_id']

    @property
    def client_secret(self):
        return self.config['client_secret']

    @property
    def location(self):
        return self.config['location']

    @property
    def retry_after(self):
        return self.config['retry_after']

    @property
    def agent_local_key_path(self):
        return self.config['agent_local_key_path']

    @property
    def ssh_key_filename(self):
        return self.config['ssh_key_filename']

    @property
    def keydata(self):
        return self.config['system_tests_shared_public']

    @property
    def standard_a2_size(self):
        return self.config['standard_a2_size']

    @property
    def linux_os_family(self):
        return self.config['linux_os_family']

    @property
    def username_ubuntu_trusty(self):
        return self.config['username_ubuntu_trusty']

    @property
    def image_publisher_ubuntu_trusty(self):
        return self.config['image_publisher_ubuntu_trusty']

    @property
    def image_offer_ubuntu_trusty(self):
        return self.config['image_offer_ubuntu_trusty']

    @property
    def image_sku_ubuntu_trusty(self):
        return self.config['image_sku_ubuntu_trusty']

    @property
    def image_version_ubuntu_trusty(self):
        return self.config['image_version_ubuntu_trusty']

    @property
    def username_centos_final(self):
        return self.config['username_centos_final']

    @property
    def image_publisher_centos_final(self):
        return self.config['image_publisher_centos_final']

    @property
    def image_offer_centos_final(self):
        return self.config['image_offer_centos_final']

    @property
    def image_sku_centos_final(self):
        return self.config['image_sku_centos_final']

    @property
    def image_version_centos_final(self):
        return self.config['image_version_centos_final']

    @property
    def username_windows(self):
        return self.config['username_windows']

    @property
    def os_family_windows(self):
        return self.config['os_family_windows']

    @property
    def image_publisher_windows(self):
        return self.config['image_publisher_windows']

    @property
    def image_offer_windows(self):
        return self.config['image_offer_windows']

    @property
    def image_sku_windows(self):
        return self.config['image_sku_windows']

    @property
    def image_version_windows(self):
        return self.config['image_version_windows']


class AzureHandler(BaseHandler):

    CleanupContext = AzureCleanupContext
    CloudifyConfigReader = CloudifyAzureInputsConfigReader

    def __init__(self, env):
        super(AzureHandler, self).__init__(env)

        def _password():
            while True:
                password = ''.join(choice(string.letters + string.digits)
                                   for _ in range(16))
                if not any(char.isdigit() for char in list(password)) \
                        or not any(char.isupper() for char in list(password))\
                        or not any(char.islower() for char in list(password)):
                    continue
                return password

        self.session_password = _password()

    @property
    def password(self):
        return self.session_password

    @property
    def azure_credentials(self):

        from azure.common.credentials import \
            ServicePrincipalCredentials

        return ServicePrincipalCredentials(
            client_id=self.env.client_id,
            secret=self.env.client_secret,
            tenant=self.env.tenant_id
        )

    @property
    def resource_client(self):

        from azure.mgmt.resource.resources import (
            ResourceManagementClient,
            ResourceManagementClientConfiguration
        )

        return ResourceManagementClient(
            ResourceManagementClientConfiguration(
                self.azure_credentials,
                self.env.subscription_id
            )
        )

    @property
    def network_client(self):

        from azure.mgmt.network import (
            NetworkManagementClient,
            NetworkManagementClientConfiguration
        )

        return NetworkManagementClient(
            NetworkManagementClientConfiguration(
                self.azure_credentials,
                self.env.subscription_id
            )
        )

    @property
    def compute_client(self):

        from azure.mgmt.compute import (
            ComputeManagementClient,
            ComputeManagementClientConfiguration
        )

        return ComputeManagementClient(
            ComputeManagementClientConfiguration(
                self.azure_credentials,
                self.env.subscription_id
            )
        )

    @property
    def storage_client(self):

        from azure.mgmt.storage import (
            StorageManagementClient,
            StorageManagementClientConfiguration
        )

        return StorageManagementClient(
            StorageManagementClientConfiguration(
                self.azure_credentials,
                self.env.subscription_id
            )
        )

    def _all_resources(self):
        all_resource_groups = self.resource_client.resource_groups.list()
        all_resources = self.resource_client.resources.list(
            filter="location eq '{0}'".format(self.env.location))
        not_deleted_resources = {}
        for r in all_resources:
            try:
                _blank, _sub, sub_id, _rg, rg_name, _pvd, \
                    pvd_name, r_type, r_name = r.id.split('/')
            except ValueError:
                self.logger.info(
                    'Not registering this resource: {}'.format(r.id))
                continue
            rg = [rg for rg in all_resource_groups if rg_name in rg.name][0]
            if DELETING not in rg.properties.provisioning_state:
                not_deleted_resources.update(
                    {
                        r_name: {
                            'name': r_name,
                            'resource_group_name': rg_name,
                            'provider_namespace': pvd_name,
                            'type': r_type
                        }
                    })
        return not_deleted_resources

    def _delete_resource_group(self, resource_group_name):
        return self.resource_client.resource_groups.delete(resource_group_name)

    def _delete_resource(self, r):
        resource_group_name = r.get('resource_group_name')
        resource_provider_namespace = r.get('provider_namespace')
        resource_type = r.get('type')
        resource_name = r.get('name')
        api_version = \
            STORAGE_API_VERSION if 'storageAccounts' in \
                                   resource_type else API_VERSION
        return self.resource_client.resources.delete(
            resource_group_name=resource_group_name,
            resource_provider_namespace=resource_provider_namespace,
            parent_resource_path='',
            resource_type=resource_type,
            resource_name=resource_name,
            api_version=api_version
        )

    def azure_infra_state(self):

        current_state = dict()
        self.logger.info('infra current_state = {0}'.format(current_state))
        return current_state

    def azure_infra_state_delta(self, before, after):

        after = copy.deepcopy(after)

        delta = {}

        for prop in before.keys():
            try:
                value = self._remove_keys(after[prop], before[prop].keys())
            except KeyError as e:
                self.logger.info(
                    'Unable to remove resource due to error: {0}'.format(
                        str(e)
                    )
                )
                continue
            delta.update({prop: value})

        return delta

    def remove_azure_resources(self, resources_to_remove):

        current_state = self.azure_infra_state()

        failed = {
            'resource_group': {},
            'virtualNetworks': {},
            'storageAccounts': {},
            'publicIPAddresses': {},
            'networkSecurityGroups': {},
            'networkInterfaces': {},
            'virtualMachines': {},
            'routeTables': {},
            'availabilitySets': {}
        }

        for resource_name in resources_to_remove.keys():
            current_resource = current_state.get(resource_name)
            self.logger.info(
                'remove current_resource == {0}'.format(current_resource))
            if current_resource:
                name = current_resource.get('name')
                resource_type = current_resource.get('type')
                resource_group_name = current_resource.get(
                    'resource_group_name')
                with self._handled_exception(name, failed, resource_type):
                    self._delete_resource(current_resource)
                with self._handled_exception(
                        resource_group_name, failed, 'resource_group'):
                    self._delete_resource_group(resource_group_name)

        return failed

    def _remove_keys(self, dct, keys):
        for key in keys:
            if key in dct:
                del dct[key]
        return dct

    @contextmanager
    def _handled_exception(self, resource_name, failed, resource_type):
        try:
            yield
        except BaseException, ex:
            failed[resource_type][resource_name] = ex


handler = AzureHandler
