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
from setuptools import find_packages


setup(
    name='cloudify-azure-plugin',
    version='3.0.3',
    license='LICENSE',
    packages=find_packages(exclude=['tests*']),
    description='Cloudify plugin for Microsoft Azure',
    install_requires=[
        'cloudify-common>=4.5',
        'requests==2.20.0',
        'urllib3==1.25.3',
        'pyyaml==3.12',
        # stating from azure v5.0.0 we need to add azure modules like this
        'azure-mgmt-web==0.46.0',
        'azure-mgmt-compute==12.0.0',
        'azure-mgmt-containerservice==9.0.1',
        'azure-mgmt-network==10.1.0',
        'azure-mgmt-storage==9.0.0',
        'azure-storage-common==2.1.0',
        'azure-mgmt-resource==9.0.0',
        'azure-common==1.1.25',
        'msrestazure==0.6.3'

    ]
)
