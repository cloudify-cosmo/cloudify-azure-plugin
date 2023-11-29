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
'''Microsoft Azure plugin for Cloudify package config'''

import os
import re
import sys
import pathlib
from setuptools import setup, find_packages


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir, 'cloudify_azure/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()

install_requires = [
    'cryptography',
    'requests>=2.23.0',
    'urllib3>=1.25.3',
    # stating from azure v5.0.0 we need to add azure modules like this
    'azure-mgmt-web==0.46.0',
    # When upgrading compute package version, update cloudify_
    # azure/resources/compute/virtualmachine/virtualmachine_utils.py
    # ::check_if_configuration_changed props list, a
    # according to available api versions.
    'azure-mgmt-batch==16.0.0',
    'azure-mgmt-compute==25.0.0',
    'azure-mgmt-containerservice==17.0.0',
    'azure-mgmt-network==19.3.0',
    'azure-mgmt-storage==19.1.0',
    'azure-storage-blob',
    'azure-storage-common==2.1.0',
    'azure-mgmt-resource==20.0.0',
    'azure-common==1.1.28',
    'msrestazure==0.6.4',
    'azure-identity==1.8.0',
]

if sys.version_info.major == 3 and sys.version_info.minor == 6:
    install_requires += [
        'cloudify-common>=4.5,<7.0',
        'cloudify-utilities-plugins-sdk>=0.0.91',  # includes YAML
    ]
    packages = [
        'azure_sdk',
        'cloudify_azure',
        'azure_sdk.resources',
        'azure_sdk.resources.app_service',
        'azure_sdk.resources.compute',
        'azure_sdk.resources.network',
        'azure_sdk.resources.storage',
        'cloudify_azure.resources',
        'cloudify_azure.workflows',
        'cloudify_azure.resources.app_service',
        'cloudify_azure.resources.compute',
        'cloudify_azure.resources.network',
        'cloudify_azure.resources.storage',
        'cloudify_azure.resources.compute.virtualmachine',
        'cloudify_azure.tests.resources',
    ]
else:
    install_requires += [
        'fusion-common',
        'fusion-mgmtworker',
        'deepdiff==5.7.0',
        'cloudify-utilities-plugins-sdk',
    ]
    packages = find_packages(exclude=['tests*'])


setup(
    name='cloudify-azure-plugin',
    version=get_version(),
    license='LICENSE',
    packages=packages,
    description='Cloudify plugin for Microsoft Azure',
    install_requires=install_requires
)
