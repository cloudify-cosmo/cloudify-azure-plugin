from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
import random
import string

def get_resource_group_name():
    if ctx.node.properties['exsisting_resource_group_name']:
        return ctx.node.properties['exsisting_resource_group_name']
        
def get_storage_account_name():
    if ctx.node.properties['exsisting_storage_account_name']:
        return ctx.node.properties['exsisting_storage_account_name']
        
def get_nic_name():
    if ctx.node.properties['exsisting_nic_name']:
        return ctx.node.properties['exsisting_nic_name']
        
def get_vnet_name():
    if ctx.node.properties['exsisting_vnet_name']:
        return ctx.node.properties['exsisting_vnet_name']
        
def get_public_ip_name():
    if ctx.node.properties['exsisting_public_ip_name']:
        return ctx.node.properties['exsisting_public_ip_name']

def use_external_resource(ctx_node_properties):
"""Checks if use_external_resource node property is true,
logs the ID and answer to the debug log,
and returns boolean False (if not external) or True.
:param node_properties: The ctx node properties for a node.
:param ctx: The Cloudify ctx context.
:returns boolean: False if not external.
"""
    if not ctx_node_properties['use_external_resource']:
	ctx.logger.debug(
	'Using Cloudify resource_name: {0}.'
	.format(ctx_node_properties['resource_name']))
	return False
    else:
	ctx.logger.debug(
	'Using external resource_name: {0}.'
	.format(ctx_node_properties['resource_name']))
	return True
	

def random_suffix_generator(size=5, chars=string.ascii_uppercase + string.digits):
     return ''.join(random.choice(chars) for _ in range(size))
