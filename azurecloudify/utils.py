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
        ctx.instance.runtime_properties.pop(key)


def check_api_response(caller_string, current_response, return_action):
    if 1 == 2:
        return "OK"
    if 3 == constants.THROW_NON_RECOVERABLE:
        raise NonRecoverableError("sdfdsfsdfsd")


def request_failed(caller_string, raw_response):
    ctx.logger.info("Checking if request_failed:{0}".format(caller_string))
    response_get_info = raw_response.json()
    error_keys = ('error', u'error')
    code_keys = ('code', u'code')
    message_keys = ('message', u'message')
    for curr_error_key in error_keys:
        if curr_error_key in response_get_info:
            ctx.logger.info("Error occurred in {0}".format(caller_string))
            curr_error = response_get_info[curr_error_key]
            for curr_code_key in code_keys:
                if curr_code_key in curr_error:
                    curr_code_value = curr_error[curr_code_key]
                    ctx.logger.info("Error code is {0} in {1}".format(curr_code_value, caller_string))
                    for curr_message_key in message_keys:
                        if curr_message_key in curr_error:
                            curr_message_value = curr_error[curr_message_key]
                            ctx.logger.info("Error message is {0} in {1}".format(curr_message_value,caller_string))
                            return True
                    return True
            return True

    return False


def resource_provisioned(caller_string, resource_name, current_response,save_response=False):
    if current_response.text:
        ctx.logger.info("{0}:resource_provisioned {1} resp is {2}".format(caller_string, resource_name, current_response.text))
        ctx.logger.info("{0}:resource_provisioned {1} status code is {2}".format(caller_string, resource_name, current_response.status_code))
        response_json = current_response.json()
        if u'properties' in response_json:
            curr_properties = response_json[u'properties']
            if u'provisioningState' in curr_properties:
                provisioning_state = curr_properties['provisioningState']
                ctx.logger.info("{0}:resource_provisioned {1} provisioningState is {2}".format(caller_string, resource_name, provisioning_state))
                if u'Failed' == provisioning_state:
                    raise NonRecoverableError("{0}:resource_provisioned checking {1} provisioningState is {2}".format(caller_string, resource_name, provisioning_state))
                elif u'Succeeded' == provisioning_state:
                    if save_response:
                        ctx.logger.info("{0}:resource_provisioned {1}  - Saving json {2}".format(caller_string, resource_name, str(response_json)))
                        ctx.instance.runtime_properties[constants.CREATE_RESPONSE] = response_json
                    return True
                else:
                    return False
        else:
            ctx.logger.info("{0}:resource_provisioned {1} - There are no properties in the response".format(caller_string, resource_name))
            return False
    if current_response.status_code:
        ctx.logger.info("{0}:resource_provisioned {1} - Status code is {2}".format(caller_string, resource_name, current_response.status_code))
    return False


def resource_was_created(headers, resource_name, check_resource_url, save_response=False):
    ctx.logger.info("In resource_was_created checking {0}".format(resource_name))
    check_resource_response = requests.get(check_resource_url, headers=headers)
    return resource_provisioned('resource_was_created', resource_name, check_resource_response, save_response)


def check_or_create_resource(headers, resource_name, resource_params, check_resource_url, create_resource_url, resource_type, save_response=False):
    if constants.REQUEST_ACCEPTED in ctx.instance.runtime_properties:
        if resource_was_created(headers, resource_name, check_resource_url, save_response):
            ctx.logger.info("check_or_create_resource resource {0} ({1}) is ready ".format(resource_name,resource_type))
            return
        else:
            raise RecoverableError("check_or_create_resource: resource {0} ({1}) is not ready yet".format(resource_name, resource_type))
    elif create_resource(headers, resource_name, resource_params, create_resource_url, resource_type):
        if resource_was_created(headers, resource_name, check_resource_url, save_response):
            ctx.logger.info("_create_resource resource {0} ({1}) is ready ".format(resource_name, resource_type))
        else:
            raise RecoverableError("check_or_create_resource: resource {0} ({1}) is not ready yet".format(resource_name, resource_type))


def create_resource(headers, resource_name, resource_params, create_resource_url, resource_type):
    ctx.logger.info("_create_resource: creating resource {0} ({1})".format(resource_name, resource_type))
    response_resource = requests.put(url=create_resource_url, data=resource_params, headers=headers)
    if response_resource.text:
        ctx.logger.info("_create_resource {0} ({1}) response_resource.text is {2}".format(resource_name, resource_type, response_resource.text))
        if request_failed("{0}:{1}".format('_create_resource', resource_name), response_resource):
            raise NonRecoverableError("_create_resource resource {0} ({1}) could not be created".format(resource_name, resource_type))

    if response_resource.status_code:
        ctx.logger.info("_create_resource:{0} ({1}) - Status code is {2}".format(resource_name, resource_type, response_resource.status_code))
        if response_resource.status_code == 202:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        elif response_resource.status_code == 201:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        elif response_resource.status_code == 200:
            ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED] = True
            return True
        else:
            raise NonRecoverableError("check_or_create_resource:{0} ({1}) - Status code for resource {2} is not 200 nor 202".format(resource_name, resource_type, response_resource.status_code))

    raise NonRecoverableError("check_or_create_resource:{0} ({1}) - No Status code for resource {2}".format(resource_name, resource_type, response_resource.status_code))


def set_resource_name(get_resource_func, resource_desc,
                      runtime_resource_key, properties_resource_key, resource_key_prefix):
    if runtime_resource_key in ctx.instance.runtime_properties:
        return ctx.instance.runtime_properties[runtime_resource_key]

    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        if properties_resource_key in ctx.node.properties and ctx.node.properties[properties_resource_key]:
            existing_resource_name = ctx.node.properties[properties_resource_key]
            if not get_resource_func(existing_resource_name):
                raise NonRecoverableError("{0} {1} doesn't exist in your Azure account".format(resource_desc, existing_resource_name))
        else:
            raise NonRecoverableError("'{0}' was specified, but '{1}' is either empty or doesn't exist in the input".format(constants.USE_EXTERNAL_RESOURCE, properties_resource_key))

        ctx.instance.runtime_properties[runtime_resource_key] = existing_resource_name
        ctx.logger.info("Using an existing {0}:{1}".format(resource_desc, existing_resource_name))
        resource_name_to_be_used_or_created = None
    elif properties_resource_key in ctx.node.properties and ctx.node.properties[properties_resource_key]:
        required_resource_name = ctx.node.properties[properties_resource_key]
        ctx.logger.info("required_resource_name is:{0}, type is:{1}".format(required_resource_name, resource_desc))
        if get_resource_func(required_resource_name):
            raise NonRecoverableError("{0} {1} already exists in your Azure account".format(resource_desc, required_resource_name))
        else:
            resource_name_to_be_used_or_created = required_resource_name
    else:
        random_suffix_value = random_suffix_generator()
        resource_name_to_be_used_or_created = "{0}{1}".format(resource_key_prefix, random_suffix_value)

    ctx.logger.info("resource_name_to_be_used_or_created is:{0}, type is:{1}".format(resource_name_to_be_used_or_created, resource_desc))
    return resource_name_to_be_used_or_created


def validate_node_properties(required_properties, ctx_node_properties):
    for property_key in required_properties:
        if property_key not in ctx_node_properties:
            raise NonRecoverableError('{0} is a required input. Unable to create.'.format(property_key))


