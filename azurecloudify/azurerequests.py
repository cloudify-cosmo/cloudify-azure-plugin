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


import utils
from cloudify import ctx
import constants
import requests


def get_provisioning_state(headers, resource_name, check_resource_url, save_successful_response=True):
    ctx.logger.info("In get_provisioning_state checking {0}".format(resource_name))
    check_resource_response = requests.get(url=check_resource_url, headers=headers)
    response_json = check_resource_response.json()
    if 'properties' in response_json:
        if save_successful_response:
            # In order to save a redundant API call
            current_instance = utils.get_instance_or_source_instance()
            current_instance.runtime_properties[constants.SUCCESSFUL_RESPONSE_JSON] = response_json
        return response_json['properties']['provisioningState']
    elif 'error' in response_json:
        err_msg = response_json['error']['message']
        ctx.logger.info("In get_provisioning_state error message is \"{0}\"".format(err_msg))
    else:
        ctx.logger.info("In get_provisioning_state returning json {0}".format(str(response_json)))

    ctx.logger.info("In get_provisioning_state status code is {0}".format(check_resource_response.status_code))
    return check_resource_response.status_code


def check_delete_response(curr_response, start_retry_interval, caller_string, resource_name, resource_type):
    if curr_response.text:
        ctx.logger.info("{0} response is {1}".format(caller_string, curr_response.text))

    if curr_response.status_code in [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE]:
        ctx.logger.info("{0} status code is {1}".format(caller_string, curr_response.status_code))
        ctx.instance.runtime_properties[constants.RESOURCE_NOT_DELETED] = None
        return curr_response.status_code
    else:
        return ctx.operation.retry(message='Waiting for the {0} ({1}) to be deleted'.
            format(resource_type, resource_name), retry_after=start_retry_interval)

