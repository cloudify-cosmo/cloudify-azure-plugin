import random
import string
from cloudify import ctx

"""
def use_external_resource(ctx_node_properties):

    if not ctx_node_properties['use_external_resource']:
	ctx.logger.info('Creating a new resource')
	return False
    else:
	ctx.logger.info('Using external resource')
	return True
"""	


def random_suffix_generator(size=5, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


# Clean runtime_properties
def clear_runtime_properties():
    for key in ctx.instance.runtime_properties:
        ctx.instance.runtime_properties = None