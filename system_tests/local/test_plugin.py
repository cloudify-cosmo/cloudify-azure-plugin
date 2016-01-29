########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

# Third Party
#from azurecloudify import azureclient

from azurecloudify import (
    resourcegroup,
    securitygroup,
    storageaccount,
    vnet,
    subnet,
    nic,
    publicip,
    constants
    auth
)

# Cloudify Imports
from cloudify.state import current_ctx
from cloudify.exceptions import NonRecoverableError



class TestWorkflowClean(AzureLocalTestUtils):

    def test_simple_resources(self):
        client = self._get_azure_client()

        test_name = 'test_simple_resources'

        inputs = self._get_inputs(test_name=test_name)
        self._set_up(inputs=inputs)

        # execute install workflow
        self.localenv.execute('install', task_retries=10)

        instance_storage = self._get_instances(self.localenv.storage)

        self.assertEquals(4, len(instance_storage))

        for node_instance in self._get_instances(self.localenv.storage):
            self.assertIn(EXTERNAL_RESOURCE_ID,
                          node_instance.runtime_properties)

        resource_group_node = \
            self._get_instance_node(
                SIMPLE_IP, self.localenv.storage)
        resource_group_address = \
            resource_group_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        resource_group_object_list = \
            client.get_all_addresses(addresses=resource_group_address)
        self.assertEqual(1, len(resource_group_object_list))

        security_group_node = \
            self._get_instance_node(SIMPLE_SG, self.localenv.storage)
        security_group_id = \
            security_group_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        security_group_object_list = \
            client.get_all_security_groups(group_ids=security_group_id)
        self.assertEqual(1, len(security_group_object_list))

        storage_account_node = \
            self._get_instance_node(SIMPLE_SA, self.localenv.storage)
        storage_account_name = \
            key_pair_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        storage_account_object_list = \
            client.get_all_key_pairs(keynames=storage_account_id)
        self.assertEqual(1, len(storage_account_object_list))
        
        vnet_node = \
            self._get_instance_node(SIMPLE_VNET, self.localenv.storage)
        vnet_name = \
            key_pair_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        vnet_object_list = \
            client.get_all_key_pairs(keynames=vnet_id)
        self.assertEqual(1, len(vnet_object_list))
        
        
        nic_node = \
            self._get_instance_node(SIMPLE_NIC, self.localenv.storage)
        nic_name = \
            nic_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        nic_object_list = \
            client.get_all_key_pairs(keynames=nic_id)
        self.assertEqual(1, len(nic_object_list))


        public_ip_node = \
            self._get_instance_node(SIMPLE_PIP, self.localenv.storage)
        public_ip_id = \
            public_ip_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        public_ip_object_list = \
            client.get_all_public_ip(group_ids=public_ip_id)
        self.assertEqual(1, len(public_ip_object_list))
    
    
        subnet_node = \
            self._get_instance_node(SIMPLE_SUBNET, self.localenv.storage)
        subnet_id = \
            public_ip_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        subnet_object_list = \
            client.get_all_subnet(group_ids=subnet_id)
        self.assertEqual(1, len(subnet_object_list))
        
        
        server_node = \
            self._get_instance_node(SIMPLE_VM, self.localenv.storage)
        server_id = \
            instance_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        reservation_list = \
            client.get_all_reservations(instance_ids=instance_id)
        instance_list = reservation_list[0].instances
        self.assertEqual(1, len(instance_list))
        
    
        self.localenv.execute('uninstall', task_retries=10)

        with self.assertRaises(AzureResponseError):
            client._get_public_ip_name(addresses=public_ip_address)
        with self.assertRaises(AzureResponseError):
            client._gesecurity_group_name(group_names=security_group_name)
        with self.assertRaises(AzureResponseError):
            client._get_all_resource_groups(group_names=resource_group_name)
        with self.assertRaises(AzureResponseError):
            client._get_resource_groups(group_names=resource_group_name)
        client.get_all_reservations(instance_ids=instance_id)
        instance_state = reservation_list[0].instances[0].update()
        self.assertIn('terminated', instance_state)

    def test_simple_relationships(self):

        client = self._get_azure_client()

        test_name = 'test_simple_relationships'

        inputs = self._get_inputs(test_name=test_name)

        self._set_up(
            inputs=inputs,
            filename='relationships-blueprint.yaml')

        # execute install workflow
        self.localenv.execute('install', task_retries=10)

        instance_storage = self._get_instances(self.localenv.storage)
        self.assertEquals(4, len(instance_storage))

        instance_node = \
            self._get_instance_node(PAIR_A_VM, self.localenv.storage)
        instance_id_a = \
            instance_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        reservation_list = \
            client.get_all_reservations(instance_ids=instance_id_a)
        instance_list_ip = reservation_list[0].instances

        self.assertEquals(4, len(instance_storage))
        elastic_ip_node = \
            self._get_instance_node(
                PAIR_A_IP, self.localenv.storage)
        elastic_ip_address = \
            elastic_ip_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        elastic_ip_object_list = \
            client.get_all_addresses(addresses=elastic_ip_address)

        self.assertEqual(
            str(elastic_ip_object_list[0].instance_id),
            str(instance_list_ip[0].id))

        instance_node = \
            self._get_instance_node(PAIR_B_VM, self.localenv.storage)
        instance_id_b = \
            instance_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        reservation_list = \
            client.get_all_reservations(instance_ids=instance_id_b)
        instance_list = reservation_list[0].instances

        security_group_node = \
            self._get_instance_node(PAIR_B_SG, self.localenv.storage)
        security_group_id = \
            security_group_node.runtime_properties[EXTERNAL_RESOURCE_ID]
        security_group_object_list = \
            client.get_all_security_groups(group_ids=security_group_id)

        self.assertIn(
            str(security_group_object_list[0].instances()[0].id),
            str(instance_list[0].id))

        self.localenv.execute('uninstall', task_retries=10)

        with self.assertRaises(EC2ResponseError):
            client.get_all_addresses(addresses=elastic_ip_address)
        with self.assertRaises(EC2ResponseError):
            client.get_all_security_groups(group_ids=security_group_id)

        client.get_all_reservations(instance_ids=instance_id_a)
        instance_state = reservation_list[0].instances[0].update()
        self.assertIn('terminated', instance_state)
        client.get_all_reservations(instance_ids=instance_id_b)
        instance_state = reservation_list[0].instances[0].update()
        self.assertIn('terminated', instance_state)

