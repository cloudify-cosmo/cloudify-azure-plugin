# #######
# Copyright (c) 2020 Cloudify Platform Ltd. All rights reserved
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
import base64
import yaml

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.containerservice import ContainerServiceClient
from msrestazure.azure_exceptions import CloudError

from cloudify.decorators import operation
from cloudify import exceptions as cfy_exc
from cloudify._compat import text_type
from cloudify_azure.resources.base import ResourceSDK


class ManagedCluster(ResourceSDK):
    def __init__(
            self, logger, credentials, resource_group, cluster_name,
            resource_config=None):
        self.resource_group = resource_group
        self.cluster_name = cluster_name
        self.logger = logger
        self.resource_config = resource_config
        self.resource_verify = bool(credentials.get('endpoint_verify', True))
        super(ManagedCluster, self).__init__(credentials)
        self.client = ContainerServiceClient(
            self.credentials, '{0}'.format(credentials['subscription_id']))
        self.resourceClient = ResourceManagementClient(
            self.credentials, '{0}'.format(credentials['subscription_id']))
        self.logger.info("Use subscription: {}"
                         .format(credentials['subscription_id']))

    def create_or_update(self):
        """Create Managed Cluster with Resource Group"""

        location = self.resource_config.get('location')
        dns_prefix = self.resource_config.get('dns_prefix')
        kubernetes_version = self.resource_config.get('kubernetes_version')
        tags = self.resource_config.get('tags')
        sp_profile = self.resource_config.get('service_principal_profile')
        agent_pool_profiles = self.resource_config.get('agent_pool_profiles')
        linux_profile = self.resource_config.get('linux_profile')
        network_profile = self.resource_config.get('network_profile')
        windows_profile = self.resource_config.get('windows_profile')
        addon_profiles = self.resource_config.get('addon_profiles')
        enable_rbac = self.resource_config.get('enable_rbac')
        managedClusterParams = {
            'location': location,
            'dns_prefix': dns_prefix,
            'kubernetes_version': kubernetes_version,
            'tags': tags,
            'service_principal_profile': sp_profile,
            'agent_pool_profiles': agent_pool_profiles,
            'linux_profile': linux_profile,
            'network_profile': network_profile,
            'windows_profile': windows_profile,
            'addon_profiles': addon_profiles,
            'enable_rbac': enable_rbac
        }

        self.logger.info("Create/Updating Managed Cluster...")
        managed_cluster_async = self.client.managed_clusters.create_or_update(
            self.resource_group,
            self.cluster_name,
            managedClusterParams
        )
        return managed_cluster_async.result()

    def get(self):
        return self.client.managed_clusters.get(
            resource_group_name=self.resource_group,
            resource_name=self.cluster_name)

    def delete(self):
        """Deletes the managed cluster with a specified
        resource group and name"""
        self.logger.info("Delete managed cluster...")
        managed_cluster_async = self.client.managed_clusters.delete(
            resource_group_name=self.resource_group,
            resource_name=self.cluster_name)
        managed_cluster_async.result()

    def get_admin_kubeconf(self):
        admin_credentials = \
            self.client.managed_clusters.list_cluster_admin_credentials(
                self.resource_group,
                self.cluster_name
            )
        return admin_credentials.as_dict().get("kubeconfigs")[0].get("value")


@operation(resumable=True)
def create(ctx, resource_group, cluster_name, resource_config, **kwargs):
    azure_auth = ctx.node.properties['azure_config']
    store_kube_config_in_runtime = \
        ctx.node.properties['store_kube_config_in_runtime']
    managedCluster = ManagedCluster(ctx.logger, azure_auth, resource_group,
                                    cluster_name, resource_config)
    if ctx.node.properties.get('use_external_resource', False):
        try:
            managedCluster.get()
            ctx.logger.info("Using external resource")
        except CloudError:
            raise cfy_exc.NonRecoverableError(
                "Can't use non-existing Managed Cluster '{}'.".
                format(cluster_name)
            )
    else:
        managedCluster.create_or_update()
        ctx.instance.runtime_properties['resource_group'] = resource_group
        ctx.instance.runtime_properties['cluster_name'] = cluster_name
    if store_kube_config_in_runtime:
        ctx.instance.runtime_properties['kubeconf'] = \
            yaml.load(base64.b64decode(managedCluster.get_admin_kubeconf()))


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_auth = ctx.node.properties['azure_config']
    resource_group = ctx.instance.runtime_properties.get('resource_group')
    cluster_name = ctx.instance.runtime_properties.get('cluster_name')
    managedCluster = ManagedCluster(ctx.logger, azure_auth, resource_group,
                                    cluster_name)
    managedCluster.delete()
