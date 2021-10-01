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
    resources.network.PublicIPAddress
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Microsoft Azure Public IP Address interface
"""
from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import (constants, decorators, utils)
from azure_sdk.resources.network.public_ip_address import PublicIPAddress

PUBLIC_IP_PROPERTY = 'public_ip_address'


@operation(resumable=True)
@decorators.with_generate_name(PublicIPAddress)
@decorators.with_azure_resource(PublicIPAddress)
def create(ctx, **_):
    """Uses an existing, or creates a new, Public IP Address"""
    # Create a resource (if necessary)
    azure_config = utils.get_client_config(ctx.node.properties)
    name = utils.get_resource_name(ctx)
    resource_group_name = utils.get_resource_group(ctx)
    public_ip_address_params = {
        'location': ctx.node.properties.get('location'),
        'tags': ctx.node.properties.get('tags'),
    }
    public_ip_address_params = \
        utils.handle_resource_config_params(public_ip_address_params,
                                            ctx.node.properties.get(
                                                'resource_config', {}))
    # Special Case dnsSettings
    public_ip_address_params['dns_settings'] = {
        'domain_name_label':
            public_ip_address_params.pop('domain_name_label', None),
        'reverse_fqdn':
            public_ip_address_params.pop('reverse_fqdn', None)
    }
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    public_ip_address = PublicIPAddress(azure_config, ctx.logger, api_version)
    # clean empty values from params
    public_ip_address_params = \
        utils.cleanup_empty_params(public_ip_address_params)

    try:
        result = \
            public_ip_address.create_or_update(
                resource_group_name,
                name,
                public_ip_address_params)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "create public_ip_address '{0}' "
            "failed with this error : {1}".format(name,
                                                  cr.message)
            )

    utils.save_common_info_in_runtime_properties(
        resource_group_name=resource_group_name,
        resource_name=name,
        resource_get_create_result=result)


@operation(resumable=True)
def start(ctx, **_):
    """Update IP runtime property"""
    azure_config = utils.get_client_config(ctx.node.properties)
    name = ctx.instance.runtime_properties.get('name')
    resource_group_name = utils.get_resource_group(ctx)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    public_ip_address = PublicIPAddress(azure_config, ctx.logger, api_version)
    try:
        result = public_ip_address.get(resource_group_name, name)
        ctx.instance.runtime_properties[PUBLIC_IP_PROPERTY] = \
            result.get('ip_address')
    except CloudError:
        raise cfy_exc.NonRecoverableError(
            "Resource with name {0} doesn't exist".format(name))


@operation(resumable=True)
def delete(ctx, **_):
    """Deletes a Public IP Address"""
    # Delete the resource
    if ctx.node.properties.get('use_external_resource', False):
        return
    azure_config = utils.get_client_config(ctx.node.properties)
    resource_group_name = utils.get_resource_group(ctx)
    name = ctx.instance.runtime_properties.get('name')
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_NETWORK)
    public_ip_address = PublicIPAddress(azure_config, ctx.logger, api_version)
    utils.handle_delete(ctx, public_ip_address, resource_group_name, name)
