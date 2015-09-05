
import requests




def get_token_from_client_credentials():
 
    client_id = ctx.node.properties['client_id']
    client_secret = ctx.node.properties['password']
    tenant_id = ctx.node.properties['tenant_id']
    endpoints = 'https://login.microsoftonline.com/'+tenant_id+'/oauth2/token'
    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'resource': constants.resource,
    }
    response = requests.post(endpoints, data=payload).json()
    token=response['access_token']
    print(token)
    return token
