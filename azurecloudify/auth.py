
import requests
import json
import time
from cloudify.exceptions import NonRecoverableError
from lockfile import LockFile
from cloudify import ctx, context
import constants
from cloudify.decorators import operation


@operation
def get_token_from_client_credentials(use_file=True, **kwargs):
    return get_token(use_file)

def get_token(use_file=True, **kwargs):
    if not use_file and constants.AUTH_TOKEN_VALUE in ctx.instance.runtime_properties:
        return ctx.instance.runtime_properties[constants.AUTH_TOKEN_VALUE]

    client_id = ctx.node.properties['client_id']
    aad_password = ctx.node.properties['aad_password']
    tenant_id = ctx.node.properties['tenant_id']
    endpoints = constants.login_url+'/'+tenant_id+'/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': aad_password,
        'resource': constants.resource,
    }

    if not use_file:
        return _get_token_and_set_runtime(endpoints, payload)

    try:
        lock = LockFile(constants.path_to_azure_conf)
        lock.acquire()
        print lock.path, 'is locked.'
        with open(constants.path_to_azure_conf, 'r') as f:
            json_data = json.load(f)
            token_expires = json_data["token_expires"]
            token = json_data["auth_token"]
    except:
        raise NonRecoverableError("Failures while locking or using {}".format(constants.path_to_azure_conf))

    timestamp = int(time.time())
    token_expires = int(token_expires)
    if token_expires-timestamp <= 600 or token_expires == 0 or token is None or token == "":
        response = requests.post(endpoints, data=payload).json()
        token = response['access_token']
        token_expires = response['expires_on']
        with open(constants.path_to_azure_conf, 'r+') as f:
            json_data = json.load(f)
            json_data["auth_token"] = token
            json_data["token_expires"] = token_expires
            f.seek(0)
            f.write(json.dumps(json_data))
    lock.release()
    print lock.path, 'is released.'
    return token


def _get_token_and_set_runtime(endpoints, payload):
    ctx.logger.info("In _get_token_and_set_runtime")
    response = requests.post(endpoints, data=payload).json()
    ctx.instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = response['access_token']
    ctx.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = response['expires_on']
    ctx.logger.info("In _get_token_and_set_runtime: token expiry is {}".format(response['expires_on']))
    return ctx.instance.runtime_properties[constants.AUTH_TOKEN_VALUE]

@operation
def set_auth_token(**kwargs):
    # This method invoked only during bootstrap
    ctx.source.instance.runtime_properties[constants.AUTH_TOKEN_VALUE] = ctx.target.instance.runtime_properties[constants.AUTH_TOKEN_VALUE]
    ctx.source.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY] = ctx.target.instance.runtime_properties[constants.AUTH_TOKEN_EXPIRY]

def get_auth_token():
    if constants.AUTH_TOKEN_VALUE in ctx.instance.runtime_properties:
        return ctx.instance.runtime_properties[constants.AUTH_TOKEN_VALUE]
    return get_token(True)