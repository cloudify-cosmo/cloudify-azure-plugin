#!/usr/bin/env python

# Built-in Imports
import tempfile
from ConfigParser import ConfigParser
import os
from os.path import join, dirname

from cloudify import ctx
# Import utilities
ctx.download_resource(
    join('components', 'utils.py'),
    join(dirname(__file__), 'utils.py'))
import utils  # NOQA


def configure_manager(manager_config_path,
                      manager_config):
    '''Sets config defaults and creates the config file'''
    _, temp_config = tempfile.mkstemp()
    config = ConfigParser()

    config.add_section('Credentials')
    config.set('Credentials', 'subscription_id',
               manager_config['subscription_id'])
    config.set('Credentials', 'tenant_id',
               manager_config['tenant_id'])
    config.set('Credentials', 'client_id',
               manager_config['client_id'])
    config.set('Credentials', 'client_secret',
               manager_config['client_secret'])

    config.add_section('Azure')
    config.set('Azure', 'location',
               manager_config['location'])

    with open(temp_config, 'w') as temp_config_file:
        config.write(temp_config_file)

    utils.mkdir(os.path.dirname(manager_config_path), use_sudo=True)
    utils.move(temp_config, manager_config_path)

    # Install prerequisites for the azure-storage Python package
    utils.yum_install('gcc', service_name='azure-storage')
    utils.yum_install('python-devel', service_name='azure-storage')
    utils.yum_install('openssl-devel', service_name='azure-storage')
    utils.yum_install('libffi-devel', service_name='azure-storage')
    utils.yum_install('python-cffi', service_name='azure-storage')


configure_manager(
    manager_config_path=os.environ.get('MGR_CONFIG_PATH'),
    manager_config={
        'subscription_id': os.environ.get('MGR_SUBSCRIPTION_ID'),
        'tenant_id': os.environ.get('MGR_TENANT_ID'),
        'client_id': os.environ.get('MGR_CLIENT_ID'),
        'client_secret': os.environ.get('MGR_CLIENT_SECRET'),
        'location': os.environ.get('MGR_LOCATION')
    }
)
