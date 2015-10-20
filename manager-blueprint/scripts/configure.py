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

import os
import tempfile
import json

import fabric
import fabric.api

from cloudify import ctx
from azurecloudify import constants


PROVIDER_CONTEXT_RUNTIME_PROPERTY = 'provider_context'


def configure(azure_config):
    _set_provider_context()
    _copy_azure_configuration_to_manager(azure_config)


def _set_provider_context():
    # Do not use this code section as a reference - it is a workaround for a
    #  deprecated feature and will be removed in the near future

    resources = dict()
    ctx.logger.info("In _set_provider_context")

    # the reference to storage only works the workflow is executed as a
    # local workflow (i.e. in a local environment context)
    node_instances = ctx._endpoint.storage.get_node_instances()
    nodes_by_id = \
        {node.id: node for node in ctx._endpoint.storage.get_nodes()}

    node_id_to_provider_context_field = {
        'manager_server': 'manager_server',
        'manager_resource_group': 'manager_resource_group',
        'manager_security_group': 'manager_security_group',
        'manager_storage_account': 'manager_storage_account',
        'manager_public_ip': 'manager_public_ip',
        'manager_nic': 'manager_nic',
        'manager_vnet': 'manager_vnet'
    }
    for node_instance in node_instances:
        if node_instance.node_id in node_id_to_provider_context_field:
            run_props = node_instance.runtime_properties
            props = nodes_by_id[node_instance.node_id].properties
            provider_context_field = \
                node_id_to_provider_context_field[node_instance.node_id]

            if 'use_external_resource' in props:
                resources[provider_context_field] = {
                    'use_external_resource': props['use_external_resource']
                }
            else:
                resources[provider_context_field] = {}

            for runtime_prop in run_props:
                resources[provider_context_field][runtime_prop] = run_props[runtime_prop]
                #ctx.logger.info("field {} prop {} = {}".format(provider_context_field,runtime_prop, run_props[runtime_prop]))

            if node_instance.node_id == 'manager_server':
                resources[provider_context_field]['ip'] = run_props['ip']
                #ctx.logger.info("provider_context_field {} private IP is {}".format(provider_context_field, run_props['ip']))

    provider = {
        'resources': resources
    }

    ctx.instance.runtime_properties[PROVIDER_CONTEXT_RUNTIME_PROPERTY] = provider
    ctx.logger.info("End of _set_provider_context")



def _copy_azure_configuration_to_manager(azure_config):
    tmp = tempfile.mktemp()
    with open(tmp, 'w') as f:
        json.dump(azure_config, f)
    with open(tmp, 'r+') as f:
        json_data = json.load(f)
        json_data["auth_token"] = ""
        json_data["token_expires"] = "0"  #unix timestamp for 1/1/1970 00:00:00 is 0
        f.seek(0)
        f.write(json.dumps(json_data))
    fabric.api.put(tmp, constants.path_to_azure_conf)
	
