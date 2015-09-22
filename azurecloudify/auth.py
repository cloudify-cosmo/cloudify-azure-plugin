
import requests
import json
import urllib2
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
    response = requests.post(endpoints, data=payload).json()
    return response['access_token']


