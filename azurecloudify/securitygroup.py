import requests
import json
import constants
import sys
import os
import auth
import utils
from cloudify.exceptions import NonRecoverableError, RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
import azurerequests


@operation
def creation_validation(**_):
    for property_key in constants.RESOURCE_GROUP_REQUIRED_PROPERTIES:
        _validate_node_properties(property_key, ctx.node.properties)


@operation
def create_security_group(**_):
    utils.set_runtime_properties_from_file()
    security_group_name = utils.set_resource_name(_get_security_group_name, 'SECUIRTY_GROUP',
                                             constants.SECURITY_GROUP_KEY, constants.EXISTING_SECURITY_GROUP_KEY,
                                             constants.SECURITY_GROUP_PREFIX)
    if security_group_name is None:
        # Using an existing public ip, so don't create anything
        return

    headers, location, subscription_id = auth.get_credentials()
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    if constants.SECURITY_GROUP_KEY in ctx.instance.runtime_properties:
        security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
    else:
        random_suffix_value = utils.random_suffix_generator()
        security_group_name = constants.SECURITY_GROUP_PREFIX+random_suffix_value

    security_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version_network

    ctx.logger.info("Creating a new security group: {0}".format(security_group_name))
    security_group_json = _get_security_group_json(location)
    security_group_params = _get_security_group_params(security_group_json)
    response_nsg = requests.put(url=security_group_url, data=security_group_params, headers=headers)
    ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY] = security_group_name
    return response_nsg.status_code


@operation
def verify_provision(start_retry_interval, **kwargs):
    security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
    curr_status = get_provisioning_state()
    if curr_status != constants.SUCCEEDED:
        return ctx.operation.retry(
            message='Waiting for the security group ({0}) to be provisioned'.format(security_group_name),
            retry_after=start_retry_interval)


@operation
def set_dependent_resources_names(azure_config, **kwargs):
    utils.write_target_runtime_properties_to_file([constants.RESOURCE_GROUP_KEY])


@operation
def delete_security_group(start_retry_interval=30, **kwargs):
    delete_current_security_group(start_retry_interval, **kwargs)
    utils.clear_runtime_properties()


def delete_current_security_group(start_retry_interval=30, **kwargs):
    if constants.USE_EXTERNAL_RESOURCE in ctx.node.properties and ctx.node.properties[constants.USE_EXTERNAL_RESOURCE]:
        ctx.logger.info("An existing security group was used, so there's no need to delete")
        return

    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
    security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]
    headers, location, subscription_id = auth.get_credentials()
    try:
        ctx.logger.info("Deleting Security Group: {0}".format(security_group_name))
        security_group_url = constants.azure_url+'/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/microsoft.network/networkSecurityGroups/'+security_group_name+'?api-version='+constants.api_version_network
        response_nsg = requests.delete(url=security_group_url, headers=headers)
        return azurerequests.check_delete_response(response_nsg, start_retry_interval,
                                                   'delete_current_security_group', security_group_name,
                                                   'security_group')
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


def _get_security_group_json(location):
    security_group_json = {
        "location": location,
        "properties": {
            "securityRules": []
        }
    }
    return security_group_json


def _get_security_group_params(security_group_json):

    # This should be in a loop (there may be more than one rule)
    # Issue #29 :
    # https://github.com/cloudify-cosmo/cloudify-azure-plugin/issues/29
    # Issue #30 :
    # https://github.com/cloudify-cosmo/cloudify-azure-plugin/issues/30
    ######################################################################
    protocol = ctx.node.properties['security_group_protocol']
    source_port_range = ctx.node.properties['security_group_sourcePortRange']
    destination_port_range = ctx.node.properties['security_group_destinationPortRange']
    source_address_prefix = ctx.node.properties['security_group_sourceAddressPrefix']
    destination_address_prefix = ctx.node.properties['security_group_destinationAddressPrefix']
    access_security_group = ctx.node.properties['security_group_access']
    security_group_priority = ctx.node.properties['security_group_priority']
    security_group_direction = ctx.node.properties['security_group_direction']

    current_rule = {
        "name": "mySecGrpRule",
        "properties": {
            "description": "My Security Group Rule Description",
            "protocol": protocol,
            "sourcePortRange": source_port_range,
            "destinationPortRange": destination_port_range,
            "sourceAddressPrefix": source_address_prefix,
            "destinationAddressPrefix": destination_address_prefix,
            "access": access_security_group,
            "priority": security_group_priority,
            "direction": security_group_direction
        }
    }
    security_group_json['properties']['securityRules'].append(current_rule)
    # End of loop
    ######################################################################

    security_group_params = json.dumps(security_group_json)
    return security_group_params


def get_provisioning_state(**_):
    resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]

    security_group_name = ctx.instance.runtime_properties[constants.SECURITY_GROUP_KEY]

    ctx.logger.info("Searching for security group {0}".format(security_group_name))
    headers, location, subscription_id = auth.get_credentials()

    security_group_url = "{0}/subscriptions/{1}/resourceGroups/{2}/providers/Microsoft.network/" \
                          "networkSecurityGroups/{3}?api-version={4}".format(constants.azure_url,
                                subscription_id, resource_group_name, security_group_name,
                                constants.api_version_network)

    return azurerequests.get_provisioning_state(headers, resource_group_name, security_group_url)

