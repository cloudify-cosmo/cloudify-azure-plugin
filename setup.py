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

from setuptools import setup

setup(
    name='cloudify-azure-plugin',
    version='2.1.10',
    license='LICENSE',
    packages=[
        'cloudify_azure',
        'cloudify_azure.auth',
        'cloudify_azure.resources',
        'cloudify_azure.resources.compute',
        'cloudify_azure.resources.app_service',
        'cloudify_azure.resources.network',
        'cloudify_azure.resources.storage'
    ],
    description='Cloudify plugin for Microsoft Azure',
    install_requires=[
        'cloudify-common==5.1.0.dev1',
        'requests==2.20.0',
        'urllib3==1.25.3',
        'pyyaml==3.12',
        'azure==4.0.0'
    ]
)
