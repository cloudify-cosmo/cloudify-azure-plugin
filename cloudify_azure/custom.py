
from contextlib import contextmanager

from .decorators import configure_custom_resource
from azure_sdk.resources.custom import CustomAzureResource

from cloudify.decorators import operation


@operation
@configure_custom_resource
def create(ctx, resource_cfg, operation_cfg, client, api):
    with custom_resource(client, ctx.logger, api, **resource_cfg) as resource:
        exists = resource.get()
        if exists:
            ctx.instance.runtime_properties['__RESOURCE_CREATED'] = False
            ctx.instance.runtime_properties['resource'] = exists
            return
        if not ctx.instance.runtime_properties.get('__RESOURCE_CREATED'):
            create_result = resource.create(**operation_cfg)
            ctx.instance.runtime_properties['create_result'] = create_result
            ctx.instance.runtime_properties['__RESOURCE_CREATED'] = True
        return ctx.operation.retry('Waiting for resource to be created.')


@operation
@configure_custom_resource
def update(ctx, resource_cfg, operation_cfg, client, api):
    with custom_resource(client, ctx.logger, api, **resource_cfg) as resource:
        if not operation_cfg:
            ctx.logger.error(
                'Skipping start operation, '
                'because no operation config for update was provided.')
        else:
            update_result = resource.update(**operation_cfg)
            ctx.instance.runtime_properties['update_result'] = update_result
        ctx.instance.runtime_properties['resource'] = resource.get()


@operation
@configure_custom_resource
def refresh(ctx, resource_cfg, _, client, api):
    with custom_resource(client, ctx.logger, api, **resource_cfg) as resource:
        ctx.instance.runtime_properties['resource'] = resource.get()


@operation
@configure_custom_resource
def delete(ctx, resource_cfg, operation_cfg, client, api):
    with custom_resource(client, ctx.logger, api, **resource_cfg) as resource:
        exists = resource.get()
        if not exists:
            del ctx.instance.runtime_properties['resource']
            ctx.instance.runtime_properties['__RESOURCE_DELETED'] = False
            return
        if not ctx.instance.runtime_properties.get('__RESOURCE_DELETED'):
            delete_result = resource.delete(**operation_cfg)
            ctx.instance.runtime_properties['delete_result'] = delete_result
            ctx.instance.runtime_properties['__RESOURCE_DELETED'] = True
        return ctx.operation.retry('Waiting for resource to be deleted.')


@contextmanager
def custom_resource(client, logger, api_version, **resource_cfg):
    yield CustomAzureResource(client, logger, api_version, **resource_cfg)
