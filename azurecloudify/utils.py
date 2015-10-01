from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

def get_resource_name():
    if ctx.node.properties['resource_name']:
        return ctx.node.properties['resource_name']


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
	
def set_external_resource_name(value, ctx_instance, external=True):
	"""Sets the EXTERNAL_RESOURCE_NAME runtime_property for a Node-Instance.
	:param value: the desired EXTERNAL_RESOURCE_NAME runtime_property
	:param ctx: The Cloudify ctx context.
	:param external: Boolean representing if it is external resource or not.
	"""
	if not external:
	    resource_type = 'Cloudify'
	else:
	    resource_type = 'external'
            ctx.logger.info('Using {0} resource: {1}'.format(resource_type, value))
	    ctx.instance.runtime_properties['resource_name'] = value
