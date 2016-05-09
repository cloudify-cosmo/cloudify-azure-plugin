########
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

from cosmo_tester.test_suites.test_blueprints import nodecellar_test

EXTERNAL_RESOURCE_ID = 'aws_resource_id'
WEBSERVER_PORT = '8080'
HOST_PUBLIC_IP = 'public_ip'

class AWSNodeCellarTest(nodecellar_test.NodecellarAppTest):

    def test_aws_nodecellar(self):
        self._test_nodecellar_impl('azure-blueprint.yaml')

    def get_inputs(self):

        return {
            'subscription_id': self.env.azure_subscription_id,
            'tenant_id': self.env.azure_tenant_id,
            'client_id': self.env.azure_client_id,
            'client_secret': self.env.azure_client_secret,
            'location': self.env.azure_location,
            'mgr_resource_group_name': self.env.manager_resource_group_name,
            'mgr_virtual_network_name': self.env.manager_virtual_network_name,
            'mgr_subnet_name': self.env.manager_subnet_name,
            'vm_size': self.env.standard_a2_size,
            'vm_os_family': self.env.linux_os_family,
            'vm_image_publisher': self.env.canonical_image_publisher,
            'vm_image_offer': self.env.ubuntu_server_14_04_image_offer,
            'vm_image_sku': self.env.ubuntu_server_14_04_image_sku,
            'vm_image_version': self.env.ubuntu_server_14_04_image_version,
            'agent_user': self.env.ubuntu_server_ubuntu_user,
            'vm_os_password': self.env.ubuntu_server_ubuntu_user_password,
            'vm_os_pubkeys': self.env.agent_public_key,
            'webserver_port': WEBSERVER_PORT
        }

    @property
    def host_expected_runtime_properties(self):
        return ['ip']

    @property
    def entrypoint_node_name(self):
        return 'nodejs_host'

    @property
    def entrypoint_property_name(self):
        return HOST_PUBLIC_IP

    @property
    def expected_nodes_count(self):
        return 16
