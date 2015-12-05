
import requests
import json
import time
from cloudify.exceptions import NonRecoverableError
from lockfile import LockFile
from cloudify import ctx, context
import constants
from cloudify.decorators import operation
import os.path
import utils


@operation
def initialize(use_client_file=True, start_retry_interval=30, **kwargs):
    generate_token(use_client_file=True, start_retry_interval=30, **kwargs)


def generate_token(use_client_file=True, start_retry_interval=30, **kwargs):
    endpoints, payload = _get_payload_endpoints(True)
    token, token_expires = _get_token_value_expiry(endpoints, payload)

    try:
        json_data = {}
        with open(constants.default_path_to_local_azure_token_file, 'w') as f:
            json_data["auth_token"] = token
            json_data["token_expires"] = token_expires
            f.seek(0)
            f.write(json.dumps(json_data))
            f.close()
    except:
        raise NonRecoverableError("Failures while creating or using {}".
            format(constants.default_path_to_local_azure_token_file))

    ctx.instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = token
    ctx.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = token_expires
    return token


def _get_token_value_expiry(endpoints, payload):
    response = requests.post(endpoints, data=payload).json()
    token = response['access_token']
    token_expires = response['expires_on']
    return token, token_expires


def _generate_token_if_expired(config_path, token, token_expires):
    timestamp = int(time.time())
    token_expires = int(token_expires)
    if token_expires - timestamp <= 600 or token_expires == 0 or token is None or token == "":
        ctx.logger.debug("Token expired: token_expires - timestamp={0}".format(token_expires-timestamp))
        endpoints, payload = _get_payload_endpoints()
        token, token_expires = _get_token_value_expiry(endpoints, payload)
        with open(config_path, 'r+') as f:
            json_data = json.load(f)
            json_data["auth_token"] = token
            json_data["token_expires"] = token_expires
            f.seek(0)
            ctx.logger.debug("Writing token         to {0}\n {1}".format(config_path, token))
            ctx.logger.debug("Writing token_expires to {0}\n {1}".format(config_path, token_expires))
            f.write(json.dumps(json_data))
            f.close()
    return token, token_expires


def get_auth_token(use_client_file=True, **kwargs):

    current_node = utils.get_node_or_source_node()
    if use_client_file:
        current_instance = utils.get_instance_or_source_instance()
        if constants.AUTH_TOKEN_VALUE in current_instance.runtime_properties:
            token = current_instance.runtime_properties[constants.AUTH_TOKEN_VALUE]
            if constants.AUTH_TOKEN_EXPIRY in current_instance.runtime_properties:
                token_expires = current_instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY]
            else:
                token_expires = 0
        else:
            token = None
            token_expires = 0

        if os.path.isfile(constants.default_path_to_local_azure_token_file):
            token, token_expires = _generate_token_if_expired(constants.default_path_to_local_azure_token_file,
                                                              token, token_expires)
            return token

    try:
        config_path = current_node.properties.get(constants.path_to_azure_conf_key) or constants.default_path_to_azure_conf
        lock = LockFile(config_path)
        lock.acquire()
        token, token_expires = _get_token_from_file(config_path)
    except:
        err_message = "Failures while locking or using {}".format(config_path)
        ctx.logger.debug(err_message)
        lock.release()
        raise NonRecoverableError(err_message)

    token, token_expires = _generate_token_if_expired(config_path, token, token_expires)
    lock.release()
    return token


@operation
def set_azure_config(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file(constants.REQUIRED_CONFIG_DATA, prefixed_keys=None, need_suffix=None)


def _get_payload_endpoints(store_in_runtime=False):

    tenant_id = utils.get_value_from_node('tenant_id', store_in_runtime)
    ctx.logger.info("_get_payload_endpoints: {0} is {1}".format('tenant_id', tenant_id))

    client_id = utils.get_value_from_node('client_id', store_in_runtime)
    ctx.logger.info("_get_payload_endpoints: {0} is {1}".format('client_id', client_id))

    aad_password = utils.get_value_from_node('aad_password', store_in_runtime)
    ctx.logger.info("_get_payload_endpoints: {0} is {1}".format('aad_password', aad_password))

    grant_type = utils.get_value_from_node('grant_type', store_in_runtime)
    ctx.logger.info("_get_payload_endpoints: {0} is {1}".format('grant_type', grant_type))

    username = utils.get_value_from_node('username', store_in_runtime)
    ctx.logger.info("_get_payload_endpoints: {0} is {1}".format('username', username))

    password = utils.get_value_from_node('password', store_in_runtime)
    ctx.logger.info("_get_payload_endpoints: {0} is {1}".format('password', password))


    endpoints = "{0}/{1}/oauth2/token".format(constants.login_url, tenant_id)

    payload = {
        'grant_type': grant_type,
        'resource': constants.resource,
        'client_id' :client_id
    }

    if grant_type == constants.CLIENT_CRED_GRANT_TYPE:
        payload['client_secret'] = aad_password
    else:
        payload['username'] = username
        payload['password'] = password

    return endpoints, payload


def _get_token_from_file(file_path):
    with open(file_path, 'r') as f:
        json_data = json.load(f)
        token_expires = json_data["token_expires"]
        token = json_data["auth_token"]
        f.close()
    return token, token_expires


def get_credentials():
    current_instance = utils.get_instance_or_source_instance()
    subscription_id = current_instance.runtime_properties['subscription_id']
    location = current_instance.runtime_properties['location']
    credentials = 'Bearer ' + get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    return headers, location, subscription_id


def _set_token_from_local_file(current_instance):
    ctx.logger.info("{} exists".format(constants.default_path_to_local_azure_token_file))
    token, token_expires = _get_token_from_file(constants.default_path_to_local_azure_token_file)
    ctx.logger.info("get_auth_token expiry is {} ".format(token_expires))
    current_instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = token
    current_instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = token_expires
    ctx.logger.info("get_auth_token token1 is {} ".format(token))
    return token

