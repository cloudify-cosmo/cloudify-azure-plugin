import random
import string

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
