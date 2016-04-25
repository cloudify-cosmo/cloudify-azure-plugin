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

# Azure SDK
from azure.mgmt.compute import (
    ComputeManagementClient,
    ComputeManagementClientConfiguration
)

from azure.mgmt.network import (
    NetworkManagementClient,
    NetworkManagementClientConfiguration
)

from azure.mgmt.storage import (
    StorageManagementClient,
    StorageManagementClientConfiguration
)

from azure.mgmt.resource.resources import (
    ResourceManagementClient,
    ResourceManagementClientConfiguration
)

# Cloudify System Tests
from cosmo_tester.framework.handlers import (
    BaseHandler,
    BaseCloudifyInputsConfigReader
)


SERVER = 'virtualmachine'
NETWORK = 'virtualnetwork'
SECURITY_GROUP = 'networksecuritygroup'
ADDRESS = 'publicipaddress'


class AzureCleanupContext(BaseHandler.CleanupContext):
    def __init__(self, context_name, env):
        super(AzureCleanupContext, self).__init__(context_name, env)
        self.before_run = self.env.handler.azure_infra_state()

    @classmethod
    def clean_resources(cls, env, resources):

        cls.logger.info('Performing cleanup: will try removing these '
                        'resources: {0}'
                        .format(resources))

        failed_to_remove = {}

        for segment in range(6):
            failed_to_remove = \
                env.handler.re(resources)
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
        return self.env.handler.azure_infra_state_delta(
            before=self.before_run, after=current_state)

    @classmethod
    def clean_all(cls, env):
        resources_to_be_removed = env.handler.azure_infra_state()
        cls.logger.info(
            "Current resources in account:"
            " {0}".format(resources_to_be_removed))
        # if env.use_existing_manager_keypair:
        #     resources_to_be_removed[KEYPAIR].pop(
        #         env.management_keypair_name, None)
        # if env.use_existing_agent_keypair:
        #     resources_to_be_removed[KEYPAIR].pop(env.agent_keypair_name,
        #                                              None)

        failed_to_remove = cls.clean_resources(env, resources_to_be_removed)

        errorflag = not (
            (len(failed_to_remove[SERVER]) == 0) and
            # (len(failed_to_remove[KEYPAIR]) == 0) and
            (len(failed_to_remove[ADDRESS]) == 0) and
            (len(failed_to_remove[SECURITY_GROUP]) == 0) and
            (len(failed_to_remove[NETWORK]) == 0))
        if errorflag:
            raise Exception(
                "Unable to clean up Environment, "
                "resources remaining: {0}".format(failed_to_remove))


class CloudifyAzureInputsConfigReader(BaseCloudifyInputsConfigReader):

    @property
    def azure_subscription_id(self):
        return self.config['subscription_id']

    @property
    def azure_credentials(self):
        return self.config['credentials']

    @property
    def management_user_name(self):
        return self.config['ssh_user']

    @property
    def agent_key_path(self):
        return self.config['agent_private_key_path']

    @property
    def management_key_path(self):
        return self.config['ssh_key_filename']

    @property
    def agent_keypair_name(self):
        return self.config['agent_keypair_name']

    @property
    def management_keypair_name(self):
        return self.config['manager_keypair_name']

    @property
    def use_existing_manager_keypair(self):
        return self.config['use_existing_manager_keypair']

    @property
    def use_existing_agent_keypair(self):
        return self.config['use_existing_agent_keypair']


class AzureHandler(BaseHandler):
    CleanupContext = AzureCleanupContext
    CloudifyConfigReader = CloudifyAzureInputsConfigReader

    def azure_compute_client(self):
        return ComputeManagementClient(
            ComputeManagementClientConfiguration(
                self.env.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def azure_network_client(self):
        return NetworkManagementClient(
            NetworkManagementClientConfiguration(
                self.env.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def azure_storage_client(self):
        return StorageManagementClient(
            StorageManagementClientConfiguration(
                self.env.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def azure_resource_client(self):
        return ResourceManagementClient(
            ResourceManagementClientConfiguration(
                self.env.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def _all_resource_groups(self, client):
        return client.resource_groups.list()

    def _all_storage_accounts(self, client):
        return client.storage_accounts.list()

    def _all_virtual_networks(self, client):
        return client.virtual_networks.list_all()

    def _all_subnets(self, client, resource_group_name, network_name):
        return client.subnets.list(resource_group_name, network_name)

    def _all_network_security_groups(self, client):
        return client.network_security_groups.list_all()

    def _all_network_security_groups_in_resource_group(self, client, resource_group_name):
        return client.network_security_groups.list(resource_group_name)

    def _all_security_rules_in_network_security_group(self, client, resource_group_name, network_security_group_name):
        return client.security_rules.list(resource_group_name, network_security_group_name)

    def _all_virtual_network_interfaces(self, client):
        return client.network_interfaces.list_all()

    def _all_virtual_network_interfaces_in_resource_group(self, client, resource_group_name):
        return client.network_interfaces.list(resource_group_name)

    def _all_load_balancers(self, client):
        return client.load_balancers.list_all()

    def _all_load_balancers_in_resource_group(self, client, resource_group_name):
        return client.load_balancers.list(resource_group_name)

    def _all_route_tables(self, client):
        return client.route_tables.list_all()

    def _all_routes(self, client, resource_group_name, route_table_name):
        return client.routes.list(resource_group_name, route_table_name)

    def _all_public_ip_addresses(self, client):
        return client.public_ip_addresses.list_all()

    def _all_public_ip_addresses_in_resource_group(self, client, resource_group_name):
        return client.public_ip_addresses.list(resource_group_name)

    def _all_virtual_machines(self, client):
        return client.virtual_machines.list_all()

    def azure_infra_state(self):
        raise NotImplementedError

    def azure_infra_state_delta(self, before, after):
        raise NotImplementedError

    def remove_azure_resources(self, resources_to_remove):
        raise NotImplementedError

handler = AzureHandler
