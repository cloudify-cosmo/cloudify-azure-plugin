########
# Copyright (c) 2014-2019 Cloudify Platform Ltd. All rights reserved
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


import os
import pytest

from ecosystem_tests.dorkl import (
    basic_blueprint_test,
    cleanup_on_failure, prepare_test
)

'''Temporary until all the plugins in the bundle will 
released with py2py3 wagons'''
UT_VERSION = '1.23.5'
UT_WAGON = 'https://github.com/cloudify-incubator/cloudify-utilities-plugin/' \
           'releases/download/{v}/cloudify_utilities_plugin-{v}-centos' \
           '-Core-py27.py36-none-linux_x86_64.wgn'.format(v=UT_VERSION)
UT_PLUGIN = 'https://github.com/cloudify-incubator/cloudify-utilities-' \
            'plugin/releases/download/{v}/plugin.yaml'.format(v=UT_VERSION)
AN_VERSION = '2.9.2'
AN_WAGON = 'https://github.com/cloudify-cosmo/cloudify-ansible-plugin/' \
           'releases/download/{v}/cloudify_ansible_plugin-{v}-centos-' \
           'Core-py27.py36-none-linux_x86_64.wgn'.format(v=AN_VERSION)
AN_PLUGIN = 'https://github.com/cloudify-cosmo/cloudify-ansible-plugin' \
            '/releases/download/{v}/plugin.yaml'.format(v=AN_VERSION)
PLUGINS_TO_UPLOAD = [(UT_WAGON, UT_PLUGIN), (AN_WAGON, AN_PLUGIN)]
SECRETS_TO_CREATE = {
    'azure_subscription_id': False,
    'azure_tenant_id': False,
    'azure_client_id': False,
    'azure_client_secret': False,
    'azure_location': False,
}

prepare_test(plugins=PLUGINS_TO_UPLOAD, secrets=SECRETS_TO_CREATE,
             execute_bundle_upload=False)

blueprint_list = ['examples/blueprint-examples/hello-world-example/azure.yaml',
                  'examples/blueprint-examples/virtual-machine/azure-arm.yaml']


@pytest.fixture(scope='function', params=blueprint_list)
def blueprint_examples(request):
    dirname_param = os.path.dirname(request.param).split('/')[-1:][0]
    try:
        basic_blueprint_test(
            request.param,
            dirname_param,
            inputs='resource_prefix=azpl -i resource_suffix=test{0}'.format(
                os.environ['CIRCLE_BUILD_NUM']))
    except:
        cleanup_on_failure(dirname_param)
        raise


def test_blueprints(blueprint_examples):
    assert blueprint_examples is None
