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


@operation
def creation_validation(**_):
    for property_key in constants.RESOURCE_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_security_group(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
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
    
    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    random_suffix_value = utils.random_suffix_generator()
    security_group_name = constants.SECURITY_GROUP_PREFIX+random_suffix_value
    security_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version
    try:
        ctx.logger.info("Creating a new security group: {0}".format(security_group_name))
        security_group_params = json.dumps({
        "location": location,
        "tags": {
            "key": "value"
        },
        "properties": {
            "securityRules": [
                {
                    "name": constants.nsg_rule_name,
                    "properties": {
                        "description": constants.NSG_RULES_DESCRIPTION,
                        "protocol": ctx.node.properties['security_group_protocol'],
                        "sourcePortRange": ctx.node.properties['security_group_sourcePortRange'] ,
                        "destinationPortRange": ctx.node.properties['security_group_destinationPortRange'],
                        "sourceAddressPrefix": ctx.node.properties['security_group_sourceAddressPrefix'],
                        "destinationAddressPrefix": ctx.node.properties['security_group_destinationAddressPrefix'],
                        "access": ctx.node.properties['security_group_access'],
                        "priority": ctx.node.properties['security_group_priority'],
                        "direction": ctx.node.properties['security_group_direction']
                    }
                }
             ]
          }
        })
        response_nsg = requests.put(url=security_group_url, data=security_group_params, headers=headers)
        if response_nsg.text:
            ctx.logger.info("create_security_group {0} response_nsg.text is {1}".format(security_group_name, response_nsg.text))
            if utils.request_failed("{0}:{1}".format('create_security_group', security_group_name), response_nsg):
                raise NonRecoverableError("create_security_group {0} could not be created".format(security_group_name))

    except:
        ctx.logger.info("Security Group {0} could not be created".format(security_group_name))
        raise NonRecoverableError("Security Group {} could not be created".format(security_group_name))


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    ctx.source.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = ctx.target.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]


@operation
def delete_security_group(**_):
    delete_current_security_group()
    utils.clear_runtime_properties()


def delete_current_security_group(**_):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing security group was used, so there's no need to delete")
        return

    security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    try:
        ctx.logger.info("Deleting Security Group: {0}".format(security_group_name))
        security_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+security_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version
        response_nsg = requests.delete(url=security_group_url, headers=headers)
        print(response_nsg.text)
    except:
        ctx.logger.info("Security Group {0} could not be deleted.".format(security_group_name))
        

def _validate_node_properties(key, ctx_node_properties):
    if key not in ctx_node_properties:
        raise NonRecoverableError('{0} is a required input. Unable to create.'.format(key))
        
        
def _get_security_group_name(security_group_name):  
    if constants.RESOURCE_GROUP_KEY in ctx.instance.runtime_properties:
        resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    else:
        raise RecoverableError("{} is not in public ip runtime_properties yet.".format(constants.RESOURCE_GROUP_KEY))
    headers, location, subscription_id = auth.get_credentials()
    list_security_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups?api-version='+constants.api_version
    response_get_security_group = requests.get(url=list_security_group_url, headers=headers)
   
    if security_group_name in response_get_security_group.text:
        return True
    else:
        ctx.logger.info("Security group {} does not exist".format(security_group_name))
        return False
