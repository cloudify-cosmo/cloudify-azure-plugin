# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
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
"""
    resources.network.NetworkSecurityRule
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Network Security Rule interface
"""
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation


from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.network.network_security_rule \
    import NetworkSecurityRule


@operation(resumable=True)
@decorators.with_generate_name(NetworkSecurityRule)
@decorators.with_azure_resource(NetworkSecurityRule)
def create(ctx, **_):
    """Uses an existing, or creates a new, Network Security Rule"""
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    nsg_name = utils.get_network_security_group(ctx)
    nsr_params = {}
    nsr_params = \
        utils.handle_resource_config_params(nsr_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_security_rule = NetworkSecurityRule(azure_config, ctx.logger,
                                                api_version)
    # clean empty values from params
    nsr_params = \
        utils.cleanup_empty_params(nsr_params)

    try:
        result = \
            network_security_rule.create_or_update(resource_group_name,
                                                   nsg_name, name,
                                                   nsr_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create network_security_rule '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )

    ctx.instance.runtime_properties['network_security_group'] = nsg_name
    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Network Security Rule"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    nsg_name = ctx.instance.runtime_properties.get('network_security_group')
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    network_security_rule = NetworkSecurityRule(azure_config, ctx.logger,
                                                api_version)
    utils.handle_delete(
        ctx, network_security_rule, resource_group_name, name, nsg_name)
