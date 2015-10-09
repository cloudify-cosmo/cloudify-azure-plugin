
import requests
import json
import urllib2
import time
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
    """
    try:
         with open(constants.path_to_azure_conf+'azure_config.json', 'r') as f:
            token_expires = f.readline()
            token = f.readline()
    except:
        print 'no token file'
        token_expires = 0
        token = None
    #open file and check, extract both
    timestamp = int(time.time())
    if(e-timestamp <= 600 or token_expires == 0 or token == None):
        response = requests.post(endpoints, data=payload).json()
        token = response['access_token']
        token_expires = response['expires_on']
        with open(constants.path_to_azure_conf+'azure_config.json', 'w+') as f:
            f.writelines([token_expires, '\n', token])
    """        
    return token


