# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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
'''
    resources.Base
    ~~~~~~~~~~~~~~
    Microsoft Azure API abstraction layer
'''

# HTTP status codes
import httplib
# JSON serializing
import json
import yaml
# Exception handling
from cloudify.exceptions import NonRecoverableError, RecoverableError
# API connection
from cloudify_azure import connection, utils
# Exceptions
from cloudify_azure.exceptions import UnexpectedResponse
# Runtime properties
from cloudify import ctx


class Resource(object):
    '''
        Microsoft Azure base resource interface

    .. warning::
        This interface should only be instantiated from
        within a Cloudify Lifecycle Operation

    :param string name: Human-readable name of the child resource
    :param string endpoint: Partial endpoint for making resource requests
    :param string api_version: API version to use for all requests
    :param `logging.Logger` logger:
        Parent logger for the class to use. Defaults to `ctx.logger`
    :param object _ctx: Cloudify Context object with *node* and
        *instance* properties. This is used to override the global
        *ctx* object to handle situations such as relationship
        operations where a source or target interface is used instead
        of a global one
    '''
    def __init__(self, name, endpoint,
                 api_version=None, logger=None,
                 _ctx=ctx):
        # Set the active context
        self.ctx = _ctx
        # Configure logger
        self.log = utils.create_child_logger(
            'resources.{0}'.format(name.replace(' ', '')),
            plogger=logger)
        # Set up labeling
        self.name = name
        # Build the partial endpoint
        self.endpoint = endpoint
        # Get a connection
        self.client = connection.AzureConnection(
            api_version=api_version,
            logger=self.log,
            _ctx=self.ctx)

    def get(self, name=None):
        '''
            Gets details about an existing resource

        :param string name: Name of the existing resource
        :returns: Response data from the Azure API call
        :rtype: dict
        :raises: :exc:`cloudify.exceptions.RecoverableError`,
                 :exc:`cloudify.exceptions.NonRecoverableError`,
                 :exc:`requests.RequestException`
        '''
        self.log.info('Retrieving {0} "{1}"'.format(self.name, name))
        # Make the request
        if name:
            url = '{0}/{1}'.format(self.endpoint, name)
        else:
            url = self.endpoint
        res = self.client.request(
            method='get',
            url=url)
        # Convert headers from CaseInsensitiveDict to Dict
        headers = dict(res.headers)
        self.log.debug('headers: {0}'.format(
            utils.secure_logging_content(headers)))
        # Check the response
        # HTTP 202 (ACCEPTED) - The operation has started but is asynchronous
        if res.status_code == httplib.ACCEPTED:
            if not headers.get('location'):
                raise RecoverableError(
                    'HTTP 202 ACCEPTED but no Location header present')
            self.ctx.instance.runtime_properties['async_op'] = headers
            return ctx.operation.retry(
                'Operation: "{0}" started'
                .format(self.get_operation_id(headers)),
                retry_after=self.get_retry_after(headers))
        # HTTP 200 (OK) - The resource already exists
        elif res.status_code == httplib.OK:
            return res.json()
        # If Azure sent a 400, we're sending bad data
        if res.status_code == httplib.BAD_REQUEST:
            self.log.info('BAD REQUEST: response: {}'.format(res.content))
            raise UnexpectedResponse(
                'Recieved HTTP 400 BAD REQUEST', res.json())
        # If Azure sent a 404, the resource doesn't exist (yet?)
        if res.status_code == httplib.NOT_FOUND:
            raise RecoverableError(
                '{0} "{1}" doesn\'t exist (yet?)'
                .format(self.name, name))
        # All other errors will be treated as recoverable
        if res.status_code != httplib.CREATED:
            raise RecoverableError(
                'Expected HTTP status code {0}, recieved {1}'
                .format(httplib.CREATED, res.status_code))
        return res.json()

    def create(self, name, params=None):
        '''
            Creates a new resource

        :param string name: Name of the new resource
        :param dict params: Parameters to be passed as-is to the Azure API
        :raises: :exc:`cloudify.exceptions.RecoverableError`,
                 :exc:`cloudify.exceptions.NonRecoverableError`,
                 :exc:`requests.RequestException`
        '''
        self.log.info('Creating {0} "{1}"'.format(self.name, name))
        self.ctx.instance.runtime_properties['async_op'] = None
        # Sanitize input data
        params = self.sanitize_json_input(params)
        # Make the request
        res = self.client.request(
            method='put',
            url='{0}/{1}'.format(self.endpoint, name),
            json=params)
        # Convert headers from CaseInsensitiveDict to Dict
        headers = dict(res.headers)
        self.log.debug('headers: {0}'.format(
            utils.secure_logging_content(headers)))
        # Check the response
        # HTTP 201 (CREATED) - The operation succeeded
        if res.status_code == httplib.CREATED:
            if headers.get('azure-asyncoperation'):
                self.ctx.instance.runtime_properties['async_op'] = headers
                return ctx.operation.retry(
                    'Operation: "{0}" started'
                    .format(self.get_operation_id(headers)),
                    retry_after=self.get_retry_after(headers))
            return
        # HTTP 202 (ACCEPTED) - The operation has started but is asynchronous
        elif res.status_code == httplib.ACCEPTED:
            if not headers.get('location'):
                raise RecoverableError(
                    'HTTP 202 ACCEPTED but no Location header present')
            self.ctx.instance.runtime_properties['async_op'] = headers
            return ctx.operation.retry(
                'Operation: "{0}" started'
                .format(self.get_operation_id(headers)),
                retry_after=self.get_retry_after(headers))
        # HTTP 200 (OK) - The resource already exists
        elif res.status_code == httplib.OK:
            if headers.get('azure-asyncoperation'):
                self.ctx.instance.runtime_properties['async_op'] = headers
                return ctx.operation.retry(
                    'Operation: "{0}" started'
                    .format(self.get_operation_id(headers)),
                    retry_after=self.get_retry_after(headers))
            self.log.warn('{0} already exists. Using resource.'
                          .format(self.name))
            return
        # HTTP 400 (BAD_REQUEST) - We're sending bad data
        elif res.status_code == httplib.BAD_REQUEST:
            self.log.info('BAD REQUEST: response: {}'.format(
                utils.secure_logging_content(res.content)))
            raise UnexpectedResponse(
                'Recieved HTTP 400 BAD REQUEST', res.json())
        # HTTP 409 (CONFLICT) - Operation failed
        elif res.status_code == httplib.CONFLICT:
            raise NonRecoverableError(
                'Operation failed. (code={0}, data={1})'
                .format(res.status_code, res.text))
        # All other errors will be treated as recoverable
        raise RecoverableError(
            'Expected HTTP status code {0}, recieved {1}'
            .format(httplib.CREATED, res.status_code))

    def update(self, name, params, force=False):
        '''
            Updates an existing resource

        :param string name: Name of the resource
        :param dict params: Parameters to update the resource with
        :param boolean force: Forces the params to be sent without merging
            with the resources' existing data
        :raises: :exc:`cloudify.exceptions.RecoverableError`,
                 :exc:`cloudify.exceptions.NonRecoverableError`,
                 :exc:`requests.RequestException`
        '''
        if not force:
            # Get the existing data (since partial updates seem to
            # be in a questionable state on Azure's side of things)
            data = self.get(name)
            # Updating the data with our new data
            params = utils.dict_update(data, params)
        self.log.info('Updating {0} "{1}"'.format(self.name, name))
        self.ctx.instance.runtime_properties['async_op'] = None
        # Sanitize input data
        params = self.sanitize_json_input(params)
        # Make the request
        res = self.client.request(
            method='put',
            url='{0}/{1}'.format(self.endpoint, name),
            json=params)
        # Convert headers from CaseInsensitiveDict to Dict
        headers = dict(res.headers)
        self.log.debug('headers: {0}'.format(
            utils.secure_logging_content(headers)))
        # Check the response
        # HTTP 202 (ACCEPTED) - The operation has started but is asynchronous
        if res.status_code == httplib.ACCEPTED:
            if not headers.get('location'):
                raise RecoverableError(
                    'HTTP 202 ACCEPTED but no Location header present')
            self.ctx.instance.runtime_properties['async_op'] = headers
            return ctx.operation.retry(
                'Operation: "{0}" started'
                .format(self.get_operation_id(headers)),
                retry_after=self.get_retry_after(headers))
        # HTTP 200 (OK) - The resource already exists
        elif res.status_code == httplib.OK:
            if headers.get('azure-asyncoperation'):
                self.ctx.instance.runtime_properties['async_op'] = headers
                return ctx.operation.retry(
                    'Operation: "{0}" started'
                    .format(self.get_operation_id(headers)),
                    retry_after=self.get_retry_after(headers))
            self.log.warn('{0} already exists. Using resource.'
                          .format(self.name))
            return
        # HTTP 400 (BAD_REQUEST) - We're sending bad data
        elif res.status_code == httplib.BAD_REQUEST:
            self.log.info('BAD REQUEST: response: {}'.format(
                utils.secure_logging_content(res.content)))
            raise UnexpectedResponse(
                'Recieved HTTP 400 BAD REQUEST', res.json())
        # HTTP 409 (CONFLICT) - Operation failed
        elif res.status_code == httplib.CONFLICT:
            raise NonRecoverableError(
                'Operation failed. (code={0}, data={1})'
                .format(res.status_code, res.text))
        # All other errors will be treated as recoverable
        elif res.status_code != httplib.CREATED:
            raise RecoverableError(
                'Expected HTTP status code {0}, recieved {1}'
                .format(httplib.CREATED, res.status_code))

    def delete(self, name):
        '''
            Deletes an existing resource

        :param string name: Name of the existing resource
        :raises: :exc:`cloudify.exceptions.RecoverableError`,
                 :exc:`cloudify.exceptions.NonRecoverableError`,
                 :exc:`requests.RequestException`
        '''
        self.log.info('Deleting {0} "{1}"'.format(self.name, name))
        self.ctx.instance.runtime_properties['async_op'] = None
        # Make the request
        res = self.client.request(
            method='delete',
            url='{0}/{1}'.format(self.endpoint, name))
        # Convert headers from CaseInsensitiveDict to Dict
        headers = dict(res.headers)
        self.log.debug('headers: {0}'.format(
            utils.secure_logging_content(headers)))
        # HTTP 200 (OK) - The operation is successful and complete
        if res.status_code == httplib.OK:
            return
        # HTTP 204 (NO_CONTENT) - The resource doesn't exist
        elif res.status_code == httplib.NO_CONTENT:
            return
        # HTTP 202 (ACCEPTED) - The operation has started but is asynchronous
        elif res.status_code == httplib.ACCEPTED:
            if not headers.get('location'):
                raise RecoverableError(
                    'HTTP 202 ACCEPTED but no Location header present')
            self.ctx.instance.runtime_properties['async_op'] = headers
            return ctx.operation.retry(
                'Operation: "{0}" started'
                .format(self.get_operation_id(headers)),
                retry_after=self.get_retry_after(headers))
        # HTTP 400 (BAD_REQUEST) - We're sending bad data
        elif res.status_code == httplib.BAD_REQUEST:
            self.log.info('BAD REQUEST: response: {}'.format(
                utils.secure_logging_content(res.content)))
            raise UnexpectedResponse(
                'Recieved HTTP 400 BAD REQUEST', res.json())
        # HTTP 409 (CONFLICT) - Operation failed
        elif res.status_code == httplib.CONFLICT:
            raise NonRecoverableError(
                'Operation failed. (code={0}, data={1})'
                .format(res.status_code, res.text))
        # All other errors will be treated as recoverable
        elif res.status_code != httplib.CREATED:
            raise RecoverableError(
                'Expected HTTP status code {0}, recieved {1}'
                .format(httplib.CREATED, res.status_code))

    def exists(self, name=None):
        '''
            Determines if a resource exists or not

        :param string name: Name of the existing resource
        :returns: True if resource exists, False if it doesn't
        :rtype: boolean
        :raises: :exc:`cloudify_azure.exceptions.UnexpectedResponse`,
                 :exc:`requests.RequestException`
        '''
        self.log.info('Checking {0} "{1}"'.format(self.name, name))
        # Make the request
        if name:
            url = '{0}/{1}'.format(self.endpoint, name)
        else:
            url = self.endpoint
        res = self.client.request(
            method='get',
            url=url)
        # Convert headers from CaseInsensitiveDict to Dict
        headers = dict(res.headers)
        self.log.debug('headers: {0}'.format(
            utils.secure_logging_content(headers)))
        # Check the response
        # HTTP 202 (ACCEPTED) - An asynchronous operation has started
        if res.status_code == httplib.ACCEPTED:
            return True
        # HTTP 200 (OK) - The resource already exists
        elif res.status_code == httplib.OK:
            return True
        # If Azure sent a 404, the resource doesn't exist (yet?)
        if res.status_code == httplib.NOT_FOUND:
            return False
        raise UnexpectedResponse(
            'Recieved unexpected HTTP ({0}) response'
            .format(res.status_code), res.json())

    def operation_complete(self, op_info):
        '''
            Checks the status of an asynchronous operation

        :param dict op_info: Long-running operation headers
        :raises: :exc:`cloudify.exceptions.RecoverableError`,
                 :exc:`cloudify.exceptions.NonRecoverableError`,
                 :exc:`requests.RequestException`
        '''
        # Get the operation ID
        op_id = op_info.get('x-ms-request-id', 'not-reported')
        # Make the request
        self.log.info('Checking status of operation "{0}"'
                      .format(op_id))
        op_url = op_info.get('location') or \
            op_info.get('azure-asyncoperation')
        res = self.client.request(method='get',
                                  url=op_url)
        # Convert headers from CaseInsensitiveDict to Dict
        headers = dict(res.headers)
        self.log.debug('headers: {0}'.format(
            utils.secure_logging_content(headers)))
        # HTTP 200 (OK) - Operation is successful and complete
        if res.status_code == httplib.OK:
            if self.validate_res_json(res) == 'InProgress':
                return ctx.operation.retry(
                    'Operation: "{0}" still pending'
                    .format(self.get_operation_id(headers)),
                    retry_after=self.get_retry_after(headers))
            self.ctx.instance.runtime_properties['async_op'] = None
            return
        # Clear the async state
        self.ctx.instance.runtime_properties['async_op'] = None
        # HTTP 202 (ACCEPTED) - Operation is still pending
        if res.status_code == httplib.ACCEPTED:
            if not headers.get('location'):
                raise RecoverableError(
                    'HTTP 202 ACCEPTED but no Location header present')
            self.ctx.instance.runtime_properties['async_op'] = headers
            return ctx.operation.retry(
                'Operation: "{0}" still pending'
                .format(self.get_operation_id(headers)),
                retry_after=self.get_retry_after(headers))
        # HTTP 409 (CONFLICT) - Operation failed
        elif res.status_code == httplib.CONFLICT:
            raise NonRecoverableError(
                'Operation "{0}" failed. (code={1}, data={2})'
                .format(op_id, res.status_code, res.text))
        # HTTP 500 (INTERNAL_SERVER_ERROR) - Operation time out
        elif res.status_code == httplib.INTERNAL_SERVER_ERROR:
            # Preserve op_info in case it's really just a time-out
            self.ctx.instance.runtime_properties['async_op'] = op_info
            return ctx.operation.retry(
                'Operation: "{0}" still pending'
                .format(self.get_operation_id(headers)),
                retry_after=self.get_retry_after(headers))
        res.raise_for_status()

    def get_retry_after(self, headers):
        '''
            Gets the amount of seconds to wait before retrying an operation

        :param dict headers: :class:`requests.Response` headers
        :returns: Seconds to wait before retrying an operation
        :rtype: int
        '''
        return utils.get_retry_after(_ctx=self.ctx) or \
            int(headers.get('retry-after', 60))

    @staticmethod
    def validate_res_json(res):
        '''Validates that a status exists'''
        try:
            return res.json().get('status')
        except ValueError:
            res.raise_for_status()
        return

    @staticmethod
    def get_operation_id(headers):
        '''
            Gets the asynchronous operation ID as reported by Azure

        :param dict headers: :class:`requests.Response` headers
        :returns: Operation ID
        :rtype: string
        '''
        return headers.get('x-ms-request-id', 'not-reported')

    @staticmethod
    def sanitize_json_input(us_data):
        '''
            Sanitizes data before going to Requests. This mostly
            handles cases where there are mixed-encoded objects
            where part of the object is ASCII/UTF-8 and the other
            part is Unicode.

        :param obj us_data: JSON-serializable Python object
        :returns: UTF-8 JSON object
        :rtype: JSON object
        '''
        if not us_data:
            return None
        if not isinstance(us_data, dict) and not isinstance(us_data, list):
            return None
        return yaml.safe_load(
            json.dumps(us_data, ensure_ascii=True).encode('utf8'))
