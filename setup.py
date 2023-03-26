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
import pathlib
from setuptools import setup
from setuptools import find_packages


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version():
    current_dir = pathlib.Path(__file__).parent.resolve()
    with open(os.path.join(current_dir, 'cloudify_azure/__version__.py'),
              'r') as outfile:
        var = outfile.read()
        return re.search(r'\d+.\d+.\d+', var).group()


general_requirements = [
    'cloudify-common>=4.5',
    'cloudify-utilities-plugins-sdk>=0.0.91',  # includes YAML
    'requests>=2.23.0',
    'urllib3>=1.25.3',
    'cryptography==3.3.2'
]

azure_requirements = [
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

setup(
    name='cloudify-azure-plugin',
    version=get_version(),
    license='LICENSE',
    packages=find_packages(exclude=['tests*']),
    description='Cloudify plugin for Microsoft Azure',
    install_requires=general_requirements + azure_requirements
)
