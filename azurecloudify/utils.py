from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
import random
import string


def use_external_resource(ctx_node_properties):
"""Checks if use_external_resource node property is true,
logs the ID and answer to the debug log,
and returns boolean False (if not external) or True.
:param node_properties: The ctx node properties for a node.
:param ctx: The Cloudify ctx context.
:returns boolean: False if not external.
"""
    if not ctx_node_properties['use_external_resource']:
	ctx.logger.info('Creating a new resource')
	return False
    else:
	ctx.logger.info('Using external resource')
	return True
	

def random_suffix_generator(size=5, chars=string.ascii_lowercase + string.digits):
     return ''.join(random.choice(chars) for _ in range(size))
