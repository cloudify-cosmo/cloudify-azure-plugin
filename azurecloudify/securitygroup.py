import requests
from requests import Request,Session,Response
import json
import constants
import sys
import os
import auth
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation



def create_network_security_group(**_):
    for property_key in constants.SECURITY_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    vm_name=ctx.node.properties['vm_name']
    security_group_name=vm_name+'_nsg'
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = vm_name+'_resource_group'
    location = ctx.node.properties['location']
    security_group_url= constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version

    credentials='Bearer '+ auth.get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

  if 1:
    try:
      ctx.logger.info("Creating new security group:" + security_group_name)
      security_group_params=json.dumps({
    "location":"West US",
    "tags":{
        "key":"value"
    },
    "properties":{
        "securityRules":[
            {
                "name":"myNsRule",
                "properties":{
                    "description":"description-of-this-rule",
                    "protocol": "Tcp",
                    "sourcePortRange":"65000",
                    "destinationPortRange":"60000",
                    "sourceAddressPrefix":"*",
                    "destinationAddressPrefix":"*",
                    "access":"Allow",
                    "priority":100,
                    "direction":"Inbound"
                }
            }
         ]
      }
   })
    response_nsg = requests.put(url=security_group_url, data=security_group_params, headers=headers)
    print response_nsg.text

  except:
    ctx.logger.info("Security group " +security_group_name + "could not be created.")
    sys.exit(1)
else:
  ctx.logger.info("Security group"  +security_group_name + "has already been provisioned by another user.")
  
  
  
@operation
def delete_security_group(**_):
  vm_name=ctx.node.properties['vm_name']
  security_group_name=vm_name+'_nsg'
  subscription_id = ctx.node.properties['subscription_id']
  resource_group_name = vm_name+'_resource_group'
  
  credentials='Bearer '+ auth.get_token_from_client_credentials()
  headers = {"Content-Type": "application/json", "Authorization": credentials}
  
  if 1:
    try:
      ctx.logger.info("Deleting Security Group")
      security_group_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version
      response_nsg = requests.delete(url=security_group_url,headers=headers)
      print(response_nic.text)
    except:
      ctx.logger.info("Security Group " + security_group_name + " could not be deleted.")
      sys.exit(1)
  else:
    ctx.logger.info("Security Group " + security_group_name + " does not exist.")
    
def _validate_node_properties(key, ctx_node_properties):
      if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
  
  
    
    
    
