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
    provider = {}
    ctx.instance.runtime_properties[
        PROVIDER_CONTEXT_RUNTIME_PROPERTY] = provider


def _copy_azure_configuration_to_manager(azure_config):
    tmp = tempfile.mktemp()
    with open(tmp, 'w') as f:
        json.dump(azure_config, f)
    with open(tmp, 'r+') as f:
        json_data = json.load(f)
        json_data["auth_token"] = ""
        json_data["token_expires"] = "0" #unix timestamp for 1/1/1970 00:00:00 is 0
        f.seek(0)
        f.write(json.dumps(json_data))
    fabric.api.put(tmp, constants.path_to_azure_conf)
	
