# #######
# Copyright (c) 2020 - 2022 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import requests
from msrestazure.azure_exceptions import CloudError
from azure.core.exceptions import ResourceNotFoundError


def compose_not_found_cloud_error():
    response = requests.Response()
    response.status_code = 404
    message = 'resource not found'
    return CloudError(response, message)


def compose_other_not_found_error():
    return ResourceNotFoundError
