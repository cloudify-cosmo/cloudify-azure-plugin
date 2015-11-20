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
        current_resource_group_name = ctx[constants.RESOURCE_GROUP_KEY]
        ctx.logger.info("In setUpClass resource group is {0}".format(current_resource_group_name))
        current_ctx.set(ctx=ctx)

    @classmethod
    def tearDownClass(self):
        ctx = self.mock_ctx('del')
        ctx.logger.info("DELETE storage_account\'s required resources")
        current_ctx.set(ctx=ctx)
        resourcegroup.delete_resource_group(ctx=ctx)

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
        time.sleep(constants.TIME_DELAY)


    def test_create_storage(self):
        ctx = self.mock_ctx('testcreatestorage')
        current_resource_group_name = ctx[constants.EXISTING_RESOURCE_GROUP_KEY]
        storage_account_name = ctx[constants.EXISTING_STORAGE_ACCOUNT_KEY]
        ctx.logger.info("BEGIN test create storage {0} in resource group {1}".format(storage_account_name, current_resource_group_name, ))
        ctx.instance.runtime_properties[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        current_ctx.set(ctx=ctx)

        status_code = -1
        valid_status_codes = [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE, constants.CREATED_STATUS_CODE]
        while status_code not in valid_status_codes:
            try:
                status_code = storageaccount.create_storage_account(ctx=ctx)
                ctx.logger.info("status_code {0} for rg:{1},sa:{2}".format(str(status_code), current_resource_group_name, storage_account_name))
                sleep(constants.TIME_DELAY)
            except RecoverableError:
                pass

        self.assertIn(status_code,valid_status_codes)
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.SUCCEEDED, timeout=600)
        ctx.logger.info("Storage Account Created")

        keys = storageaccount.get_storage_keys(ctx)
        self.assertIsNotNone(keys)
        self.assertEqual(len(keys), 2)
        ctx.logger.info("Key 1: {}, key 2: {}".format(keys[0], keys[1]))

        self.assertEqual(constants.ACCEPTED_STATUS_CODE, storageaccount.delete_storage_account(ctx=ctx))

        ctx.logger.info("Checking Storage Account deleted")
        current_ctx.set(ctx=ctx)
        self.assertRaises(test_utils.WindowsAzureError, storageaccount.get_provisioning_state, ctx=ctx)
        ctx.logger.info("Storage Account Deleted")

        ctx.logger.info("END test create storage")
 

    def test_delete_storage(self):
        return
        ctx = self.mock_ctx('testdeletestorage')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("BEGIN test delete storage")

        status_code = storageaccount.create(ctx=ctx)
        ctx.logger.info("status_code : " + str(status_code))
        self.assertTrue(bool((status_code == 200) | (status_code == 202)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.SUCCEEDED, timeout=600)

        ctx.logger.info("----------------------------------")
        ctx.logger.info("3. Creating a storage account with USE_EXTERNAL_RESOURCE property = True")
        ctx.node.properties[constants.USE_EXTERNAL_RESOURCE] = True
        
        ctx.logger.info("Do not delete storage acount")
        self.assertEqual(0, storageaccount.delete(ctx=ctx))

        ctx.logger.info("Set deletable propertie to True")
        ctx.node.properties[constants.DELETABLE_KEY] = True

        ctx.logger.info("Delete storage account")
        self.assertEqual(200, storageaccount.delete(ctx=ctx))

        ctx.logger.info("Checking Storage Account deleted")
        current_ctx.set(ctx=ctx)
        self.assertRaises(test_utils.WindowsAzureError, storageaccount.get_provisioning_state, ctx=ctx
        )
        ctx.logger.info("Storage Account Deleted")

        ctx.logger.info("END test delete storage")


    def test_conflict_storage(self):
        return
        ctx = self.mock_ctx('testconflictstorage')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("BEGIN test conflict storage")

        status_code = storageaccount.create(ctx=ctx)
        ctx.logger.info("status_code : " + str(status_code))
        self.assertTrue(bool((status_code == 200) | (status_code == 202)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.STORAGE_ACCOUNT, constants.SUCCEEDED, timeout=600)
        ctx.logger.info("Storage Account Created")

        ctx.logger.info("Conflict Creating Storage Account")
        self.assertEqual(409, storageaccount.create_storage_accounte(ctx=ctx))

        self.assertEqual(200, storageaccount.delete_storage_account(ctx=ctx))

        ctx.logger.info("Check is Storage Account is release")
        current_ctx.set(ctx=ctx)
        self.assertRaises(test_utils.WindowsAzureError,storageaccount.get_provisioning_state, ctx=ctx)
        ctx.logger.info("Storage Account Deleted")

        ctx.logger.info("END test conflict storage")