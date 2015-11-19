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
from azurecloudify import constants
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
            constants.SUBSCRIPTION_KEY: test_conf.SUBSCRIPTION_ID,
            constants.LOCATION_KEY: test_conf.LOCATION,
            constants.CLIENT_ID_KEY: test_conf.CLIENT_ID,
            constants.AAD_PASSWORD_KEY: test_conf.AAD_PASSWORD,
            constants.TENANT_ID_KEY: test_conf.TENANT_ID,
            constants.PATH_TO_AZURE_CONF_KEY: test_conf.PATH_TO_AZURE_CONF,
            constants.EXISTING_RESOURCE_GROUP_KEY: test_name + self.__random_id,
            constants.USE_EXTERNAL_RESOURCE: False
        }

        return MockCloudifyContext(node_id='test' + self.__random_id, properties=test_properties)

    def setUp(self):
        super(TestResourceGroup, self).setUp()


    def tearDown(self):
        super(TestResourceGroup, self).tearDown()
        time.sleep(TIME_DELAY)

    def test_create_resource_group(self):
        ctx = self.mock_ctx('testcreategroup')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("==================================")
        ctx.logger.info("BEGIN resource_group create test")

        ctx.logger.info("1. Creating a resource group ...")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("status_code is {0}".format(status_code))
        self.assertIn(status_code, [constants.OK_STATUS_CODE, constants.CREATED_STATUS_CODE])
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.SUCCEEDED, timeout=600)
        ctx.logger.info("----------------------------------")

        current_ctx.set(ctx=ctx)
        ctx.logger.info("2. Deleting a resource group ... ")
        self.assertEqual(constants.ACCEPTED_STATUS_CODE, resourcegroup.delete_resource_group(ctx=ctx))
        
        try:
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.RESOURCE_NOT_FOUND, timeout=600)
            ctx.logger.info("----------------------------------")
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("END resource_group create test")

    def test_delete_resource_group(self):
        return
        ctx = self.mock_ctx('testdeletegroup')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("==================================")
        ctx.logger.info("BEGIN resource_group delete test")

        ctx.logger.info("1. Creating a resource_group")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        current_resource_group_name = ctx[constants.RESOURCE_GROUP_KEY]
        ctx.logger.debug("status_code for {0} is {1}".format(current_resource_group_name, str(status_code)))
        self.assertTrue(bool((status_code == constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.SUCCEEDED, timeout=600)
        ctx.logger.info("----------------------------------")

        current_ctx.set(ctx=ctx)
        ctx.logger.info("2. Deleting a resource_group")
        result = resourcegroup.delete_resource_group(ctx=ctx)
        self.assertIn(result, [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE])

        try:
            ctx[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.RESOURCE_NOT_FOUND, timeout=600)
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("----------------------------------")
        ctx.logger.info("3. Creating a resource_group with USE_EXTERNAL_RESOURCE property = True")
        ctx.node.properties[constants.USE_EXTERNAL_RESOURCE] = True
        ctx.node.properties[constants.EXISTING_RESOURCE_GROUP_KEY] = current_resource_group_name
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        ctx.logger.debug("status_code is {0}".format(str(status_code)))
        self.assertTrue(bool((status_code == constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.SUCCEEDED, timeout=600)

        ctx.logger.info("----------------------------------")
        ctx.logger.info("4. Do not delete the resource_group")
        current_ctx.set(ctx=ctx)
        self.assertEqual(constants.ACCEPTED_STATUS_CODE, resourcegroup.delete_resource_group(ctx=ctx))

        ctx.logger.info("Set USE_EXTERNAL_RESOURCE properties to False")
        ctx[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
        ctx.node.properties[constants.USE_EXTERNAL_RESOURCE] = False
        ctx[constants.USE_EXTERNAL_RESOURCE] = False
        current_ctx.set(ctx=ctx)
        result = resourcegroup.delete_resource_group(ctx=ctx)
        self.assertIn(result, [constants.OK_STATUS_CODE, constants.ACCEPTED_STATUS_CODE])

        try:
            ctx[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.RESOURCE_NOT_FOUND, timeout=600)
            ctx.logger.info("----------------------------------")
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("END resource_group delete test")
        ctx.logger.info("==================================")

    def test_conflict_resource_group(self):
        return
        ctx = self.mock_ctx('conflictgroup')
        current_ctx.set(ctx=ctx)
        ctx.logger.info("==================================")
        ctx.logger.info("BEGIN resource_group conflict test")
        ctx.logger.info("1. Creating a resource group ")
        status_code = resourcegroup.create_resource_group(ctx=ctx)
        current_resource_group_name = ctx[constants.RESOURCE_GROUP_KEY]
        ctx.logger.debug("create_resource_group #1 ({0}) status: {1}".format(current_resource_group_name, str(status_code)))
        self.assertTrue(bool((status_code == constants.OK_STATUS_CODE) or (status_code == 201)))
        current_ctx.set(ctx=ctx)
        test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.SUCCEEDED, timeout=600)
        ctx.logger.info("----------------------------------")

        ctx.logger.info("2. Conflict create resource group")
        status_code = resourcegroup.create_resource_group(ctx=ctx)

        ctx.logger.debug("create_resource_group #2 ({0}) status: {1}".format(current_resource_group_name, str(status_code)))
        self.assertTrue(bool((status_code == constants.OK_STATUS_CODE)))
        ctx.logger.info("----------------------------------")

        ctx.logger.info("3. Deleting a resource group {0}".format(current_resource_group_name))
        current_ctx.set(ctx=ctx)
        result = resourcegroup.delete_resource_group(ctx=ctx)
        ctx.logger.info("Delete resource group {0} status is {1}".format(current_resource_group_name,result))
        self.assertEqual(constants.ACCEPTED_STATUS_CODE, result)
        
        try:
            ctx[constants.RESOURCE_GROUP_KEY] = current_resource_group_name
            current_ctx.set(ctx=ctx)
            test_utils.wait_status(ctx, constants.RESOURCE_GROUP, constants.RESOURCE_NOT_FOUND, timeout=600)
        except test_utils.WindowsAzureError:
            pass

        ctx.logger.info("END resource_group conflict test")
        ctx.logger.info("==================================")