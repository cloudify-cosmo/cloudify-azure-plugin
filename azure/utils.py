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
    list_rg=requests.get(url=constants.list_resource_group_url, headers=constants.headers)
    print list_rg.text
    #rg_list= extract from json file
    #return rg_list

@operation
def list_all_storage_accounts(**_):
    list_sg = requests.get(url=constants.list_storage_account_url, headers = constants.headers)
    print list_sg.text
    #sg_account_name_list= #extract sg_name
    #return sg_account_name_list

@operation
def list_all_virtual_networks(**_):
    list_vnet = requests.get(url=constants.list_vnet_url, headers = constants.headers)
    print list_vnet.text

    #vnet_list= #extract vnet_name
    #return vnet_list


@operation
def list_all_virtual_machines(**_):
    list_vms = requests.get(url=constants.list_vms_url, headers = constants.headers)
    print list_vms.text
    #vm_list= #extract vnet_name
    #return vm_list

