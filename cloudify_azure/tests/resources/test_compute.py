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
import requests

from cloudify import constants
from cloudify.state import current_ctx
from cloudify import mocks as cfy_mocks
from cloudify.exceptions import OperationRetry
from msrestazure.azure_exceptions import CloudError

from cloudify_azure import utils
from cloudify_azure.resources.compute import (availabilityset)
from cloudify_azure.resources.compute.virtualmachine import virtualmachine


def return_none(foo):
    return


@mock.patch('azure_sdk.common.ClientSecretCredential')
@mock.patch('azure_sdk.resources.compute.'
            'availability_set.ComputeManagementClient')
class AvailabilitySetTest(unittest.TestCase):

    def _get_mock_context_for_run(self, operation=None):
        operation = operation or {
            'name': 'cloudify.interfaces.lifecycle.create'}
        fake_ctx = cfy_mocks.MockCloudifyContext(operation=operation)
        instance = mock.Mock()
        instance.runtime_properties = {}
        instance.relationships = []
        fake_ctx._instance = instance
        node = mock.Mock()
        fake_ctx._node = node
        node.properties = {
            'use_external_resource': False,
            'create_if_missing': False,
            'use_if_exists': False,
        }
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

    def test_create(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockavailset'
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = name
        self.node.properties['location'] = 'eastus'
        self.node.properties['resource_config'] = {
            'platformUpdateDomainCount': 1,
            'platformFaultDomainCount': 2
        }
        availability_set_conf = {
            'location': self.node.properties.get('location'),
            'platform_update_domain_count': 1,
            'platform_fault_domain_count': 2
        }
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().availability_sets.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            availabilityset.create(ctx=self.fake_ctx)
            client().availability_sets.get.assert_called_with(
                resource_group_name=resource_group,
                availability_set_name=name
            )
            client().availability_sets.create_or_update.assert_called_with(
                resource_group_name=resource_group,
                availability_set_name=name,
                parameters=availability_set_conf
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockavailset'
        self.node.properties['use_external_resource'] = True
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = name
        self.node.properties['location'] = 'eastus'
        self.node.properties['resource_config'] = {
            'platformUpdateDomainCount': 1,
            'platformFaultDomainCount': 2
        }
        client().availability_sets.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            availabilityset.create(ctx=self.fake_ctx)
            client().availability_sets.get.assert_called_with(
                resource_group_name=resource_group,
                availability_set_name=name
            )
            client().availability_sets.create_or_update.assert_not_called()

    def test_delete(self, client, credentials):
        resource_group = 'sample_resource_group'
        name = 'mockavailset'
        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.delete'})
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        current_ctx.set(ctx=fake_ctx)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            availabilityset.delete(ctx=fake_ctx)
        client().availability_sets.delete.assert_called_with(
            resource_group_name=resource_group,
            availability_set_name=name)

    def test_delete_do_not_exist(self, client, credentials):
        resource_group = 'sample_resource_group'
        name = 'mockavailset'
        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.delete'})
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().availability_sets.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            availabilityset.delete(ctx=fake_ctx)
            client().availability_sets.delete.assert_not_called()


@mock.patch('azure_sdk.common.ClientSecretCredential')
@mock.patch('azure_sdk.resources.compute.'
            'virtual_machine.ComputeManagementClient')
class VirtualMachineTest(unittest.TestCase):

    def _get_mock_context_for_run(self, operation=None):
        operation = operation or {
            'name': 'cloudify.interfaces.lifecycle.create'}
        fake_ctx = cfy_mocks.MockCloudifyContext(operation=operation)
        instance = mock.Mock()
        instance.runtime_properties = {}
        instance.relationships = {}
        fake_ctx._instance = instance
        node = mock.Mock()
        fake_ctx._node = node
        node.properties = {}
        node.type_hierarchy = []
        node.runtime_properties = {}
        node.type_hierarchy = ['ctx.nodes.Root', constants.COMPUTE_NODE_TYPE]
        fake_ctx.get_resource = mock.MagicMock(
            return_value=""
        )
        current_ctx.set(fake_ctx)
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

    @mock.patch('cloudify_azure.resources.compute.virtualmachine.'
                'virtualmachine.build_network_profile',
                side_effect=return_none)
    def test_create(self, _, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = name
        self.node.properties['location'] = 'eastus'
        self.node.properties['os_family'] = 'linux'
        self.node.properties['resource_config'] = {
            'hardwareProfile': {
                'vmSize': 'Standard_A2',
            },
            'storageProfile': {
                'imageReference': {
                    'publisher': 'Canonical',
                    'offer': 'UbuntuServer',
                    'sku': '14.04.4-LTS',
                    'version': '14.04.201604060'
                }
            },
            'osProfile': {
                'computerName': name,
                'adminUsername': 'cloudify',
                'adminPassword': 'Cl0ud1fy!',
                'linuxConfiguration': {
                    'ssh': {
                        'publicKeys': {
                            'path': '/home/cloudify/.ssh/authorized_keys',
                            'keyData': 'ssh-rsa AAAAA3----MOCK----aabbzz'
                        }
                    },
                    'disablePasswordAuthentication': True
                }
            }
        }
        storage_profile = {
            'os_disk': {
                'caching': 'ReadWrite',
                'vhd': {
                    'uri': 'http://None.blob./vhds/mockvm.vhd'
                },
                'name': 'mockvm',
                'create_option': 'FromImage'
            }
        }
        vm_params = {
            'location': self.node.properties.get('location'),
            'storageProfile': storage_profile,
        }
        vm_params = utils.handle_resource_config_params(
            vm_params,
            self.node.properties.get("resource_config")
        )
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().virtual_machines.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualmachine.create(ctx=self.fake_ctx)
            client().virtual_machines.get.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )
            client()\
                .virtual_machines.begin_create_or_update.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name,
                parameters=vm_params
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get("name"),
                name
            )
            self.assertEquals(
                self.fake_ctx.instance.runtime_properties.get(
                    "resource_group"),
                resource_group
            )

    def test_create_already_exists(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = name
        self.node.properties['use_external_resource'] = True
        self.node.properties['location'] = 'eastus'
        self.node.properties['os_family'] = 'linux'
        self.node.properties['resource_config'] = {
            'hardwareProfile': {
                'vmSize': 'Standard_A2',
            },
            'storageProfile': {
                'imageReference': {
                    'publisher': 'Canonical',
                    'offer': 'UbuntuServer',
                    'sku': '14.04.4-LTS',
                    'version': '14.04.201604060'
                }
            },
            'osProfile': {
                'computerName': name,
                'adminUsername': 'cloudify',
                'adminPassword': 'Cl0ud1fy!',
                'linuxConfiguration': {
                    'ssh': {
                        'publicKeys': {
                            'path': '/home/cloudify/.ssh/authorized_keys',
                            'keyData': 'ssh-rsa AAAAA3----MOCK----aabbzz'
                        }
                    },
                    'disablePasswordAuthentication': True
                }
            }
        }
        client().virtual_machines.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualmachine.create(ctx=self.fake_ctx)
            client().virtual_machines.get.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )
            # client().virtual_machines.create_or_update.assert_not_called()

    def test_create_with_external_resource(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        self.node.properties['resource_group_name'] = resource_group
        self.node.properties['name'] = name
        self.node.properties['location'] = 'eastus'
        self.node.properties['os_family'] = 'linux'
        self.node.properties['resource_config'] = {
            'hardwareProfile': {
                'vmSize': 'Standard_A2'
            },
            'storageProfile': {
                'imageReference': {
                    'publisher': 'Canonical',
                    'offer': 'UbuntuServer',
                    'sku': '14.04.4-LTS',
                    'version': '14.04.201604060'
                }
            },
            'osProfile': {
                'computerName': name,
                'adminUsername': 'cloudify',
                'adminPassword': 'Cl0ud1fy!',
                'linuxConfiguration': {
                    'ssh': {
                        'publicKeys': {
                            'path': '/home/cloudify/.ssh/authorized_keys',
                            'keyData': 'ssh-rsa AAAAA3----MOCK----aabbzz'
                        }
                    },
                    'disablePasswordAuthentication': True
                }
            }
        }
        self.node.properties['use_external_resource'] = True
        client().virtual_machines.get.return_value = mock.Mock()
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualmachine.create(ctx=self.fake_ctx)
            client().virtual_machines.get.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )
            client()\
                .virtual_machines.begin_create_or_update.assert_not_called()

    def test_delete(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.delete'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualmachine.delete(ctx=fake_ctx)
            client().virtual_machines.begin_delete.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )

    def test_delete_do_not_exist(self, client, credentials):
        self.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        self.instance.runtime_properties['resource_group'] = resource_group
        self.instance.runtime_properties['name'] = name
        response = requests.Response()
        response.status_code = 404
        message = 'resource not found'
        client().virtual_machines.get.side_effect = \
            CloudError(response, message)
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualmachine.delete(ctx=self.fake_ctx)
            client().virtual_machines.begin_delete.assert_not_called()

    def test_start(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.start'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            response = mock.MagicMock()
            response.status_code = 200
            message = {
                'instance_view': {'statuses': [{'code': 'PowerState/stopped'}]}
            }
            response.as_dict.return_value = message
            client().virtual_machines.get.return_value = response
            with self.assertRaisesRegexp(
                    OperationRetry, 'Waiting for PowerState/running status'):
                virtualmachine.start(
                    command_to_execute='', file_uris=[], ctx=fake_ctx)
            client().virtual_machines.begin_start.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )

    def test_start_started(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.start'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            response = mock.MagicMock()
            response.status_code = 200
            message = {
                'instance_view': {'statuses': [{'code': 'PowerState/running'}]}
            }
            response.as_dict.return_value = message
            client().virtual_machines.get.return_value = response
            virtualmachine.start(
                command_to_execute='', file_uris=[], ctx=fake_ctx)
            client().virtual_machines.begin_start.assert_not_called()

    def test_stopped(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.stop'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        response = mock.MagicMock()
        response.status_code = 200
        message = {
            'instance_view': {'statuses': [{'code': 'PowerState/deallocated'}]}
        }
        response.as_dict.return_value = message
        client().virtual_machines.get.return_value = response
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            virtualmachine.stop(ctx=fake_ctx)
            client().virtual_machines.begin_power_off.assert_not_called()

    def test_stop(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.lifecycle.stop'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        response = mock.MagicMock()
        response.status_code = 200
        message = {
            'instance_view': {'statuses': [{'code': 'PowerState/running'}]}}
        response.as_dict.return_value = message
        client().virtual_machines.get.return_value = response
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            with self.assertRaisesRegexp(
                    OperationRetry,
                    'Waiting for {} PowerState/deallocated status'.format(name)
            ):
                virtualmachine.stop(
                    command_to_execute='', file_uris=[], ctx=fake_ctx)
            client().virtual_machines.begin_power_off.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )

    def test_restart(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.operations.restart'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            response = mock.MagicMock()
            response.status_code = 200
            client().virtual_machines.get.return_value = response
            virtualmachine.restart(ctx=fake_ctx)
            client().virtual_machines.begin_restart.assert_called_with(
                resource_group_name=resource_group,
                vm_name=name
            )

    def test_resize(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.operations.resize'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        vm_size = 'Standard_B2s'
        params = {
            'location': self.node.properties.get('location'),
            'hardware_profile': {
                'vm_size': vm_size
            }
        }
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            response = mock.MagicMock()
            response.status_code = 200
            client().virtual_machines.get.return_value = response
            virtualmachine.resize(vm_size=vm_size, ctx=fake_ctx)
            client().virtual_machines.begin_create_or_update \
                .assert_called_with(
                    resource_group_name=resource_group,
                    vm_name=name,
                    parameters=params
                )

    def test_run_command(self, client, credentials):

        fake_ctx, _, __ = self._get_mock_context_for_run(
            operation={'name': 'cloudify.interfaces.operations.run_command'})
        fake_ctx.node.properties['azure_config'] = self.dummy_azure_credentials
        resource_group = 'sample_resource_group'
        name = 'mockvm'
        params = {
            'command_id': 'RunShellScript',
            'script': ['echo "test"'],
            'parameters': []
        }
        fake_ctx.instance.runtime_properties['resource_group'] = resource_group
        fake_ctx.instance.runtime_properties['name'] = name
        with mock.patch('cloudify_azure.utils.secure_logging_content',
                        mock.Mock()):
            response = mock.MagicMock()
            response.status_code = 200
            client().virtual_machines.get.return_value = response
            virtualmachine.run_command(ctx=fake_ctx,
                                       command_id=params.get('command_id'),
                                       script=params.get('script'),
                                       params=params.get('parameters'))
            client().virtual_machines.begin_run_command \
                .assert_called_with(
                    resource_group_name=resource_group,
                    vm_name=name,
                    parameters=params
                )
