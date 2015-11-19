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

# instance module constants
INSTANCE_STATE_STARTED = 16
INSTANCE_STATE_TERMINATED = 48
INSTANCE_STATE_STOPPED = 80
TIME_DELAY = 10


CREATING = 'Creating'
UPDATING = 'Updating'
FAILED = 'Failed'
SUCCEEDED = 'Succeeded'
DELETING = 'Deleting'

REQUEST_SUCCEEDED = 'Succeeded'
REQUEST_IN_PROGRESS = 'InProgress'
REQUEST_FAILED = 'Failed'

TOKEN_URL = 'https://login.windows.net/common/oauth2/token'
RESOURCE_CONNECTION_URL = 'https://management.core.windows.net/'
AZURE_API_URL = 'https://management.azure.com'

AZURE_API_VERSION_01 = '2015-01-01'
AZURE_API_VERSION_04_PREVIEW = '2014-04-01-preview'
AZURE_API_VERSION_05_preview = '2015-05-01-preview'
AZURE_API_VERSION_06 = '2015-06-15'


USERNAME_KEY = 'username'
PASSWORD_KEY = 'password'
LOCATION_KEY = 'location'


RESOURCE_GROUP_KEY = 'resource_group_name'



PATH_TO_AZURE_CONF_KEY = "azure_conf_file_path"
SUBSCRIPTION_KEY = 'subscription_id'
CLIENT_ID_KEY = 'client_id'
AAD_PASSWORD_KEY = 'aad_password'
TENANT_ID_KEY = 'tenant_id'

OK_STATUS_CODE = 200