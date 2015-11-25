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
import requests
from requests import Request,Session,Response
import json
import constants
import sys
import os
import auth
from resourcegroup import *
import utils
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify import ctx
from cloudify.decorators import operation


@operation
def creation_validation(**_):
    for property_key in constants.DISK_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_disk(**_):

    curr_disk_key = "{0}{1}{2}".format(constants.DATA_DISK_KEY, ctx.node.id, ctx.instance.id)
    if curr_disk_key in ctx.instance.runtime_properties:
        ctx.logger.info("Using disk {0}".format(ctx.instance.runtime_properties[curr_disk_key]))
        return

    current_disk_name = constants.DATA_DISK_PREFIX+utils.random_suffix_generator()
    ctx.instance.runtime_properties[curr_disk_key] = current_disk_name
    ctx.logger.info("{0} is {1}".format(curr_disk_key, current_disk_name))


@operation
def delete_disk(**_):
    utils.clear_runtime_properties()


@operation
def set_resource_group_details(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]


def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))


def set_disks_from_runtime(caller_string, source_runtime_properties, target_runtime_properties, use_only_first_disk=True):
    for curr_key in target_runtime_properties:
        if curr_key.startswith(constants.DATA_DISK_KEY):
            source_runtime_properties[curr_key] = target_runtime_properties[curr_key]
            ctx.logger.info("{0}:{1} is {2}".format(caller_string, curr_key, source_runtime_properties[curr_key]))
            if use_only_first_disk:
                return source_runtime_properties[curr_key]
    return "OK"
