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

import testtools
import time
from time import sleep
import test_utils
import random

from azurecloudify.tests import test_conf
from azurecloudify import resourcegroup
from azurecloudify import storageaccount
from azurecloudify import constants
from cloudify.exceptions import RecoverableError

from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext


class TestStorage(testtools.TestCase):

    __random_id = str(random.randrange(0, 1000, 2))

    @classmethod
    def setUpClass(self): 
        ctx = self.mock_ctx('init')
        ctx.logger.info("BEGIN test storage number " + self.__random_id)
        ctx.logger.info("CREATE storage_account\'s required resources")
        current_ctx.set(ctx=ctx)
        resourcegroup.create_resource_group(ctx=ctx)
        current_resource_group_name = ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY]
        ctx.logger.info("In setUpClass resource group is {0}".format(current_resource_group_name))
        current_ctx.set(ctx=ctx)


    @classmethod
    def tearDownClass(self):
        ctx = self.mock_ctx('del')
        curr_resource_group = ctx[constants.EXISTING_RESOURCE_GROUP_KEY]
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = curr_resource_group
        ctx.logger.info("Delete the resource group {0}".format(curr_resource_group))
        current_ctx.set(ctx=ctx)
        status_code = resourcegroup.delete_resource_group(ctx=ctx)
        ctx.logger.info("Deleted the resource group {0}, status code is {1}".format(curr_resource_group, status_code))


    @classmethod
    def mock_ctx(self, test_name):
        """ Creates a mock context for the instance
            tests
        """
        sa_test = "sa_test"
        test_properties = {
            constants.SUBSCRIPTION_KEY: test_conf.SUBSCRIPTION_ID,
            constants.LOCATION_KEY: test_conf.LOCATION,
            constants.CLIENT_ID_KEY: test_conf.CLIENT_ID,
            constants.AAD_PASSWORD_KEY: test_conf.AAD_PASSWORD,
            constants.TENANT_ID_KEY: test_conf.TENANT_ID,
            constants.PATH_TO_AZURE_CONF_KEY: test_conf.PATH_TO_AZURE_CONF,
            constants.EXISTING_RESOURCE_GROUP_KEY: "{0}_rg_{1}".format(sa_test, self.__random_id),
            constants.EXISTING_STORAGE_ACCOUNT_KEY: "{0}{1}".format(test_name, self.__random_id),
            constants.storage_account_type: 'Standard_LRS', #Standard_LRS|Standard_ZRS|Standard_GRS|Standard_RAGRS|Premium_LRS
            constants.USE_EXTERNAL_RESOURCE: False
        }

        return MockCloudifyContext(node_id='test', properties=test_properties)


    def setUp(self):
        super(TestStorage, self).setUp()


    def tearDown(self):
        super(TestStorage, self).tearDown()
        time.sleep(constants.WAITING_TIME)


    def test_create_storage(self):
        ctx = self.mock_ctx('testcreatestorage')
        current_resource_group_name = ctx[constants.EXISTING_RESOURCE_GROUP_KEY]
        storage_account_name = ctx[constants.EXISTING_STORAGE_ACCOUNT_KEY]
        ctx.logger.info("BEGIN test create storage {0} in resource group {1}".format(storage_account_name, current_resource_group_name, ))
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        current_ctx.set(ctx=ctx)

        status_code = test_utils.wait_4_statuses(constants.STORAGE_ACCOUNT, 'create_storage_account', ctx)
        self.assertIn(status_code, constants.valid_status_codes)
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.SUCCEEDED, timeout=600)
        ctx.logger.info("Storage Account has been created")

        ctx.logger.info("Retrieving storage account's access keys...")
        keys = storageaccount.get_storageaccount_access_keys(ctx=ctx)
        self.assertIsNotNone(keys)
        self.assertEqual(len(keys), 2)
        ctx.logger.info("KEY1 is {}".format(keys[0]))
        ctx.logger.info("KEY2 is {}".format(keys[1]))

        result = storageaccount.delete_storage_account(ctx=ctx)
        self.assertIn(result, [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE])

        ctx.logger.info("Checking if the storage account has been deleted")

        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = storage_account_name
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.RESOURCE_NOT_FOUND, timeout=600)
        ctx.logger.info("Storage account has been deleted")
        ctx.logger.info("END test create storage")


    def test_delete_storage(self):
        ctx = self.mock_ctx('testdeletestorage')
        current_resource_group_name = ctx[constants.EXISTING_RESOURCE_GROUP_KEY]
        storage_account_name = ctx[constants.EXISTING_STORAGE_ACCOUNT_KEY]
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        current_ctx.set(ctx=ctx)
        ctx.logger.info("BEGIN test delete storage {0} in resource group {1}".format(storage_account_name, current_resource_group_name))

        status_code = test_utils.wait_4_statuses(constants.STORAGE_ACCOUNT, 'create_storage_account', ctx)
        self.assertIn(status_code, constants.valid_status_codes)
        ctx.logger.info("Status_code {0}".format(str(status_code)))
        self.assertIn(status_code, [constants.OK_STATUS_CODE, constants.CREATED_STATUS_CODE, constants.ACCEPTED_STATUS_CODE])
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.SUCCEEDED, timeout=600)

        ctx.logger.info("----------------------------------")
        ctx.logger.info("Creating a storage account with USE_EXTERNAL_RESOURCE property set to True")
        ctx.node.properties[constants.USE_EXTERNAL_RESOURCE] = True
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = storage_account_name
        current_ctx.set(ctx=ctx)
        ctx.logger.info("Do not delete storage account {0}".format(storage_account_name))
        status_code = storageaccount.delete_storage_account(ctx=ctx)
        self.assertEqual(status_code, constants.ACCEPTED_STATUS_CODE)

        ctx.logger.info("Setting USE_EXTERNAL_RESOURCE property to False")
        ctx.node.properties[constants.USE_EXTERNAL_RESOURCE] = False
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = storage_account_name
        current_ctx.set(ctx=ctx)
        ctx.logger.info("Deleting storage account")
        status_code = storageaccount.delete_storage_account(ctx=ctx)
        self.assertIn(status_code, [constants.ACCEPTED_STATUS_CODE, constants.OK_STATUS_CODE])

        ctx.logger.info("Checking if storage account {0} has been deleted".format(storage_account_name))
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        ctx.instance.runtime_properties[constants.STORAGE_ACCOUNT_KEY] = storage_account_name
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.RESOURCE_NOT_FOUND, timeout=600)
        ctx.logger.info("Storage Account Deleted")

        ctx.logger.info("END test delete storage")

