########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

import random
import logging
import os
import time
import copy
from contextlib import contextmanager


from cosmo_tester.framework.handlers import (
    BaseHandler,
    BaseCloudifyInputsConfigReader)
    


class AzureCleanupContext(BaseHandler.CleanupContext):

    def __init__(self, context_name, env):
        super(AzureCleanupContext, self).__init__(context_name, env)
        self.before_run = self.env.handler.azure_infra_state()

    def cleanup(self):
        """
        Cleans resources created by the test.
        Resource that existed before the test will not be removed
        """
        super(AzureCleanupContext, self).cleanup()
        resources_to_teardown = self.get_resources_to_teardown(
            self.env, resources_to_keep=self.before_run)
        if self.skip_cleanup:
            self.logger.warn('[{0}] SKIPPING cleanup of resources: {1}'
                             .format(self.context_name, resources_to_teardown))
        else:
            self._clean(self.env, resources_to_teardown)
    
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
        if env.use_external_resource:
            resources_to_be_removed['resource_group_name'].pop(
                env.existing_resource_group_name, None)
       
        if env.use_external_resource:
            resources_to_be_removed['storage_account_name'].pop(env.existing_storage_account_name,
                                                     None)
        if env.use_external_resource:
            resources_to_be_removed['vnet_name'].pop(env.existing_vnet_name,
                                                     None)
        if env.use_external_resource:
            resources_to_be_removed['public_ip_name'].pop(env.existing_public_ip_name,
                                                     None)
        if env.use_external_resource:
            resources_to_be_removed['nic_name'].pop(env.existing_nic_name,
                                                     None)
        
        cls.logger.info(
            "resources_to_be_removed: {0}".format(resources_to_be_removed))
        failed = env.handler.remove_azure_resources(resources_to_be_removed)
        errorflag = not (
            (len(failed['resourcegroups']) == 0) and
            (len(failed['storageaccounts']) == 0) and
            (len(failed['vnets']) == 0) and
            (len(failed['nics']) == 0) and
            (len(failed['publicips']) == 0) and
            (len(failed['subnets']) == 0)
            # This is the default security group which cannot
            # be removed by a user.
            (len(failed['securitygroups']) == 1))
        if errorflag:
            raise Exception(
                "Unable to clean up Environment, "
                "resources remaining: {0}".format(failed))
                
   
class CloudifyAzureInputsConfigReader(BaseCloudifyInputsConfigReader):

    @property
    def subscription_id(self):
        return self.config['subscription_id']

    @property
    def location(self):
        return self.config['location']

    @property
    def vm_prefix(self):
        return self.config['vm_prefix']

    @property
    def vm_size(self):
        return self.config['vm_size']

    @property
    def image_reference_offer(self):
        return self.config['image_reference_offer']

    @property
    def image_reference_publisher(self):
        return self.config['image_reference_publisher']
        
    @property
    def image_reference_sku(self):
        return self.config['image_reference_sku']


    @property
    def use_external_resource(self):
        return self.config['use_external_resource']

    @property
    def existing_resource_group_name(self):
        return self.config['existing_resource_group_name']

    @property
    def existing_storage_account_name(self):
        return self.config['existing_storage_account_name']

    @property
    def existing_security_group_name(self):
        return self.config['existing_security_group_name']

    @property
    def existing_vnet_name(self):
        return self.config['existing_vnet_name']

    @property
    def existing_nic_name(self):
        return self.config['existing_nic_name']

    @property
    def existing_public_ip_name(self):
        return self.config['existing_public_ip_name']

    @property
    def key_data(self):
        return self.config['key_data']

    @property
    def agent_remote_key_path(self):
        return self.config.get('agent_remote_key_path')

    @property
    def agent_local_key_path(self):
        return self.config['agent_local_key_path']

    @property
    def ssh_key_id(self):
        return self.config['ssh_key_id']
    
    @property
    def ssh_key_filename(self):
        return self.config['ssh_key_filename']
        
    @property
    def client_id(self):
        return self.config['client_id']  
        
    @property
    def tenant_id(self):
        return self.config['tenant_id'] 
 
    @property
    def aad_password(self):
        return self.config['aad_password'] 
 
    @property
    def subnet(self):
        return self.config['subnet'] 

    @property
    def ssh_user(self):
        return self.config['ssh_user'] 
 
    @property
    def custom_script_path(self):
        return self.config['custom_script_path']  


    @property
    def custom_script_command(self):
        return self.config['custom_script_command']  


    @property
    def security_group_priority(self):
        return self.config['security_group_priority']  

    @property
    def security_group_protocol(self):
        return self.config['security_group_protocol'] 

    @property
    def security_group_access(self):
        return self.config['security_group_access'] 


    @property
    def security_group_direction(self):
        return self.config['security_group_direction'] 
        
        
    @property
    def security_group_sourcePortRange(self):
        return self.config['security_group_sourcePortRange']  


    @property
    def security_group_destinationPortRange(self):
        return self.config['security_group_destinationPortRange'] 

    @property
    def security_group_sourceAddressPrefix(self):
        return self.config['security_group_sourceAddressPrefix'] 


    @property
    def security_group_destinationAddressPrefix(self):
        return self.config['security_group_destinationAddressPrefix'] 
        
        
class AzureHandler(BaseHandler):

    CleanupContext = AzureCleanupContext
    CloudifyConfigReader = CloudifyAzureInputsConfigReader

    def azure_client(self):
        creds = self._client_creds()
        return (client.Client(**creds),
                client.Client(subscription_id=creds['subscription_id'],
                                location=creds['location'],
                                tenant_id = creds['tenant_id'],
                                client_id = creds['client_id'],
                client.Client(**creds))


    def azure_infra_state(self):
       
        azurecloudify = self.azure_clients()
        try:
            prefix = self.env.resources_prefix
        except (AttributeError, KeyError):
            prefix = ''
        return {
            'resourcegroups': dict(self._resourcegroups(azurecloudify)),
            'subnets': dict(self._subnets(azurecloudify)),
            'storageaccounts': dict(self._storageaccounts(azurecloudify)),
            'securitygroups': dict(self._securitygroups(azurecloudify)),
            'servers': dict(self._servers(azurecloudify)),
            'publicips': dict(self._publicips(azurecloudify)),
            'nics': dict(self._nics(azurecloudify)),
            'availabilitysets': dict(self._availabilitysets(azurecloudify)),
            'serverwithnics': dict(self._serverwithnics(azurecloudify))
        }

    def azure_infra_state_delta(self, before, after):
        after = copy.deepcopy(after)
        return {
            prop: self._remove_keys(after[prop], before[prop].keys())
            for prop in before
        }


    def remove_azure_resources(self, resources_to_remove):
        
        
        servers = self.azurecloudify.servers.list()
        resourcegroups = self.azurecloudify._get_resource_group_name()['resource_group_name']
        storageaccounts = self.azurecloudify._get_storage_account_name()['storage_account_name']
        subnets = self.azurecloudify._get_subnet_name()['subnet_name']
        publicips = self.azurecloudify._get_public_ip_name()['public_ip_name']
        nics = self.azurecloudify._get_nic_name()['nic_name']
        vnet = self.azurecloudify._get_vnet_name()['vnet_name']
        availabilitysets = self.azurecloudify._get_availability_set_name()['availability_set_name']
        securitygroups = self.azurecloudify._get_security_group_name()['security_groups_name']
    
        failed = {
            'servers': {},
            'storageaccounts': {},
            'resourcegroups': {},
            'publicips': {},  
            'vnets': {},  
            'nics': {},  
            'availabilitysets': {},  
            'serverwithnics': {},
            'security_groups': {}
        }

        for vm_name in servers:
            if vm_name in resources_to_remove['servers']:
                with self._handled_exception(vm_name, failed, 'servers'):
                    azurecloudify.server.delete_vm(vm_name)

        for nic_name in nics:
            if nic_name in resources_to_remove['nics']:
                with self._handled_exception(nic_name, failed, 'nics'):
                    azurecloudify.nic.delete_nic(nic_name)

        for public_ip_name in publicips:
            if public_ip_name in resources_to_remove['publicips']:
                with self._handled_exception(public_ip_name, failed, 'publicips'):
                    azurecloudify.publicip.delete_public_ip(public_ip_name)
                    
        for vnet_name in vnets:
            if vnet_name in resources_to_remove['vnets']:
                with self._handled_exception(vnet_name, failed, 'vnets'):
                    azurecloudify.vnet.delete_vnet(vnet_name)


        for subnet_name in subnets:
            if subnet_name in resources_to_remove['subnets']:
                with self._handled_exception(vnet_name, failed, 'subnets'):
                    azurecloudify.subnet.delete_subnet(subnet_name)

        for security_group_name in securitygroups:
            if security_group_name in resources_to_remove['securitygroups']:
                with self._handled_exception(security_group_name, failed, 'securitygroups'):
                    azurecloudify.securitygroup.delete_security_group(security_group_name)

        for storage_account_name in storageaccounts:
            if security_group_name in resources_to_remove['storageaccounts']:
                with self._handled_exception(storage_account_name, failed, 'storageaccounts'):
                    azurecloudify.storageaccount.delet_storage_account(storage_account_name)
                    
        for resource_group_name in resourcegroups:
            if resource_group_name in resources_to_remove['resourcegroups']:
                with self._handled_exception(resource_group_name, failed, 'resourcegroups'):
                    azurecloudify.resourcegroup.delet_resource_group(resource_group_name)

        return failed

    

    def _client_creds(self):
        return {
            'subscription_id': self.env.subscription_id,
            'location': self.env.location
        }

    def _resourcegroups(self, azure_client):
        return [(resource_group_name)
                for resource_group in resoucegroup._get_resource_group_name()]
        

    def _storageaccounts(self, azure_client):
        return [(storage_account_name]
                for storage_account in storageaccount._get_storage_account_name()]

    def _securityaccounts(self,azure_client):
        return [(security_group_name)
                for security_group in securitygroup._get_security_group_name()]

    def _vnets(self, azure_client):
        return [vnet_name
                for vnet_name in vnet._get_vnet_name()]

    def _publicips(self, azure_client):
        return [public_ip_name
                for public_ip in publicip._get_public_ip_name()]

    def _nics(self, azure_client):
        return [nic_name
                for nic in nic._get_nic_name]

    def _servers(self, azure_client):
        return [vm_name
                for vnet in server._get_server_name]

    def _availability_sets(self, azure_client):
        return [availability_set_name
                for availabilty_set in availabilityset._get_availability_set_name]

    @contextmanager
    def _handled_exception(self, resource_id, failed, resource_group):
        try:
            yield
        except BaseException, ex:
            failed[resource_group][resource_id] = ex

handler = AzureHandler
