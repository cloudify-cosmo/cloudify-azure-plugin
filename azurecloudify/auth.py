
import requests
import json
from cloudify import ctx
import constants

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
    response =json.loads(requests.post(endpoints, data=payload).json())
    token=response['access_token']
    print(token)
    return token


"""  
def _generate_credentials(**_):
    client_id=ctx.node.properties['client_id']
    tenant_id=ctx.node.properties['tenant_id']
    username=ctx.node.properties['username']
    password=ctx.node.properties['password']
    url='https://login.microsoftonline.com/'+tenant_id+'/oauth2/token'
    headers ={"Content-Type":"application/x-www-form-urlencoded"}
    body = "grant_type=password&username="+username+"&password="+password+"&client_id="+client_id+"&resource=https://management.core.windows.net/"
    req = Request(method="POST",url=url,data=body)
    req_prepped = req.prepare()
    s = Session()
    res = Response()
    res = s.send(req_prepped)
    s=res.content
    end_of_leader = s.index('access_token":"') + len('access_token":"')
    start_of_trailer = s.index('"', end_of_leader)
    token=s[end_of_leader:start_of_trailer]
    credentials = "Bearer " + token
    head = {"Content-Type": "application/json", "Authorization": credentials}
    return head
"""
