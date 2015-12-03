
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
def generate_token(use_client_file=True, **kwargs):
    endpoints, payload = _get_payload_endpoints()
    token, token_expires = _get_token_value_expiry(endpoints, payload)
    #ctx.logger.debug("In generate_token: token_expires {}".format(token_expires))
    try:
        json_data = {}
        with open(constants.default_path_to_local_azure_token_file, 'w') as f:
            json_data["auth_token"] = token
            json_data["token_expires"] = token_expires
            f.seek(0)
            f.write(json.dumps(json_data))
            f.close()
    except:
        raise NonRecoverableError("Failures while creating or using {}".format(constants.default_path_to_local_azure_token_file))

    ctx.instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = token
    ctx.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = token_expires
    return token


def _get_token_value_expiry(endpoints, payload):
    response = requests.post(endpoints, data=payload).json()
    token = response['access_token']
    token_expires = response['expires_on']
    #ctx.logger.debug("_get_token_value_expiry token is {} ".format(token))
    return token, token_expires


# If client file is used (use_client_file==True), it means that this is during bootstrap
def get_auth_token(use_client_file=True, **kwargs):
    #ctx.logger.debug("In auth.get_auth_token")
    current_instance = utils.get_instance_or_source_instance()
    if use_client_file:
        if constants.AUTH_TOKEN_VALUE in current_instance.runtime_properties:
            return current_instance.runtime_properties[constants.AUTH_TOKEN_VALUE]

        # Check if token file exists on the client's VM. If so, take the value from it and set it in the runtime
        #ctx.logger.debug("In auth.get_auth_token checking local azure file path {}".format(constants.path_to_local_azure_token_file))
        if os.path.isfile(constants.default_path_to_local_azure_token_file):
            # If you are here , it means that this is during bootstrap
            ctx.logger.info("{} exists".format(constants.default_path_to_local_azure_token_file))
            token, token_expires = get_token_from_client_file()
            ctx.logger.info("get_auth_token expiry is {} ".format(token_expires))
            current_instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = token
            current_instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = token_expires
            ctx.logger.info("get_auth_token token1 is {} ".format(token))
            return token

    # From here, this is not during bootstrap, which also means that this code runs on the manager's VM.
    try:
        current_node = utils.get_node_or_source_node()
        config_path = current_node.properties.get(constants.path_to_azure_conf_key) or constants.default_path_to_azure_conf
        #ctx.logger.debug("In auth.get_auth_token b4 locking {}".format(config_path))
        lock = LockFile(config_path)
        lock.acquire()
        #ctx.logger.debug("{} is locked".format(lock.path))
        with open(config_path, 'r') as f:
            json_data = json.load(f)
            token_expires = json_data["token_expires"]
            token = json_data["auth_token"]
            #ctx.logger.debug("get_auth_token token2 is {} ".format(token))
    except:
        lock.release()
        raise NonRecoverableError("Failures while locking or using {}".format(config_path))

    #ctx.logger.debug("In auth.get_auth_token b4 timestamp")
    timestamp = int(time.time())
    #ctx.logger.debug("In auth.get_auth_token timestamp is {}".format(timestamp))
    #ctx.logger.debug("In auth.get_auth_token token_expires1 is {}".format(token_expires))
    token_expires = int(token_expires)
    #ctx.logger.debug("In auth.get_auth_token token_expires2 is {}".format(token_expires))
    if token_expires-timestamp <= 600 or token_expires == 0 or token is None or token == "":
        #ctx.logger.debug("In auth.get_auth_token token_expires-timestamp {}".format(token_expires-timestamp))
        endpoints, payload = _get_payload_endpoints()
        token, token_expires = _get_token_value_expiry(endpoints, payload)
        #ctx.logger.debug("get_auth_token token3 is {} ".format(token))
        #ctx.logger.debug("In auth.get_auth_token b4 opening {}".format(config_path))
        with open(config_path, 'r+') as f:
            json_data = json.load(f)
            json_data["auth_token"] = token
            json_data["token_expires"] = token_expires
            f.seek(0)
            f.write(json.dumps(json_data))
            f.close()
    lock.release()
    #ctx.logger.debug("{} is released".format(lock.path))
    #ctx.logger.debug("get_auth_token token4 is {} ".format(token))
    return token


@operation
def set_auth_token(azure_config, **kwargs):
    # This method invoked only during bootstrap (it's a relationship interface)
    ctx.source.instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = ctx.target.instance.runtime_properties[constants.AUTH_TOKEN_VALUE]
    ctx.source.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = ctx.target.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY]


def _get_payload_endpoints():
    current_node = utils.get_node_or_source_node()
    client_id = current_node.properties['client_id']
    aad_password = current_node.properties['aad_password']
    tenant_id = current_node.properties['tenant_id']
    endpoints = constants.login_url+'/'+tenant_id+'/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': aad_password,
        'resource': constants.resource,
    }
    return endpoints, payload


def get_token_from_client_file():
    with open(constants.default_path_to_local_azure_token_file, 'r') as f:
        json_data = json.load(f)
        token_expires = json_data["token_expires"]
        token = json_data["auth_token"]
        f.close()

    #ctx.logger.debug("get_token_from_client_file expiry is {} ".format(token_expires))
    return token, token_expires


def get_credentials():
    current_node = utils.get_node_or_source_node()
    subscription_id = current_node.properties['subscription_id']
    location = current_node.properties['location']
    credentials = 'Bearer ' + get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
    return headers, location, subscription_id