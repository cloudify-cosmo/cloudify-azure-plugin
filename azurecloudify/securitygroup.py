import requests
from requests import Request,Session,Response
import json
import constants
import sys
import os
import auth
from resourcegroup import *
from storageaccount import *
import utils
from cloudify.exceptions import NonRecoverableError
from cloudify import ctx
from cloudify.decorators import operation

RANDOM_SUFFIX_VALUE = utils.random_suffix_generator()
security_group_name = ctx.node.properties['security_group_name']+RANDOM_SUFFIX_VALUE

@operation
def create_network_security_group(**_):
    for property_key in constants.SECURITY_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)
    vm_name=server.vm_name
    subscription_id = ctx.node.properties['subscription_id']
    resource_group_name = resourcegroup.resource_group_name
    location = ctx.node.properties['location']
    security_group_url= constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version

    credentials='Bearer '+ auth.get_token_from_client_credentials()
    headers = {"Content-Type": "application/json", "Authorization": credentials}

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
                        "sourcePortRange":constants.sourcePortRange,
                        "destinationPortRange":constants.destinationPortRange,
                        "sourceAddressPrefix":"*",
                        "destinationAddressPrefix":"*",
                        "access":"Allow",
                        "priority":constants.priority,
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
  vm_name=server.vm_name
  subscription_id = ctx.node.properties['subscription_id']
  resource_group_name = resourcegroup.resource_group_name
  
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
  
  
    
    
    
