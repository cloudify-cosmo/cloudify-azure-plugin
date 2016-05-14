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
    lifecycle.Configure
    ~~~~~~~~~~~~~~~~~~~
    Configures the Cloudify test Azure web application
'''

import os
import shutil
from cloudify import ctx
from cloudify.exceptions import HttpException

IIS_DEF_DIR = 'C:\\inetpub\\wwwroot\\'


def remove_folder_contents(folder):
    '''Removes all files and folders from a folder'''
    if not os.path.isdir(folder):
        return
    for fs_item in os.listdir(folder):
        file_path = os.path.join(folder, fs_item)
        ctx.logger.debug('Removing file/folder "{0}"'.format(file_path))
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except OSError as exc:
            ctx.logger.warn('Could not delete file / folder: {0}'
                            .format(str(exc)))


def main():
    '''Entry point'''
    ctx.logger.info('Removing default IIS web application')
    remove_folder_contents(IIS_DEF_DIR)
    ctx.logger.info('Downloading web application to {0}'.format(IIS_DEF_DIR))
    try:
        ctx.download_resource_and_render(
            'webapp/index.html',
            os.path.join(IIS_DEF_DIR, 'index.html'))
        ctx.download_resource_and_render(
            'webapp/style.css',
            os.path.join(IIS_DEF_DIR, 'style.css'))
    except HttpException as exc:
        ctx.logger.error('HttpException during web application '
                         'install. "{0}"'.format(str(exc)))


main()
