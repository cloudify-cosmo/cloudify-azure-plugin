
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
    path = '/root/token.txt'
    try:
        with open(path, 'r') as f:
            e = f.readline()
            token = f.readline()
    except:
        print 'no token file'
        e = 0
        token = None
    #open file and check, extract both
    timestamp = int(time.time())
    if(e-timestamp <= 600 or e == 0 or token == None):
        response = requests.post(endpoints, data=payload).json()
        token = response['access_token']
        e = response['expires_on']
        with open(path, 'w+') as f:
            f.writelines([e, '\n', token])
    return token


