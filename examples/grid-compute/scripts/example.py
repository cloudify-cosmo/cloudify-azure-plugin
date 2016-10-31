from cloudify import ctx

ctx.logger.info('Hello, my instance ID is %s', ctx.instance.id)
