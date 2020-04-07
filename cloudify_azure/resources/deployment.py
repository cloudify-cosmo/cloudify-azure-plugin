# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
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

import ast
import json

from cloudify._compat import PY2
from cloudify.decorators import operation
from cloudify import exceptions as cfy_exc
from cloudify._compat import (urlopen, urlparse, text_type)

from cloudify_azure import constants

from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode

from cloudify_azure.auth.oauth2 import to_service_principle_credentials


def is_url(string):
    parse_info = urlparse('{0}'.format(string))
    return parse_info.scheme and (parse_info.netloc or parse_info.path)


class Deployment(object):

    def __init__(self, logger, credentials, name, timeout=None):
        self.resource_group = name
        self.logger = logger
        self.timeout = timeout or 900
        self.resource_verify = bool(credentials.get('endpoint_verify', True))
        self.credentials = to_service_principle_credentials(
            client_id='{0}'.format(credentials['client_id']),
            certificate='{0}'.format(credentials.get('certificate', '')),
            thumbprint='{0}'.format(credentials.get('thumbprint', '')),
            cloud_environment='{0}'.format(
                credentials.get('cloud_environment', '')),
            secret='{0}'.format(credentials.get('client_secret', '')),
            tenant='{0}'.format(credentials['tenant_id']),
            verify=self.resource_verify,
            endpoints_active_directory='{0}'.format(credentials.get(
                'endpoints_active_directory', '')),
            resource='{0}'.format(
                credentials.get('endpoint_resource',
                                constants.OAUTH2_MGMT_RESOURCE),)
        )
        self.client = ResourceManagementClient(
            self.credentials,
            '{0}'.format(credentials['subscription_id']),
            base_url='{0}'.format(
                credentials.get('endpoints_resource_manager',
                                constants.CONN_API_ENDPOINT)))

        self.logger.info("Using subscription: {0}".format(
            credentials['subscription_id']))

    def create(self, location):
        """Deploy the template to a resource group."""
        self.logger.info("Creating resource group: {0}".format(
            self.resource_group))
        self.client.resource_groups.create_or_update(
            self.resource_group,
            {
                "location": location
            },
            verify=self.resource_verify
        )

    def get(self):
        return self.client.deployments.get(
            self.resource_group,  # resource group name
            self.resource_group,  # deployment name
        )

    @staticmethod
    def format_params(params):
        # We need to traverse the parameters' dictionary
        # and convert all unicode strings to regular strings
        def convert_value(v):
            if v is None:
                return None
            if isinstance(v, int) or \
                    isinstance(v, bool) or \
                    isinstance(v, text_type):
                return v
            if (PY2 and isinstance(v, unicode)) or isinstance(v, text_type):
                return ast.literal_eval(repr(v))
            if isinstance(v, dict):
                for k, y in v.items():
                    v[k] = convert_value(y)
                return v
            raise Exception("Unhandled data type: {0} ({1})".format(
                type(v), '{0}'.format(v)))

        if params is None:
            return None
        for k, v in params.items():
            updated_value = convert_value(v)
            params[k] = {"value": updated_value}
        return params

    def update(self, template, params):

        self.logger.info("Creating deployment: {0}".format(
            self.resource_group))

        deployment_properties = {
            'mode': DeploymentMode.incremental,
            'template': template,
            'parameters': self.format_params(params)
        }

        deployment_async_operation = self.client.deployments.create_or_update(
            self.resource_group,  # resource group name
            self.resource_group,  # deployment name
            deployment_properties,
            verify=self.resource_verify
        )
        self.logger.info(
            "Waiting for deployment to finish (timeout: {0} seconds)".format(
                repr(self.timeout)))

        deployment_async_operation.wait(timeout=self.timeout)

    def delete(self):
        """Destroy the given resource group"""
        self.logger.info("Deleting resource group: {0}".format(
            self.resource_group))
        deployment_async_operation = self.client.resource_groups.delete(
            self.resource_group,
            verify=self.resource_verify
        )
        self.logger.info(
            "Waiting for deployment to be deleted (timeout: {0} "
            "seconds)".format(repr(self.timeout)))
        deployment_async_operation.wait(timeout=self.timeout)


def get_template(ctx, properties):
    template = properties.get('template')
    if template:
        if isinstance(template, (text_type, bytes)):
            ctx.logger.info("Template provided as a string in blueprint")
            ctx.logger.debug("Template string: %s", template)
            template = json.loads(template)
        elif not isinstance(template, dict):
            raise cfy_exc.NonRecoverableError(
                "Provided template is neither a string nor a dict "
                "(type: {0}, value: {1})".format(
                    type(template), repr(template)))
    else:
        template = properties.get('template_file')
        if template is None:
            raise cfy_exc.NonRecoverableError(
                "Deployment template not provided. Please specify "
                "either 'template' or 'template_file'."
            )
        ctx.logger.info("Template file provided: %s", template)
        if is_url(template):
            f = urlopen(template)
            try:
                template = json.load(f)
            finally:
                f.close()
        else:
            template = ctx.get_resource(template)
            template = json.loads(template)
    return template


@operation(resumable=True)
def create(ctx, **kwargs):
    properties = {}
    properties.update(ctx.node.properties)
    properties.update(kwargs)

    deployment = Deployment(ctx.logger, properties['azure_config'],
                            properties['name'],
                            timeout=properties.get('timeout'))

    if ctx.node.properties.get('use_external_resource', False):
        ctx.logger.info("Using external resource")
    else:
        # load template
        template = get_template(ctx, properties)
        ctx.logger.debug("Parsed template: %s", json.dumps(template, indent=4))

        # create deployment
        deployment.create(location=properties['location'])
        ctx.instance.runtime_properties['resource_id'] = properties['name']

        # update deployment
        deployment.update(template=template,
                          params=properties.get('params', {}))

    resource = deployment.get()
    ctx.instance.runtime_properties['outputs'] = resource.properties.outputs


@operation(resumable=True)
def delete(ctx, **kwargs):
    if ctx.node.properties.get('use_external_resource', False):
        return
    properties = {}
    properties.update(ctx.node.properties)
    properties.update(kwargs)
    deployment = Deployment(ctx.logger, properties['azure_config'],
                            ctx.instance.runtime_properties['resource_id'],
                            timeout=properties.get('timeout'))
    deployment.delete()
