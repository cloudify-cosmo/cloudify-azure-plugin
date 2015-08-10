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

# Built-in Imports
import os
import requests
import json
from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.decorators import operation
import constants


@operation
def validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


@operation
def list_all_resource_groups(**_):
    list_resource_groups_url='https://management.azure.com/subscriptions/'+constants.subscription_id+'/resourcegroups?api-version='+constants.api_version
    list_rg=requests.get(url=list_resource_groups_url, headers=constants.headers)
    print list_rg.text
    #rg_list= extract from json file
    #return rg_list

@operation
def list_all_storage_accounts(**_):
    resource_group_name = ctx.node.properties['resource_group_name']
    list_storage_accounts_url='https://management.azure.com/subscriptions/'+constants.subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts?api-version='+constants.api_version
    list_sg = requests.get(url=list_storage_accounts_url, headers = constants.headers)
    print list_sg.text
    #sg_account_name_list= #extract sg_name
    #return sg_account_name_list

@operation
def list_all_vnets(**_):
    resource_group_name = ctx.node.properties['resource_group_name']
    list_vnets_url='https://management.azure.com/subscriptions/'+constants.subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version
    list_vnet = requests.get(url=list_vnets_url, headers = constants.headers)
    print list_vnet.text

    #vnet_list= #extract vnet_name
    #return vnet_list


@operation
def list_all_virtual_machines(**_):
    resource_group_name = ctx.node.properties['resource_group_name']
    list_virtual_machines_url='https://management.azure.com/subscriptions/'+constants.subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualmachines?api-version='+constants.api_version
    list_vms = requests.get(url=list_virtual_machines_url, headers = constants.headers)
    print list_vms.text
    #vm_list= #extract vnet_name
    #return vm_list

