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
    if 'use_external_resource' in ctx.node.properties and ctx.node.properties['use_external_resource']:
        if constants.EXISTING_SECURITY_GROUP_KEY in ctx.node.properties:
            existing_security_group_name = ctx.node.properties[constants.EXISTING_SECURITY_GROUP_KEY]
            if existing_security_group_name:
                security_group_exists = _get_security_group_name(existing_security_group_name)
                if not security_group_exists:
                    raise NonRecoverableError("Security group {} doesn't exist your Azure account".format(existing_security_group_name))
            else:
                raise NonRecoverableError("The value of '{}' in the input, is empty".format(constants.EXISTING_SECURITY_GROUP_KEY))
        else:
            raise NonRecoverableError("'{}' was specified, but '{}' doesn't exist in the input".format('use_external_resource',constants.EXISTING_SECURITY_GROUP_KEY))

        ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY] = ctx.node.properties[constants.EXISTING_SECURITY_GROUP_KEY]
        return
    
    credentials='Bearer '+ auth.get_auth_token()
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
        #response_nsg = requests.put(url=security_group_url, data=security_group_params, headers=headers)
        #print response_nsg.text
    except:
        ctx.logger.info("Security group " +security_group_name + "could not be created.")
        sys.exit(1)

  
@operation
def delete_security_group(**_):
    #vm_name=server.vm_name
    subscription_id = ctx.node.properties['subscription_id']
    #resource_group_name = resourcegroup.resource_group_name
  
    credentials='Bearer '+ auth.get_auth_token()
    headers = {"Content-Type": "application/json", "Authorization": credentials}
  

    try:
        ctx.logger.info("Deleting Security Group")
        #security_group_url=constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version
        #response_nsg = requests.delete(url=security_group_url,headers=headers)
        #print(response_nic.text)
    except:
        ctx.logger.info("Security Group " + security_group_name + " could not be deleted.")
        sys.exit(1)

    utils.clear_runtime_properties()


def _validate_node_properties(key, ctx_node_properties):
      if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
