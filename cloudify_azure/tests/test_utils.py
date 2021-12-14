import mock
import unittest

from msrestazure.azure_exceptions import CloudError

from cloudify_azure.utils import handle_task


class UtilsTests(unittest.TestCase):

    def test_handle_task(self):
        # TODO: Write tests for checking handle_task
        resource = mock.Mock()
        resource.task = mock.Mock(return_value='taco')
        resource_group_name = 'foo'
        name = 'bar'
        parent_name = 'baz'
        resource_task = 'task'
        handle_task(
            resource, resource_group_name, name, parent_name, resource_task)
        resource.task.assert_called_once_with(
            resource_group_name, parent_name, name)

        resource = mock.Mock()
        resource.task = mock.Mock(return_value='taco')
        resource_group_name = 'foo'
        name = 'bar'
        parent_name = None
        resource_task = 'task'
        handle_task(
            resource, resource_group_name, name, parent_name, resource_task)
        resource.task.assert_called_once_with(
            resource_group_name, name)

        resource = mock.Mock()
        resource.task = mock.Mock(return_value='taco')
        resource_group_name = 'foo'
        name = None
        parent_name = None
        resource_task = 'task'
        handle_task(
            resource, resource_group_name, name, parent_name, resource_task)
        resource.task.assert_called_once_with(resource_group_name)

        resource = mock.Mock()
        response = mock.Mock()
        response.status_code = 400
        side_effect = CloudError(response, 'taco')
        resource.task = mock.Mock(side_effect=side_effect)
        resource_group_name = 'foo'
        name = None
        parent_name = None
        resource_task = 'task'
        result = handle_task(
            resource, resource_group_name, name, parent_name, resource_task)
        resource.task.assert_called_once_with(resource_group_name)
        self.assertEquals(result, side_effect)
