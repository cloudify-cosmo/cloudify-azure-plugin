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

import time
import random

import testtools
from cloudify.state import current_ctx
from cloudify.mocks import MockCloudifyContext

from azurecloudify.tests import test_conf
from azurecloudify import resourcegroup
import test_constants
import test_utils


TIME_DELAY = 20


class TestResourceGroup(testtools.TestCase):

    __random_id = str(random.randrange(0, 1000, 2))
    
    @classmethod
    def setUpClass(self):
        ctx = self.mock_ctx('init')
        ctx.logger.info("Testing resource_group id: {0}".format(self.__random_id))

    @classmethod
    def mock_ctx(self, test_name):
        """ Creates a mock context for the instance
            tests
        """

        test_properties = {
            test_constants.AZURE_CONFIG_KEY: {
                test_constants.SUBSCRIPTION_KEY: test_conf.SUBSCRIPTION_ID,
                test_constants.PASSWORD_KEY: test_conf.AAD_PASSWORD,
                test_constants.LOCATION_KEY: 'westus',
                test_constants.RESOURCE_GROUP_KEY: test_name + self.__random_id,
            },
            test_constants.SUBSCRIPTION_KEY: test_conf.SUBSCRIPTION_ID,
            test_constants.LOCATION_KEY: test_conf.LOCATION,
            test_constants.CLIENT_ID_KEY: test_conf.CLIENT_ID,
            test_constants.AAD_PASSWORD_KEY: test_conf.AAD_PASSWORD,
            test_constants.TENANT_ID_KEY: test_conf.TENANT_ID,
            test_constants.PATH_TO_AZURE_CONF_KEY: test_conf.PATH_TO_AZURE_CONF,
            test_constants.RESOURCE_GROUP_KEY: test_name + self.__random_id,
            test_constants.USE_EXTERNAL_RESOURCE: False
        }

        return MockCloudifyContext(node_id='test' + self.__random_id, properties=test_properties)

    def setUp(self):
        super(TestResourceGroup, self).setUp()


    def tearDown(self):
        super(TestResourceGroup, self).tearDown()
        time.sleep(TIME_DELAY)

    def ttest_create_resource_group(self):
        return
        ctx = self.mock_ctx('testcreategroup')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("BEGIN resource_group create test")

        ctx.logger.info("Creating a resource group ...")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("status_code = " + str(status_code) )
        self.assertTrue(bool((status_code == test_constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, "resource_group", test_constants.SUCCEEDED, timeout=600)

        current_ctx.set(ctx=ctx)
        ctx.logger.info("Deleting a resource group ... ")
        self.assertEqual(202, resourcegroup.delete_resource_group(ctx=ctx))
        
        try:
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, "resourcegroup", "Waiting for exception", timeout=600)
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("END resource_group create test")

    def ttest_delete_resource_group(self):
        return
        ctx = self.mock_ctx('testdeletegroup')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("BEGIN resource_group delete test")

        ctx.logger.info("create resource_group")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("status_code = " + str(status_code) )
        self.assertTrue(bool((status_code == test_constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, "resourcegroup", test_constants.SUCCEEDED, timeout=600)

        current_ctx.set(ctx=ctx)
        ctx.logger.info("delete resource_group")
        self.assertEqual(202, resourcegroup.delete_resource_group(ctx=ctx))

        try:
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, "resourcegroup", "waiting for exception", timeout=600)
        except test_utils.WindowsAzureError:
            pass


        ctx.logger.info("create resource_group with USE_EXTERNAL_RESOURCE properties set to True")
        ctx.node.properties[test_constants.USE_EXTERNAL_RESOURCE] = True
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("status_code = " + str(status_code) )
        self.assertTrue(bool((status_code == test_constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, "resourcegroup", test_constants.SUCCEEDED, timeout=600)

        ctx.logger.info("not delete resource_group")
        current_ctx.set(ctx=ctx)
        self.assertEqual(0, resourcegroup.delete_resource_group(ctx=ctx))
        
        ctx.logger.info("delete resource_group")
        ctx.logger.info("Set USE_EXTERNAL_RESOURCE properties to False")
        current_ctx.set(ctx=ctx)
        ctx.node.properties[test_constants.USE_EXTERNAL_RESOURCE] = False
        self.assertEqual(202, resourcegroup.delete_resource_group(ctx=ctx))

        try:
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, "resourcegroup", "waiting for exception", timeout=600)
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("END resource_group delete test")

    def test_conflict_resource_group(self):
        ctx = self.mock_ctx('conflictgroup')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("BEGIN resource_group conflict test")
        ctx.logger.info("create resource group")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("Status_code1 is {0}".format(str(status_code)))
        self.assertTrue(bool((status_code == test_constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, "resourcegroup", test_constants.SUCCEEDED, timeout=600)

        ctx.logger.info("Conflict create resource group")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("Status_code2 is {0}".format(str(status_code)))
        self.assertTrue(bool((status_code == test_constants.OK_STATUS_CODE) or (status_code == 201)))

        ctx.logger.info("Deleting a resource group...")
        current_ctx.set(ctx=ctx)
        expected_result = resourcegroup.delete_resource_group(ctx=ctx)
        self.assertEqual(202, expected_result)
        
        try:
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, "resourcegroup", "waiting for exception", timeout=600)
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("END resource_group conflict test")