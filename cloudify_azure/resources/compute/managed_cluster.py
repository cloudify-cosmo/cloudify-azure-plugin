# #######
# Copyright (c) 2020 - 2022 Cloudify Platform Ltd. All rights reserved
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

import yaml
import base64

from cloudify.decorators import operation
from cloudify import ctx as ctx_from_import

from cloudify_azure import (constants, utils, decorators)
from azure_sdk.resources.compute.managed_cluster import ManagedCluster


def get_manged_cluster_interface(ctx):
    azure_config = utils.get_client_config(ctx.node.properties)
    api_version = \
        ctx.node.properties.get('api_version',
                                constants.API_VER_MANAGED_CLUSTER)
    return ManagedCluster(azure_config, ctx.logger, api_version)


def handle_deprecated_values(config, deprecated_values):
    for value in deprecated_values:
        if value in config:
            new_value = value.capitalize()
            config[new_value] = config.pop(value)
            ctx_from_import.logger.error(
                'The value {} has been deprecrated by Microsoft '
                'and replaced by {}'.format(value, new_value))


@operation(resumable=True)
@decorators.with_azure_resource(ManagedCluster)
def create(ctx, resource_group, cluster_name, resource_config, **_):
    managed_cluster = get_manged_cluster_interface(ctx)
    if ctx.node.properties.get('cluster_name'):
        ctx.logger.warn(
            'The cluster_name is deprecated, but was provided. '
            'Update your blueprint to use the "name" property, '
            'which replaces "cluster_name".')
    resource_config_payload = {}
    if 'network_profile' in resource_config_payload:
        handle_deprecated_values(
            resource_config_payload['network_profile'],
            ['managedOutboundIPs', 'outboundIPPrefixes', 'outboundIPs'])
    resource_config_payload = \
        utils.handle_resource_config_params(resource_config_payload,
                                            resource_config)
    result = utils.handle_create(
        managed_cluster,
        resource_group,
        cluster_name,
        additional_params=resource_config_payload)
    utils.save_common_info_in_runtime_properties(resource_group,
                                                 cluster_name,
                                                 result)


@operation(resumable=True)
def store_kubeconf_if_needed(ctx):
    _store_kubeconf_if_needed(ctx)


@operation(resumable=True)
def refresh_kubeconfig(ctx):
    _store_kubeconf_if_needed(ctx.target)


def _store_kubeconf_if_needed(_ctx):
    resource_group = utils.get_resource_group(_ctx)
    name = utils.get_resource_name(_ctx)
    managed_cluster = get_manged_cluster_interface(_ctx)
    store_kube_config_in_runtime = \
        _ctx.node.properties.get('store_kube_config_in_runtime')

    if store_kube_config_in_runtime:
        _ctx.instance.runtime_properties['kubeconf'] = \
            yaml.load(base64.b64decode(managed_cluster.get_admin_kubeconf(
                resource_group, name)))


@operation(resumable=True)
@decorators.with_azure_resource(ManagedCluster)
def delete(ctx, **_):
    resource_group = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    managed_cluster = get_manged_cluster_interface(ctx)
    utils.handle_delete(ctx, managed_cluster, resource_group, name)
