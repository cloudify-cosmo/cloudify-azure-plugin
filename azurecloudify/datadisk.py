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
import json
import constants
import sys
import os
import auth
import utils
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation


@operation
def creation_validation(**_):
    for property_key in constants.DISK_REQUIRED_PROPERTIES:
        utils.validate_node_properties(property_key, ctx.node.properties)


@operation
def create_disk(**_):
	luns = ctx.node.properties['lun']
	for x in range(0, luns):
		curr_disk_key = "{0}{1}{2}".format(constants.DATA_DISK_KEY, ctx.node.id, ctx.instance.id)
		#if curr_disk_key in ctx.instance.runtime_properties:
		#	ctx.logger.info("Using disk {0}".format(ctx.instance.runtime_properties[curr_disk_key]))
		#	return

		utils.set_runtime_properties_from_file()
		current_disk_name = constants.DATA_DISK_PREFIX+utils.random_suffix_generator()
		ctx.instance.runtime_properties[curr_disk_key] = current_disk_name
		ctx.logger.info("create_disk: {0} is {1}".format(curr_disk_key, current_disk_name))
		ctx.instance.runtime_properties[constants.DATA_DISK_SIZE_KEY] = ctx.node.properties[constants.DATA_DISK_SIZE_KEY]
		ctx.logger.info("create_disk: {0} is {1}".format(current_disk_name,
														 ctx.instance.runtime_properties[constants.DATA_DISK_SIZE_KEY]))


@operation
def delete_disk(**_):
    utils.clear_runtime_properties()


@operation
def set_storageaccount_details(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY, constants.STORAGE_ACCOUNT_KEY]+constants.REQUIRED_CONFIG_DATA)



