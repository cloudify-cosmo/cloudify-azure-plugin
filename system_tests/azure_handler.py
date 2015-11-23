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

    @classmethod
    def clean_all(cls, env):
        """
        Cleans *all* resources, including resources that were not
        created by the test
        """
        super(AzureCleanupContext, cls).clean_all(env)
        resources_to_teardown = cls.get_resources_to_teardown(env)
        cls._clean(env, resources_to_teardown)

    @classmethod
    def _clean(cls, env, resources_to_teardown):
        cls.logger.info('Azure handler will try to remove these resources:'
                        ' {0}'.format(resources_to_teardown))
        failed_to_remove = env.handler.remove_azure_resources(
            resources_to_teardown)
        if failed_to_remove:
            trimmed_failed_to_remove = {key: value for key, value in
                                        failed_to_remove.iteritems()
                                        if value}
            if len(trimmed_failed_to_remove) > 0:
                msg = 'Azure handler failed to remove some resources:' \
                      ' {0}'.format(trimmed_failed_to_remove)
                cls.logger.error(msg)
                raise RuntimeError(msg)

    @classmethod
    def get_resources_to_teardown(cls, env, resources_to_keep=None):
        all_existing_resources = env.handler.azure_infra_state()
        if resources_to_keep:
            return env.handler.azure_infra_state_delta(
                before=resources_to_keep, after=all_existing_resources)
        else:
            return all_existing_resources

    def update_server_id(self, server_name):

        # retrieve the id of the new server
        nova, _, _ = self.env.handler.azure_clients()
        servers = nova.servers.list(
            search_opts={'name': server_name})
        if len(servers) > 1:
            raise RuntimeError(
                'Expected 1 server with name {0}, but found {1}'
                .format(server_name, len(servers)))

        new_server_id = servers[0].id

        # retrieve the id of the old server
        old_server_id = None
        servers = self.before_run['servers']
        for server_id, name in servers.iteritems():
            if server_name == name:
                old_server_id = server_id
                break
        if old_server_id is None:
            raise RuntimeError(
                'Could not find a server with name {0} '
                'in the internal cleanup context state'
                .format(server_name))

        # replace the id in the internal state
        servers[new_server_id] = servers.pop(old_server_id)


class CloudifyAzureInputsConfigReader(BaseCloudifyInputsConfigReader):
"""
    def __init__(self, cloudify_config, manager_blueprint_path, **kwargs):
        super(CloudifyAzureInputsConfigReader, self).__init__(
            cloudify_config, manager_blueprint_path=manager_blueprint_path,
            **kwargs)
"""
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

    def before_bootstrap(self):
        super(AzureHandler, self).before_bootstrap()
        with self.update_cloudify_config() as patch:
            suffix = '-%06x' % random.randrange(16 ** 6)
            server_name_prop_path = 'manager_server_name'
            patch.append_value(server_name_prop_path, suffix)

    def after_bootstrap(self, provider_context):
        super(AzureHandler, self).after_bootstrap(provider_context)
        resources = provider_context['resources']
        agent_keypair = resources['agents_keypair']
        management_keypair = resources['management_keypair']
        self.remove_agent_keypair = agent_keypair['external_resource'] is False
        self.remove_management_keypair = \
            management_keypair['external_resource'] is False

    def after_teardown(self):
        super(AzureHandler, self).after_teardown()
        if self.remove_agent_keypair:
            agent_key_path = get_actual_keypath(self.env,
                                                self.env.agent_key_path,
                                                raise_on_missing=False)
            if agent_key_path:
                os.remove(agent_key_path)
        if self.remove_management_keypair:
            management_key_path = get_actual_keypath(
                self.env,
                self.env.management_key_path,
                raise_on_missing=False)
            if management_key_path:
                os.remove(management_key_path)

    def azure_clients(self):
        creds = self._client_creds()
        return (client.Client(**creds),
                client.Client(subscription_id=creds['subscription_id'],
                                location=creds['location'],
                client.Client(**creds))

    @retry(stop_max_attempt_number=5, wait_fixed=20000)
    def azure_infra_state(self):
        """
        @retry decorator is used because this error sometimes occur:
        ConnectionFailed: Connection to neutron failed: Maximum
        attempts reached
        """
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
        # basically sort of a workaround, but if we get the order wrong
        # the first time, there is a chance things would better next time
        # 3'rd time can't really hurt, can it?
        # 3 is a charm
        for _ in range(3):
            resources_to_remove = self._remove_openstack_resources_impl(
                resources_to_remove)
            if all([len(g) == 0 for g in resources_to_remove.values()]):
                break
            # give openstack some time to update its data structures
            time.sleep(3)
        return resources_to_remove

    def _remove_azure_resources_impl(self, resources_to_remove):
        nova, neutron, cinder = self.openstack_clients()
        
        servers = azurecloudify.servers.list()
        resourcegroups = azurecloudify._get_resource_group_name()['resource_group_name']
        storageaccounts = azurecloudify._get_storage_account_name()['storage_account_name']
        subnets = azurecloudify._get_subnet_name()['subnet_name']
        publicips = azurecloudify._get_public_ip_name()['public_ip_name']
        nics = azurecloudify._get_nic_name()['nic_name']
        vnet = azurecloudify._get_vnet_name()['vnet_name']
        availabilitysets = azurecloudify._get_availability_set_name()['availability_set_name']
        securitygroups = azurecloudify._get_security_group_name()['security_groups_name']
    
        failed = {
            'servers': {},
            'storageaccounts': {},
            'resourcegroups' {},
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

    def _delete_volumes(self, nova, cinder, existing_volumes):
        unremovables = {}
        end_time = time.time() + VOLUME_TERMINATION_TIMEOUT_SECS

        for volume in existing_volumes:
            # detach the volume
            if volume.status in ['available', 'error', 'in-use']:
                try:
                    self.logger.info('Detaching volume {0} ({1}), currently in'
                                     ' status {2} ...'.
                                     format(volume.display_name, volume.id,
                                            volume.status))
                    for attachment in volume.attachments:
                        nova.volumes.delete_server_volume(
                            server_id=attachment['server_id'],
                            attachment_id=attachment['id'])
                except Exception as e:
                    self.logger.warning('Attempt to detach volume {0} ({1})'
                                        ' yielded exception: "{2}"'.
                                        format(volume.display_name, volume.id,
                                               e))
                    unremovables[volume.id] = e
                    existing_volumes.remove(volume)

        time.sleep(3)
        for volume in existing_volumes:
            # delete the volume
            if volume.status in ['available', 'error', 'in-use']:
                try:
                    self.logger.info('Deleting volume {0} ({1}), currently in'
                                     ' status {2} ...'.
                                     format(volume.display_name, volume.id,
                                            volume.status))
                    cinder.volumes.delete(volume)
                except Exception as e:
                    self.logger.warning('Attempt to delete volume {0} ({1})'
                                        ' yielded exception: "{2}"'.
                                        format(volume.display_name, volume.id,
                                               e))
                    unremovables[volume.id] = e
                    existing_volumes.remove(volume)

        # wait for all volumes deletion until completed or timeout is reached
        while existing_volumes and time.time() < end_time:
            time.sleep(3)
            for volume in existing_volumes:
                volume_id = volume.id
                volume_name = volume.display_name
                try:
                    vol = cinder.volumes.get(volume_id)
                    if vol.status == 'deleting':
                        self.logger.debug('volume {0} ({1}) is being '
                                          'deleted...'.format(volume_name,
                                                              volume_id))
                    else:
                        self.logger.warning('volume {0} ({1}) is in '
                                            'unexpected status: {2}'.
                                            format(volume_name, volume_id,
                                                   vol.status))
                except Exception as e:
                    # the volume wasn't found, it was deleted
                    if hasattr(e, 'code') and e.code == 404:
                        self.logger.info('deleted volume {0} ({1})'.
                                         format(volume_name, volume_id))
                        existing_volumes.remove(volume)
                    else:
                        self.logger.warning('failed to remove volume {0} '
                                            '({1}), exception: {2}'.
                                            format(volume_name,
                                                   volume_id, e))
                        unremovables[volume_id] = e
                        existing_volumes.remove(volume)

        if existing_volumes:
            for volume in existing_volumes:
                # try to get the volume's status
                try:
                    vol = cinder.volumes.get(volume.id)
                    vol_status = vol.status
                except:
                    # failed to get volume... status is unknown
                    vol_status = 'unknown'

                unremovables[volume.id] = 'timed out while removing volume {0}' \
                                          ' ({1}), current volume status is ' \
                                          '{2}'.format(volume.display_name,
                                                       volume.id, vol_status)

        if unremovables:
            self.logger.warning('failed to remove volumes: {0}'.format(
                unremovables))

        return unremovables

    def _client_creds(self):
        return {
            'subscription_id': self.env.subscription_id
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
