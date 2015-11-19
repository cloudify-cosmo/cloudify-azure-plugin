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

import random
import string
from cloudify import ctx
import constants
from cloudify.exceptions import NonRecoverableError,RecoverableError
import requests
from requests import Request,Session,Response
import json


def get_provisioning_state(headers, resource_name, check_resource_url):
    ctx.logger.info("In get_provisioning_state checking {0}".format(resource_name))
    check_resource_response = requests.get(url=check_resource_url, headers=headers)
    response_json = check_resource_response.json()
    if 'properties' in response_json:
        return response_json['properties']['provisioningState']
    elif 'error' in response_json:
        err_msg = response_json['error']['message']
        ctx.logger.info("In get_provisioning_state error message is \"{0}\"".format(err_msg))
        return err_msg
    else:
        ctx.logger.info("In get_provisioning_state returning json {0}".format(str(response_json)))
        return response_json


