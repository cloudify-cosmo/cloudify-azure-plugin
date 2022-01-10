import mock
import logging
from unittest import TestCase

from .. import decorators


class DecoratorTests(TestCase):

    @staticmethod
    def get_logger(logger_name=None):
        logger_name = logger_name or 'unit_test_logger'
        return logging.getLogger(logger_name)

    def test_get_custom_resource_config(self):
        runtime_props = {
            'resource_config': {
                'foo': 'bar'
            }
        }
        props = {
            'resource_config': {
                'foo': 'baz'
            }
        }
        self.assertEquals(
            decorators.get_custom_resource_config(runtime_props, props)['foo'],
            'bar')

    def test_configure_custom_resource(self):

        @decorators.configure_custom_resource
        def foo(*args, **kwargs):
            return args, kwargs

        props = {
            'client_config': {
                'subscription_id': 'foo',
            },
            'api_version': 'bar',
            'resource_config': 'foo',
            'operation_config': {
                'create': {
                    'resource_group_name': 'qux',
                    'parameters': {
                        'location': 'north'
                    }
                }
            }
        }
        node = mock.Mock(properties=props)
        instance = mock.Mock(runtime_properties={})
        operation = mock.Mock()
        operation.name = 'cloudify.interfaces.lifecycle.create'
        ctx = mock.Mock(node=node,
                        instance=instance,
                        operation=operation,
                        logger=self.get_logger())

        args = []
        kwargs = {
            'ctx': ctx
        }
        result = foo(*args, **kwargs)
        self.assertEquals(
            result,
            (
                (
                    ctx,
                    props['resource_config'],
                    props['operation_config']['create'],
                    props['client_config'],
                    props['api_version']
                ),
                {}
            )
        )
