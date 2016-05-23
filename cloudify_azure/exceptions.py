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
    Exceptions
    ~~~~~~~~~~
    Microsoft Azure plugin for Cloudify exception handling
'''


class UnauthorizedRequest(Exception):
    '''
        Azure has not authorized an action or has
        rejected an authorization attempt.

    :param object exc: Exception information
    :type object: dict or string
    :raises: :exc:`Exception`
    '''
    def __init__(self, exc):
        self.exc = exc if isinstance(exc, dict) else {'error': exc}
        Exception.__init__(self, exc)

    def __str__(self):
        return repr('Unauthorized attempt to access an Azure resource')


class InvalidCredentials(Exception):
    '''
        An authorization interface recieved missing or malformed credentials

    :param string msg: Exception message
    :param dict exc: Exception information
    :raises: :exc:`Exception`
    '''
    def __init__(self, msg, exc=None):
        self.msg = msg
        self.exc = exc if isinstance(exc, dict) else dict()
        Exception.__init__(self, exc)

    def __str__(self):
        return repr('Invalid credentials recieved. {0}'.format(self.msg))


class UnexpectedResponse(Exception):
    '''
        Azure returned an unexpected response to a request.

    :param string msg: Exception message
    :param dict exc: Exception information
    :raises: :exc:`Exception`
    '''
    def __init__(self, msg, exc=None):
        self.msg = msg
        self.exc = exc if isinstance(exc, dict) else dict()
        Exception.__init__(self, exc)

    def __str__(self):
        return repr('Unexpected response recieved. {0}'.format(self.msg))
