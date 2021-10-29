# Copyright (c) 2015-2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock
import unittest
from copy import deepcopy

from cloudify.state import current_ctx
from cloudify import mocks as cfy_mocks

from cloudify_azure.resources.compute.virtualmachine.virtualmachine_utils \
    import (ordered,
            diff_dictionaries,
            check_if_configuration_changed)


class VirtualMachineTest(unittest.TestCase):

    def _get_mock_context_for_run(self):
        operation = {'name': 'cloudify.interfaces.lifecycle.create'}
        fake_ctx = cfy_mocks.MockCloudifyContext(operation=operation)
        instance = mock.Mock()
        instance.runtime_properties = {}
        fake_ctx._instance = instance
        node = mock.Mock()
        fake_ctx._node = node
        node.properties = {}
        node.runtime_properties = {}
        node.type_hierarchy = ['ctx.nodes.Root']
        fake_ctx.get_resource = mock.MagicMock(
            return_value=""
        )
        return fake_ctx, node, instance

    def setUp(self):
        self.fake_ctx, self.node, self.instance = \
            self._get_mock_context_for_run()
        self.dummy_azure_credentials = {
            'client_id': 'dummy',
            'client_secret': 'dummy',
            'subscription_id': 'dummy',
            'tenant_id': 'dummy'
        }
        current_ctx.set(self.fake_ctx)
        self.update_vm_config = {
            'location': 'eastus2',
            'tags': {'a': 'b', 'c': 'd'},
            'availability_set': {
                'id':
                    '/subscriptions/cfyinfraavailset1'},
            'storage_profile': {'os_disk': {'name': 'demovm',
                                            'vhd': {
                                                'uri':
                                                    'http://demostorageaccount'
                                                    '.blob.core.windows.net/'
                                                    'vhds/demovm.vhd'},
                                            'caching': 'ReadWrite',
                                            'create_option':
                                                'FromImage'},
                                'image_reference': {
                                    'publisher': 'OpenLogic',
                                    'offer': 'CentOS',
                                    'sku': 7.6,
                                    'version': 'latest'}},
            'os_profile': {'computer_name': 'demovm',
                           'admin_username': 'centos',
                           'linux_configuration': {'ssh': {
                               'public_keys': [{
                                   'key_data': 'ssh-rsa demokey',
                                   'path':
                                       '/home/centos/.ssh/authorized_keys'}]},
                               'disable_password_authentication': True}},
            'hardware_profile': {'vm_size': 'Standard_B1s'}}

    def test_ordered_simple_dict(self):
        dict_a = {'a': 1, 'b': 2}
        dict_b = {'b': 2, 'a': 1}
        self.assertEquals(ordered(dict_a), ordered(dict_b))

    def test_ordered_dict_with_list(self):
        dict_a = {'a': [1, 2, 3]}
        dict_b = {'a': [3, 2, 1]}
        self.assertNotEquals(dict_a, dict_b)
        self.assertEquals(ordered(dict_a), ordered(dict_b))

    def test_ordered_recursive_integers_to_str(self):
        dict_a = {'a': {'b': '2', 'c': '3'}}
        dict_b = {'a': {'c': 3, 'b': 2}}
        self.assertNotEquals(dict_a, dict_b)
        self.assertEquals(ordered(dict_a), ordered(dict_b))

    def test_ordered_recursive_list_in_list(self):
        dict_a = {'a': [[1, 2, 3], [4, 5, 6]]}
        dict_b = {'a': [[5, 4, 6], [2, 1, 3]]}
        self.assertNotEquals(dict_a, dict_b)
        self.assertEquals(ordered(dict_a), ordered(dict_b))

    def test_diff_dictionaries(self):
        update_conf = {'a': {'b': 2}}
        current_conf = {'a': {'b': 2}}
        self.assertEquals(diff_dictionaries(update_conf, current_conf), False)

    def test_diff_dictionaries_current_conf_has_more_fields(self):
        update_conf = {'a': {'b': 2}}
        current_conf = {'a': {'b': 2, 'c': 3}}
        self.assertEquals(diff_dictionaries(update_conf, current_conf), False)

    def test_diff_dictionaries_update_conf_has_more_fields(self):
        update_conf = {'a': {'b': 2}, 'c': 3}
        current_conf = {'a': {'b': 2}}
        self.assertEquals(diff_dictionaries(update_conf, current_conf),
                          True)

    def test_diff_dictionaries_update_conf_has_more_fields_recursive(self):
        update_conf = {'a': {'b': {'c': {'d': 4, 'e': 5}}}}
        current_conf = {'a': {'b': {'c': {'d': 4}}}}
        self.assertEquals(diff_dictionaries(update_conf, current_conf),
                          True)

    def test_diff_dictionaries_with_list(self):
        update_conf = {'a': {'b': [1, 2, 3]}}
        current_conf = {'a': {'b': [3, 2, 1]}}
        self.assertEquals(diff_dictionaries(update_conf, current_conf),
                          False)

    def test_if_configuration_changed_same_conf(self):
        self.assertEquals(
            check_if_configuration_changed(self.fake_ctx,
                                           self.update_vm_config,
                                           self.update_vm_config), False)

    def test_check_if_configuration_changed_same_conf(self):
        self.assertEquals(
            check_if_configuration_changed(self.fake_ctx,
                                           self.update_vm_config,
                                           self.update_vm_config), False)

    def test_configuration_not_changed_more_elements_in_current_conf(self):
        current_conf = deepcopy(self.update_vm_config)
        current_conf['storage_profile']['os_disk']['disk_size_gb'] = 30
        current_conf['id'] = 'foo'
        self.assertEquals(check_if_configuration_changed(self.fake_ctx,
                                                         self.update_vm_config,
                                                         current_conf), False)

    def test_configuration_changed(self):
        current_conf = deepcopy(self.update_vm_config)
        self.update_vm_config['availability_set']['id'] = 'foo'
        self.assertEquals(check_if_configuration_changed(self.fake_ctx,
                                                         self.update_vm_config,
                                                         current_conf), True)

    def test_configuration_changed_deep(self):
        current_conf = deepcopy(self.update_vm_config)
        self.update_vm_config['os_profile']['linux_configuration'][
            'disable_password_authentication'] = False
        self.assertEquals(check_if_configuration_changed(self.fake_ctx,
                                                         self.update_vm_config,
                                                         current_conf), True)
