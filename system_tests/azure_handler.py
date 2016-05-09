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
from contextlib import contextmanager

# Azure SDK
from azure.common.credentials import \
    ServicePrincipalCredentials

from azure.mgmt.resource.resources import (
    ResourceManagementClient,
    ResourceManagementClientConfiguration
)

from azure.mgmt.network import (
    NetworkManagementClient,
    NetworkManagementClientConfiguration
)

from azure.mgmt.compute import (
    ComputeManagementClient,
    ComputeManagementClientConfiguration
)

from azure.mgmt.storage import (
    StorageManagementClient,
    StorageManagementClientConfiguration
)


# Cloudify System Tests
from cosmo_tester.framework.handlers import (
    BaseHandler,
    BaseCloudifyInputsConfigReader
)

NAME = 'name'
RESOURCE_GROUP = 'resourcegroup'
COMPUTE = 'compute'
STORAGE = 'storage'
VIRTUAL_MACHINE = 'virtualmachine'
AVAILABILITY_SET = 'availability_set'
NETWORK = 'virtualnetwork'
SUBNET = 'subnet'
ROUTE_TABLE = 'routetable'
ROUTES = 'routes'
PUBLIC_IP_ADDRESS = 'publicipaddress'
SECURITY_GROUP = 'networksecuritygroup'
SECURITY_GROUP_RULE = 'networksecurityrule'
NETWORK_INTERFACE_CARD = 'networkinterfacecard'
LOAD_BALANCER = 'loadbalancer'
STORAGE_ACCOUNT = 'storageaccount'

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
            (len(failed_to_remove[VIRTUAL_MACHINE]) == 0) and
            (len(failed_to_remove[PUBLIC_IP_ADDRESS]) == 0) and
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
    def azure_tenant_id(self):
         return self.config['tenant_id']

    @property
    def azure_client_id(self):
        return self.config['client_id']

    @property
    def azure_client_secret(self):
        return self.config['client_secret']

    @property
    def azure_location(self):
        return self.config['azure_location']

    @property
    def manager_resource_group_name(self):
        return self.config['resource_group_name']

    @property
    def manager_virtual_network_name(self):
        return self.config['virtual_network_name']

    @property
    def manager_subnet_name(self):
        return self.config['subnet_name']

    def agents_security_group_name(self):
        return self.config['agents_security_group_name']

    @property
    def standard_a2_size(self):
        return self.config['standard_a2_size']

    @property
    def linux_os_family(self):
        return self.config['linux_os_family']

    @property
    def canonical_image_publisher(self):
        return self.config['canonical_image_publisher']

    @property
    def ubuntu_server_14_04_image_offer(self):
        return self.config['ubuntu_server_14_04_image_offer']

    @property
    def ubuntu_server_14_04_image_sku(self):
        return self.config['ubuntu_server_14_04_image_sku']

    @property
    def ubuntu_server_14_04_image_version(self):
        return self.config['ubuntu_server_14_04_image_version']

    @property
    def ubuntu_server_ubuntu_user(self):
        return self.config['ubuntu_server_ubuntu_user']

    @property
    def ubuntu_server_ubuntu_user_password(self):
        return self.config['ubuntu_server_ubuntu_user_password']

    @property
    def agent_public_key(self):
        return self.config['agent_public_key']



class AzureHandler(BaseHandler):
    CleanupContext = AzureCleanupContext
    CloudifyConfigReader = CloudifyAzureInputsConfigReader

    def azure_resource_client(self):
        return ResourceManagementClient(
            ResourceManagementClientConfiguration(
                self.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def azure_network_client(self):
        return NetworkManagementClient(
            NetworkManagementClientConfiguration(
                self.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def azure_compute_client(self):
        return ComputeManagementClient(
            ComputeManagementClientConfiguration(
                self.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def azure_storage_client(self):
        return StorageManagementClient(
            StorageManagementClientConfiguration(
                self.azure_credentials,
                self.env.azure_subscription_id
            )
        )

    def _all_resource_groups(self):
        return self.resource_client.resource_groups.list()

    def _all_resources_in_resource_group(self, resource_group_name):
        return self.resource_client.resource_groups.list_resources(resource_group_name)

    def _delete_resource_group(self, resource_group_name):
        return self.resource_client.resource_groups.delete(resource_group_name)

    def _all_virtual_networks(self, resource_group_name):
        return self.network_client.virtual_networks.list(resource_group_name)

    def _delete_virtual_network(self, resource_group_name, virtual_network_name):
        return self.network_client.virtual_networks.delete(resource_group_name, virtual_network_name)

    def _all_subnets(self, resource_group_name, network_name):
        return self.network_client.subnets.list(resource_group_name, network_name)

    def _delete_subnet(self, resource_group_name, virtual_network_name, subnet_name):
        return self.network_client.subnets.delete(resource_group_name, virtual_network_name, subnet_name)

    def _all_network_security_groups(self, resource_group_name):
        return self.network_client.network_security_groups.list(resource_group_name)

    def _delete_network_security_group(self, resource_group_name, network_security_group_name):
        return self.network_client.network_security_groups.delete(resource_group_name, network_security_group_name)

    def _all_security_rules_in_network_security_group(self, resource_group_name, network_security_group_name):
        return self.network_client.security_rules.list(resource_group_name, network_security_group_name)

    def _delete_security_rules(self, resource_group_name, network_security_group_name, security_rule_name):
        return self.network_client.security_rules.delete(resource_group_name, network_security_group_name, security_rule_name)

    def _all_virtual_network_interfaces(self, resource_group_name):
        return self.network_client.network_interfaces.list(resource_group_name)

    def _delete_virtual_network_interface(self, resource_group_name, network_interface_name):
        return self.network_client.network_interfaces.delete(resource_group_name, network_interface_name)

    def _all_load_balancers(self, resource_group_name):
        return self.network_client.load_balancers.list(resource_group_name)

    def _delete_load_balancer(self, resource_group_name, load_balancer_name):
        return self.network_client.load_balancers.delete(resource_group_name, load_balancer_name)

    def _all_route_tables(self, resource_group_name):
        return self.network_client.route_tables.list(resource_group_name)

    def _delete_route_table(self, resource_group_name, route_table_name):
        return self.network_client.route_tables.delete(resource_group_name, route_table_name)

    def _all_routes(self, resource_group_name, route_table_name):
        return self.network_client.routes.list(resource_group_name, route_table_name)

    def _delete_route(self, resource_group_name, route_table_name, route_name):
        return self.network_client.routes.delete(resource_group_name, route_table_name, route_name)

    def _all_public_ip_addresses_in_resource_group(self, resource_group_name):
        return self.network_client.public_ip_addresses.list(resource_group_name)

    def _delete_public_ip_addresses(self, resource_group_name, public_ip_address_name):
         return self.network_client.public_ip_addresses.delete(resource_group_name, public_ip_address_name)

    def _all_virtual_machines(self, resource_group_name):
        return self.compute_client.virtual_machines.list(resource_group_name)

    def _delete_virtual_machine(self, resource_group_name, vm_name):
        return self.compute_client.virtual_machines.delete(resource_group_name, vm_name)

    def _all_availability_sets(self, resource_group_name):
        return self.compute_client.availability_sets.list(resource_group_name)

    def _delete_availability_sets(self, resource_group_name, availability_set_name):
        return self.compute_client.availability_sets.delete(resource_group_name, availability_set_name)

    def _all_storage_accounts(self, resource_group_name):
        return self.storage_client.storage_accounts.list_by_resource_group(resource_group_name)

    def _delete_storage_account(self, resource_group_name, storage_account_name):
        return self.storage_client.storage_accounts.delete(resource_group_name, storage_account_name)

    def resource_group_infra_state(self):

        all_resource_groups = {}

        for resource_group in self._all_resource_groups():
            all_resource_groups.update(
                {
                    resource_group.name: {}
                }
            )

        return all_resource_groups

    def network_infra_state(self, resource_group_name):

        all_network = self.network_state_structure

        for virtual_network in self._all_virtual_networks(resource_group_name):
            all_network[NETWORK].update(
                {
                    virtual_network.name: {}
                }
            )

        for virtual_network in all_network[NETWORK].keys():
            subnets_in_network = self._all_subnets(resource_group_name, virtual_network)
            virtual_network[SUBNET] = subnets_in_network

        for route_table in self._all_route_tables(resource_group_name):
            all_network[ROUTE_TABLE].update(
                {
                    route_table.name: {}
                }
            )

        for route_table in all_network[ROUTE_TABLE].keys():
            routes_in_table = self._all_routes(resource_group_name, route_table)
            route_table[ROUTES] = routes_in_table

        for security_group in self._all_network_security_groups(resource_group_name):
            all_network[SECURITY_GROUP].update(
                {
                    security_group.name: {}
                }
            )

        for security_group in all_network[SECURITY_GROUP].keys():
            security_rules = self._all_security_rules_in_network_security_group(resource_group_name, security_group)
            security_group[SECURITY_GROUP_RULE] = security_rules

        for public_ip in self._all_public_ip_addresses_in_resource_group(resource_group_name):
            all_network[PUBLIC_IP_ADDRESS].append(public_ip.name)

        for network_card in self._all_virtual_network_interfaces(resource_group_name):
            all_network[NETWORK_INTERFACE_CARD].append(network_card.name)

        for load_balancer in self._all_load_balancers(resource_group_name):
            all_network[LOAD_BALANCER].append(load_balancer.name)

        return all_network

    def compute_infra_state(self, resource_group_name):

        all_compute = self.compute_state_structure

        for virtual_machine in self._all_virtual_machines(resource_group_name):
            all_compute[VIRTUAL_MACHINE].append(virtual_machine.name)

        for availability_set in self._all_availability_sets(resource_group_name):
            all_compute[AVAILABILITY_SET].append(availability_set.name)

        return all_compute

    def storage_infra_state(self, resource_group_name):

        all_storage = self.storage_state_structure

        for storage_account in self._all_storage_accounts(resource_group_name):
            all_storage[STORAGE_ACCOUNT].append(storage_account.name)

        return all_storage

    def azure_infra_state(self):

        current_state = dict()
        current_state.update(self.resource_group_infra_state())
        for resource_group_name in current_state[RESOURCE_GROUP]:
            intermediate_state = current_state.copy()
            intermediate_state.update(self.network_infra_state(resource_group_name))
            intermediate_state.update(self.compute_infra_state(resource_group_name))
            intermediate_state.update(self.storage_infra_state(resource_group_name))
            current_state = intermediate_state.copy()
        return current_state

    # TODO: Rewrite this to handle the more complex structure of multiple resource groups/types
    def azure_infra_state_delta(self, before, after):

        after = copy.deepcopy(after)

        return {
            prop: self._remove_keys(after[prop], before[prop].keys())
            for prop in before.keys()
        }

    def remove_azure_resources(self, resources_to_remove):

        current_state = self.azure_infra_state()
        failed = {}

        for resource_group_name in resources_to_remove.keys():
            current_resource = current_state.get(resource_group_name)

            if current_resource:

                for virtual_machine_name in current_resource[VIRTUAL_MACHINE]:
                    with self._handled_exception(virtual_machine_name, failed, VIRTUAL_MACHINE):
                        self._delete_virtual_machine(resource_group_name, virtual_machine_name)

                for availability_set_name in current_resource[AVAILABILITY_SET]:
                    with self._handled_exception(availability_set_name, failed, AVAILABILITY_SET):
                        self._delete_availability_sets(resource_group_name, availability_set_name)

                for storage_account_name in current_resource[STORAGE_ACCOUNT]:
                    with self._handled_exception(storage_account_name, failed, STORAGE_ACCOUNT):
                        self._delete_storage_account(resource_group_name, storage_account_name)

                for load_balancer_name in current_resource[LOAD_BALANCER]:
                    with self._handled_exception(load_balancer_name, failed, LOAD_BALANCER):
                        self._delete_load_balancer(resource_group_name, load_balancer_name)

                for network_interface_name in current_resource[NETWORK_INTERFACE_CARD]:
                    with self._handled_exception(network_interface_name, failed, NETWORK_INTERFACE_CARD):
                        self._delete_virtual_network_interface(resource_group_name, network_interface_name)

                for public_ip_address_name in current_resource[PUBLIC_IP_ADDRESS]:
                    with self._handled_exception(public_ip_address_name, failed, PUBLIC_IP_ADDRESS):
                        self._delete_public_ip_addresses(resource_group_name, public_ip_address_name)

                for security_group_name in current_resource[SECURITY_GROUP].keys():
                    security_group = current_resource[SECURITY_GROUP].get(security_group_name)
                    for security_group_rule in security_group.get(SECURITY_GROUP_RULE):
                        with self._handled_exception(security_group_rule, failed, SECURITY_GROUP_RULE):
                            self._delete_security_rules(resource_group_name, security_group_name, security_group_rule)
                    with self._handled_exception(security_group_name, failed, SECURITY_GROUP):
                        self._delete_network_security_group(resource_group_name, security_group_name)

                for route_table_name in current_resource[ROUTE_TABLE].keys():
                    route_table = current_resource[ROUTE_TABLE].get(route_table_name)
                    for route_name in route_table.get(ROUTES):
                        with self._handled_exception(route_name, failed, ROUTES):
                            self._delete_route(resource_group_name, route_table_name, route_name)
                    with self._handled_exception(route_table_name, failed, ROUTE_TABLE):
                        self._delete_route_table(resource_group_name, route_table_name)

                for virtual_network_name in current_resource[NETWORK].keys():
                    if virtual_network_name in resources_to_remove[resource_group_name][NETWORK]:
                        network = resources_to_remove[resource_group_name][NETWORK].get(virtual_network_name)
                        for subnet_name in network.get(SUBNET):
                            with self._handled_exception(subnet_name, failed, SUBNET):
                                self._delete_subnet(resource_group_name, virtual_network_name, subnet_name)
                        with self._handled_exception(virtual_network_name, failed, NETWORK):
                            self._delete_virtual_network(resource_group_name, virtual_network_name)

            with self._handled_exception(resource_group_name, failed, RESOURCE_GROUP):
                self._delete_resource_group(resource_group_name)

        return failed

    def _remove_keys(self, dct, keys):
        for key in keys:
            if key in dct:
                del dct[key]
        return dct

    @contextmanager
    def _handled_exception(self, resource_id, failed, resource_group):
        try:
            yield
        except BaseException, ex:
            failed[resource_group][resource_id] = ex

    @property
    def azure_credentials(self):
        return ServicePrincipalCredentials(
            client_id=self.env.azure_client_id,
            secret=self.env.azure_client_secret,
            tenant=self.env.azure_tenant_id
        )

    @property
    def resource_client(self):
        return self.azure_resource_client()

    @property
    def network_client(self):
        return self.azure_network_client()

    @property
    def compute_client(self):
        return self.azure_compute_client()

    @property
    def storage_client(self):
        return self.azure_storage_client()

    @property
    def network_state_structure(self):

        return {
            NETWORK: {},
            ROUTE_TABLE: {},
            PUBLIC_IP_ADDRESS: [],
            SECURITY_GROUP: {},
            NETWORK_INTERFACE_CARD: [],
            LOAD_BALANCER: []
        }

    @property
    def compute_state_structure(self):

        return {
            VIRTUAL_MACHINE: [],
            AVAILABILITY_SET: []
        }

    @property
    def storage_state_structure(self):
        return {
            STORAGE_ACCOUNT: []
        }

    @property
    def resources_state_structure(self):
        structure = {}
        structure.update(self.compute_state_structure)
        structure.update(self.network_state_structure)
        structure.update(self.storage_state_structure)
        return structure

handler = AzureHandler
