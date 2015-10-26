import random
import string
from cloudify import ctx
import constants
from cloudify.exceptions import NonRecoverableError,RecoverableError
import requests
from requests import Request,Session,Response
import json


def random_suffix_generator(size=5, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Clean runtime_properties
def clear_runtime_properties():
    for key in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties[key] = None


def request_failed(caller_string, raw_response):
    ctx.logger.info("In request_failed:{}".format(caller_string))
    response_get_info = raw_response.json()
    error_keys = ('error', u'error')
    code_keys = ('code', u'code')
    message_keys = ('message', u'message')
    for curr_error_key in error_keys:
        if curr_error_key in response_get_info:
            ctx.logger.info("Error occurred in {}".format(caller_string))
            curr_error = response_get_info[curr_error_key]
            for curr_code_key in code_keys:
                if curr_code_key in curr_error:
                    curr_code_value = curr_error[curr_code_key]
                    ctx.logger.info("Error code is {} in {}".format(curr_code_value,caller_string))
                    for curr_message_key in message_keys:
                        if curr_message_key in curr_error:
                            curr_message_value = curr_error[curr_message_key]
                            ctx.logger.info("Error message is {} in {}".format(curr_message_value,caller_string))
                            return True
                    return True
            return True

    return False


def resource_provisioned(caller_string, resource_name, current_response,save_response=False):
    if current_response.text:
        ctx.logger.info("{}:resource_provisioned {} resp is {}".format(caller_string, resource_name, current_response.text))
        ctx.logger.info("{}:resource_provisioned {} status code is {}".format(caller_string, resource_name, current_response.status_code))
        response_json = current_response.json()
        if u'properties' in response_json:
            curr_properties = response_json[u'properties']
            if u'provisioningState' in curr_properties:
                provisioning_state = curr_properties['provisioningState']
                ctx.logger.info("{}:resource_provisioned {} provisioningState is {}".format(caller_string, resource_name, provisioning_state))
                if u'Failed' == provisioning_state:
                    raise NonRecoverableError("{}:resource_provisioned checking {} provisioningState is {}".format(caller_string, resource_name, provisioning_state))
                elif u'Succeeded' == provisioning_state:
                    if save_response:
                        ctx.instance.runtime_properties[constants.CREATE_RESPONSE] = response_json
                    return True
                else:
                    return False
        else:
            ctx.logger.info("{}:resource_provisioned {} - There are no properties in the response".format(caller_string, resource_name))
            return False
    if current_response.status_code:
        ctx.logger.info("{}:resource_provisioned {} - Status code is {}".format(caller_string, resource_name, current_response.status_code))
    return False

def resource_was_created(headers, resource_name, check_resource_url, save_response=False):
    ctx.logger.info("In resource_was_created checking {}".format(resource_name))
    check_resource_response = requests.get(check_resource_url, headers=headers)
    return resource_provisioned('resource_was_created', resource_name, check_resource_response, save_response)


def check_or_create_resource(headers, resource_name, resource_params, check_resource_url, create_resource_url, resource_type, save_response=False):
    if constants.REQUEST_ACCEPTED in ctx.instance.runtime_properties:
        if resource_was_created(headers, resource_name, check_resource_url, save_response):
            ctx.logger.info("check_or_create_resource resource {} ({}) is ready ".format(resource_name,resource_type))
            return
        else:
            raise NonRecoverableError("check_or_create_resource: resource {} ({}) is not ready yet".format(resource_name, resource_type))
    elif create_resource(headers, resource_name, resource_params, create_resource_url, resource_type):
        if resource_was_created(headers, resource_name, check_resource_url, save_response):
            ctx.logger.info("_create_resource resource {} ({}) is ready ".format(resource_name, resource_type))
        else:
            raise NonRecoverableError("check_or_create_resource: resource {} ({}) is not ready yet".format(resource_name, resource_type))

def create_resource(headers, resource_name, resource_params, create_resource_url, resource_type):
    ctx.logger.info("_create_resource: creating resource {} ({})".format(resource_name,resource_type))
    response_resource = requests.put(url=create_resource_url, data=resource_params, headers=headers)
    if response_resource.text:
        ctx.logger.info("_create_resource {} ({}) response_resource.text is {}".format(resource_name, resource_type, response_resource.text))
        if request_failed("{}:{}".format('_create_resource', resource_name), response_resource):
            raise NonRecoverableError("_create_resource resource {} ({}) could not be created".format(resource_name, resource_type))

    if response_resource.status_code:
        ctx.logger.info("_create_resource:{} ({}) - Status code is {}".format(resource_name, resource_type, response_resource.status_code))
        if response_resource.status_code == 202:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        elif response_resource.status_code == 200:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        else:
            raise NonRecoverableError("check_or_create_resource:{} ({}) - Status code for resource {} is not 200 nor 202".format(resource_name, resource_type, response_resource.status_code))

    raise NonRecoverableError("check_or_create_resource:{} ({}) - No Status code for resource {}".format(resource_name, resource_type, response_resource.status_code))
