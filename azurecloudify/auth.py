
import requests
import json
import urllib2
import time
from lockfile import LockFile
from cloudify import ctx
import constants

def get_token_from_client_credentials():
 
    client_id = ctx.node.properties['client_id']
    aad_password = ctx.node.properties['aad_password']
    tenant_id = ctx.node.properties['tenant_id']
    endpoints =constants.login_url+'/'+tenant_id+'/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': aad_password,
        'resource': constants.resource,
    }
    azure_conf_exists = os.path.isfile(constants.path_to_azure_conf)
    if azure_conf_exists:
     try:
          lock = LockFile(constants.path_to_azure_conf)
          lock.acquire()
          print lock.path, 'is locked.'
          with open(constants.path_to_azure_conf, 'r') as f:
              json_data = json.load(f)
              token_expires = json_data["token_expires"]
              token = json_data["auth_token"]
     except:
         print 'no token file'
         token_expires = 0
         token = None
    #open file and check, extract both
    timestamp = int(time.time())
    token_expires=int(token_expires)
    if(token_expires-timestamp <= 600 or token_expires == 0 or token == None or token == ""):
        response = requests.post(endpoints, data=payload).json()
        token = response['access_token']
        token_expires = response['expires_on']
        if azure_conf_exists:
         with open(constants.path_to_azure_conf, 'r+') as f:
             json_data = json.load(f)
             json_data["auth_token"] = token
             json_data["token_expires"] = token_expires
             f.seek(0)
             f.write(json.dumps(json_data))
         lock.release()
         print lock.path, 'is released.'
         
    return token


