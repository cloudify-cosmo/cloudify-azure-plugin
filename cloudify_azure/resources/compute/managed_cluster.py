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

import yaml
import base64

from msrestazure.azure_exceptions import CloudError

from cloudify.decorators import operation
from cloudify import exceptions as cfy_exc

from cloudify_azure import (constants, utils, decorators)
from azure_sdk.resources.compute.managed_cluster import ManagedCluster


# @operation(resumable=True)
# def create(ctx, resource_group, cluster_name, resource_config, **kwargs):
#     azure_config = utils.get_client_config(ctx.node.properties)
#     store_kube_config_in_runtime = \
#         ctx.node.properties.get('store_kube_config_in_runtime')
#     api_version = \
#         ctx.node.properties.get('api_version',
#                                 constants.API_VER_MANAGED_CLUSTER)
#     managed_cluster = ManagedCluster(azure_config, ctx.logger, api_version)
#     resource_config_payload = {}
#     resource_config_payload = \
#         utils.handle_resource_config_params(resource_config_payload,
#                                             resource_config)
#     try:
#         result = managed_cluster.get(resource_group, cluster_name)
#         if ctx.node.properties.get('use_external_resource', False):
#             ctx.logger.info("Using external resource")
#         else:
#             ctx.logger.info("Resource with name {0} exists".format(
#                 cluster_name))
#             return
#     except CloudError:
#         if ctx.node.properties.get('use_external_resource', False):
#             raise cfy_exc.NonRecoverableError(
#                 "Can't use non-existing managed_cluster '{0}'.".format(
#                     cluster_name))
#         else:
#             try:
#                 result = \
#                     managed_cluster.create_or_update(resource_group,
#                                                      cluster_name,
#                                                      resource_config_payload)
#             except CloudError as cr:
#                 raise cfy_exc.NonRecoverableError(
#                     "create managed_cluster '{0}' "
#                     "failed with this error : {1}".format(cluster_name,
#                                                           cr.message)
#                     )
#
#     ctx.instance.runtime_properties['resource_group'] = resource_group
#     ctx.instance.runtime_properties['resource'] = result
#     ctx.instance.runtime_properties['resource_id'] = result.get("id", "")
#     ctx.instance.runtime_properties['name'] = cluster_name
#
#     if store_kube_config_in_runtime:
#         ctx.instance.runtime_properties['kubeconf'] = \
#             yaml.load(base64.b64decode(managed_cluster.get_admin_kubeconf(
#                 resource_group, cluster_name)))


@operation(resumable=True)
@decorators.with_azure_resource(ManagedCluster)
def create(ctx, resource_group, cluster_name, resource_config, **kwargs):
    managed_cluster = get_manged_cluster_interface(ctx)
    resource_config_payload = {}
    resource_config_payload = \
        utils.handle_resource_config_params(resource_config_payload,
                                            resource_config)
    try:
        result = \
            managed_cluster.create_or_update(resource_group,
                                             cluster_name,
                                             resource_config_payload)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create managed_cluster '{0}' "
            "failed with this error : {1}".format(cluster_name,
                                                  cr.message)
            )

    utils.save_common_info_in_runtime_properties(resource_group,
                                                 cluster_name,
                                                 result)
    store_kubeconf_if_needed(ctx, resource_group, cluster_name)


def get_manged_cluster_interface(ctx):
    azure_config = utils.get_client_config(ctx.node.properties)
    api_version = \
        ctx.node.properties.get('api_version',
                                constants.API_VER_MANAGED_CLUSTER)
    return ManagedCluster(azure_config, ctx.logger, api_version)


def store_kubeconf_if_needed(ctx, resource_group, name):
    managed_cluster = get_manged_cluster_interface(ctx)
    store_kube_config_in_runtime = \
        ctx.node.properties.get('store_kube_config_in_runtime')

    if store_kube_config_in_runtime:
        ctx.instance.runtime_properties['kubeconf'] = \
            yaml.load(base64.b64decode(managed_cluster.get_admin_kubeconf(
                resource_group, name)))


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    resource_group = ctx.instance.runtime_properties.get('resource_group')
    name = ctx.instance.runtime_properties.get('name')
    managed_cluster = get_manged_cluster_interface(ctx)
    try:
        managed_cluster.get(resource_group, name)
    except CloudError:
        ctx.logger.info("Resource with name {0} doesn't exist".format(name))
        return
    try:
        managed_cluster.delete(resource_group, name)
        utils.runtime_properties_cleanup(ctx)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "delete managed_cluster '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )
