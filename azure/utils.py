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
def generate_credentials():
    client_id=ctx.node.properties('client_id')
    tenant_id=ctx.node.properties('tenant_id')
    username=ctx.node.properties('username')
    password=ctx.node.properties('password')
    url='https://login.microsoftonline.com/'+tenant_id+'/oauth2/token'
    headers ={"Content-Type":"application/x-www-form-urlencoded"}
    body = "grant_type=password&username="+username+"&password="+password+"&client_id="+client_id+"&resource=https://management.core.windows.net/"
    req = Request(method="POST",url=url,data=body)
    req_prepped = req.prepare()
    s = Session()
    res = Response()
    res = s.send(req_prepped)
    s=res.content
    end_of_leader = s.index('access_token":"') + len('access_token":"')
    start_of_trailer = s.index('"', end_of_leader)
    token=s[end_of_leader:start_of_trailer]
    print(token)
    credentials = "Bearer " + token
    return credentials

@operation
def validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


@operation
def list_all_resource_groups(**_):
    subscription_id = ctx.node.properties['subscription_id']
    list_resource_groups_url=azure_url+'/subscriptions/'+subscription_id+'/resourcegroups?api-version='+constants.api_version
    list_rg=requests.get(url=list_resource_groups_url, headers=constants.headers)
    print list_rg.text
    #rg_list= extract from json file
    #return rg_list

@operation
def list_all_storage_accounts(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_storage_accounts_url=azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Storage/storageAccounts?api-version='+constants.api_version
    list_sg = requests.get(url=list_storage_accounts_url, headers = constants.headers)
    print list_sg.text
    #sg_account_name_list= #extract sg_name
    #return sg_account_name_list

@operation
def list_all_vnets(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_vnets_url=azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/virtualnetworks?api-version='+constants.api_version
    list_vnet = requests.get(url=list_vnets_url, headers = constants.headers)
    print list_vnet.text

    #vnet_list= #extract vnet_name
    #return vnet_list

@operation
def list_all_public_ips(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_public_ips_url=azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/publicIPAddresses?api-version='+constants.api_version
    list_public_ips = requests.get(url=list_public_ips_url, headers = constants.headers)
    print list_public_ips.text
    #public_ips_list= #extract public_ips
    #return public_ips_list

    
@operation
def list_all_nics(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_nics_url=azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkInterfaces?api-version='+constants.api_version
    list_nic = requests.get(url=list_nics_url, headers = constants.headers)
    print list_nic.text

    #nic_list= #extract nic_name
    #return nic_list


@operation
def list_all_virtual_machines(**_):
    resource_group_name = ctx.node.properties['vm_name']+'_resource_group'
    subscription_id = ctx.node.properties['subscription_id']
    list_virtual_machines_url=azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/virtualmachines?api-version='+constants.api_version
    list_vms = requests.get(url=list_virtual_machines_url, headers = constants.headers)
    print list_vms.text
    #vm_list= #extract vnet_name
    #return vm_list

