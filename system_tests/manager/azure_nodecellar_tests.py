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

HOST_PUBLIC_IP = 'public_ip'


class AzureNodeCellarTest(nodecellar_test.NodecellarAppTest):

    @property
    def repo_branch(self):
        return 'master'

    @property
    def host_expected_runtime_properties(self):
        return []

    @property
    def entrypoint_node_name(self):
        return 'nodejs_host'

    @property
    def entrypoint_property_name(self):
        return HOST_PUBLIC_IP

    @property
    def expected_nodes_count(self):
        return 16

    @property
    def short_test_id(self):
        bad_chars = [
            '`', '~', '!', '@', '#', '$', '%', '^', '&', '*',
            '(', ')', '=', '+', '_', '[', ']', '{', '}', '\\',
            '|', ';', ':', '.', '\'', ',', '<', '>', '/', '?', '-']
        id = self.test_id.translate(None, ''.join(bad_chars))
        id = id.replace('2016', '')
        id = id.replace('test', '')
        id = id.replace('local', '')
        return id.replace('system', '')

    def test_aws_nodecellar(self):
        self._test_nodecellar_impl('azure-blueprint.yaml')

    def get_inputs(self):

        return {
            'subscription_id': self.env.subscription_id,
            'tenant_id': self.env.tenant_id,
            'client_id': self.env.client_id,
            'client_secret': self.env.client_secret,
            'location': self.env.location,
            'resource_prefix': self.short_test_id,
            'resource_suffix': '',
            'mgr_resource_group_name': '{0}rg{1}'.format(
                self.env.resource_prefix, self.env.resource_suffix),
            'mgr_virtual_network_name': '{0}vnet{1}'.format(
                self.env.resource_prefix, self.env.resource_suffix),
            'mgr_subnet_name': '{0}subnet{1}'.format(
                self.env.resource_prefix, self.env.resource_suffix),
            'vm_size': self.env.standard_a2_size,
            'vm_os_family': self.env.os_family_linux,
            'vm_image_publisher': self.env.image_publisher_ubuntu_trusty,
            'vm_image_offer': self.env.image_offer_ubuntu_trusty,
            'vm_image_sku': self.env.image_sku_ubuntu_trusty,
            'vm_image_version': self.env.image_version_ubuntu_trusty,
            'vm_os_username': self.env.username_ubuntu_trusty,
            'vm_os_password': self.env.password,
            'vm_os_pubkeys': [
                {
                    'path': self.env.authorized_keys_ubuntu,
                    'keydata': self.env.keydata
                }
            ],
        }
