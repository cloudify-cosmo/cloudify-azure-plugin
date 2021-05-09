# #######
# Copyright (c) 2018-2020 Cloudify Platform Ltd. All rights reserved
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

from msrestazure.azure_exceptions import CloudError

from cloudify import exceptions as cfy_exc
from cloudify.decorators import operation

from cloudify_azure import constants

from cloudify_azure import utils
from azure_sdk.resources.app_service.publishing_user import PublishingUser


@operation(resumable=True)
def set_user(ctx, user_details, **kwargs):
    azure_config = utils.get_client_config(ctx.node.properties)
    api_version = \
        ctx.node.properties.get('api_version', constants.API_VER_APP_SERVICE)
    publishing_user = PublishingUser(azure_config, ctx.logger, api_version)
    if not user_details:
        raise cfy_exc.NonRecoverableError(
            "check user_details value")
    try:
        publishing_user.set_or_update(user_details)
    except CloudError as cr:
        raise cfy_exc.NonRecoverableError(
            "set publishing_user '{0}' "
            "failed with this error : {1}".format(user_details,
                                                  cr.message)
            )
