# #######
# Copyright (c) 2022 Cloudify Platform Ltd. All rights reserved
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

import logging
from mock import patch
from unittest import TestCase

from ..resources import custom


@patch('azure.mgmt.foo', create=True)
@patch('azure_sdk.common.ClientSecretCredential')
@patch('azure.mgmt.resource.ResourceManagementClient')
class TestCustom(TestCase):

    @staticmethod
    def get_logger(logger_name=None):
        logger_name = logger_name or 'unit_test_logger'
        return logging.getLogger(logger_name)

    def test_create(self, *_):
        init_params = {
            'azure_config': {
                'client_id': 'dummy',
                'client_secret': 'dummy',
                'subscription_id': 'dummy',
                'tenant_id': 'dummy'
            },
            'logger': self.get_logger(),
            'api_version': '2022-01-01',
            'custom_resource_module': 'azure.mgmt.foo',
            'custom_resource_class_name': 'FooBarManagementClient',
            'custom_resource_object_name': 'foo_bar',
            'create_fn_name': 'create',
            'update_fn_name': 'update',
            'delete_fn_name': 'delete',
            'get_fn_name': 'get',
            'get_params': {
                'name': 'baz'
            }
        }
        with self.assertRaises(custom.AzureCustomResourceError):
            custom.CustomAzureResource(**init_params)
        init_params.update({
            'api_version': '2017-05-10',
            'custom_resource_module': 'azure.mgmt.resource',
            'custom_resource_class_name': 'ResourceManagementClient',
            'custom_resource_object_name': 'resource_groups',
            'create_fn_name': 'create_or_update',
            'update_fn_name': 'create_or_update',
            'delete_fn_name': 'delete',
            'get_params': {'resource_group_name': 'foo'},
        })
        obj = custom.CustomAzureResource(**init_params)
        create_params = {
            'resource_group_name': 'bar',
            'parameters': {
                'location': 'up',
            }
        }
        obj.create(**create_params)
