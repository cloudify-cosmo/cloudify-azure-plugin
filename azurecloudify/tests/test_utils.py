########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# Built-in Imports
import importlib
from time import sleep

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError

from azurecloudify import constants


def validate_node_property(key, ctx_node_properties):
    """Checks if the node property exists in the blueprint.

    :param key: The key to find.
    :param ctx_node_properties: The dictionary to search
    :raises NonRecoverableError: if key not in the node's properties
    """
    if key not in ctx_node_properties:
        raise NonRecoverableError(
            '{0} is a required input. Unable to create.'.format(key))


def log_available_resources(list_of_resources):
    """This logs a list of available resources.

    :param list_of_resources:
    """
    message = 'Available resources: \n'

    for resource in list_of_resources:
        message = '{0}{1}\n'.format(message, resource)

    ctx.logger.debug(message)


def unassign_runtime_property_from_resource(property_name, ctx_instance):
    """Pops a runtime_property and reports to debug.

    :param property_name: The runtime_property to remove.
    :param ctx_instance: The CTX Node-Instance Context.
    :param ctx:  The Cloudify ctx context.
    """
    value = ctx_instance.runtime_properties.pop(property_name)
    ctx.logger.debug(
        'Unassigned {0} runtime property: {1}'.format(property_name, value))




def get_target_property(ctx, relationship_name, property_name):
    """Get a runtime_property from the target of a relationship.

    :param ctx:  The Cloudify ctx context.
    :param relationship_name: The relationship's name.
    :param property_name: The runtime_property's key to get.
    :return: the runtime_property's value.
    """
    # FIX: this function will only return the first property found for
    # the first corresponding relationship found. Maybe return an array
    # of properties if more than one relationship correspond.
    if ctx.instance.relationships:
        for relationship in ctx.instance.relationships:
            if relationship.type == relationship_name:
                for property in relationship.target.instance.runtime_properties:
                    if property_name == property:
                        return relationship.target.instance.runtime_properties[property]
        raise NonRecoverableError(
                'Relationship property {} for {} has not been found.'.format(
                        property_name, ctx.node.name)
                )
    else:
        raise NonRecoverableError('Missing relationship for {}.'.format(
                                                        ctx.node.name)
                                  )


def get_targets_properties(ctx, relationship_name, properties_name):
    """Get all runtime_property from targets of a relationship.

    :param ctx:  The Cloudify ctx context.
    :param relationship_name: The relationship's name.
    :param property_name: The runtime_property's key to get.
    :return: the runtime_property's value.
    """
    properties_list = []
    if ctx.instance.relationships:
        for relationship in ctx.instance.relationships:
            if relationship.type == relationship_name:
                properties_dict = {}
                for property_name in properties_name:
                    for property in relationship.target.instance.runtime_properties:
                        if property == property_name:
                            properties_dict[property_name]=relationship.target.instance.runtime_properties[property_name]
                            break
                properties_list.append(properties_dict)
        if not properties_list:
            raise NonRecoverableError(
                'Relationship property {} for {} has not been found.'.format(
                    property_name, ctx.node.name)
            )
        else:
            ctx.logger.debug('properties_list: {}'.format(properties_list))
            return properties_list
    else:
        raise NonRecoverableError('Missing relationship for {}.'.format(
            ctx.node.name)
        )


def wait_status(ctx, resource, expected_status=constants.SUCCEEDED, timeout=600):
    """ A helper to send request to Azure. The operation status
    is check to monitor the request. Failures are managed too.

    :param ctx: The Cloudify context to log information.
    :param resource: The resource to waiting for.
    :param expected_status: The expected status for the operation.
    :param timeout: Maximum time to wait in seconds.
    """
    module = importlib.import_module('azurecloudify.{0}'.format(resource),
                                     package=None
                                     )
    ctx.logger.debug('Waiting for status {0} for {1}...'.format(expected_status, resource))

    attempt_index = 1
    waiting_time = 0
    status = getattr(module, 'get_provisioning_state')(ctx=ctx)
    ctx.logger.info('{0} status is {1}...'.format(resource, status))
    while (status != expected_status) and (status != constants.FAILED) and (waiting_time <= timeout):
        waiting_time += constants.WAITING_TIME
        sleep(constants.WAITING_TIME)
        status = getattr(module, 'get_provisioning_state')(ctx=ctx)
        attempt_index += 1
        ctx.logger.info('{0} status is {1} - attempt #{2}...'.format(resource, status, attempt_index))
    
    if status != expected_status:
        if waiting_time >= timeout:
            message = 'Timeout occurs while waiting status {0} for {1}...'.format(expected_status,resource)
        else:
            message = '*** Failed waiting {0} for {1}: {2} ***'.format(expected_status, resource, status)
        raise NonRecoverableError(message)
    else:
        ctx.logger.info("** {0}'s status ({1}) is as expected. **".format(resource, status))


class WindowsAzureError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return 'Error {}: {}.'.format(self.code, self.message)