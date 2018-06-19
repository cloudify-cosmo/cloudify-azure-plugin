# Built-in Imports
import os

# Cloudify Imports
from ecosystem_tests import TestLocal, utils


class TestAzure(TestLocal):

    def inputs(self):
        try:
            return {
                'password': self.password,
                'location': 'westus',
                'resource_prefix': 'trammell',
                'resource_suffix': os.environ['CIRCLE_BUILD_NUM'],
                'subscription_id': os.environ['AZURE_SUB_ID'],
                'tenant_id': os.environ['AZURE_TEN_ID'],
                'client_id': os.environ['AZURE_CLI_ID'],
                'client_secret': os.environ['AZURE_CLI_SE'],
                'large_image_size': 'Standard_H8m'
            }
        except KeyError:
            raise

    def teardown_failed_resource_group(self, resource_group_name):
        utils.execute_command(
            'az resource delete --name {0}'.format(
                resource_group_name))

    def check_resources_in_deployment(self, deployment):
        for resource in \
                utils.get_deployment_resource_names(
                    deployment, 'cloudify.azure.nodes',
                    'name',
                    resource_id_key='name'):
            list_resources = \
                'az resource list --name {0}'.format(resource)
            self.assertEqual(0, utils.execute_command(list_resources))

    def setUp(self):
        sensitive_data = [
            os.environ['AZURE_CLI_SE'],
            os.environ['AZURE_CLI_ID'],
            os.environ['AZURE_TEN_ID'],
            os.environ['AZURE_SUB_ID']
        ]
        super(TestAzure, self).setUp(
            'azure.yaml', sensitive_data=sensitive_data)

        resource_group_name = \
            '{0}rg{1}'.format(
                self.inputs()['resource_prefix'],
                self.inputs()['resource_suffix'])
        self.addCleanup(
            self.teardown_failed_resource_group, resource_group_name)

        if 'ECOSYSTEM_SESSION_MANAGER_IP' not in os.environ:
            self.install_manager()
            self.manager_ip = utils.get_manager_ip(self.node_instances)
        os.environ['ECOSYSTEM_SESSION_MANAGER_IP'] = self.manager_ip

    def node_instances_after_setup(self):
        for resource in utils.get_resource_ids_by_type(
                self.node_instances,
                'cloudify.azure.nodes',
                self.cfy_local.storage.get_node):
            list_resources = 'az resource list --name {0}'.format(resource)
            self.assertEqual(0, utils.execute_command(list_resources))

    def install_network(self):
        resource_group_name = \
            'cfyresource_group{0}'.format(
                os.environ['CIRCLE_BUILD_NUM'])
        self.addCleanup(
            self.teardown_failed_resource_group,
            resource_group_name)
        network_inputs = {
            'resource_suffix': os.environ['CIRCLE_BUILD_NUM']
        }
        utils.create_deployment(
            'azure-example-network',
            inputs=network_inputs)
        utils.execute_install('azure-example-network')
        self.check_resources_in_deployment('azure-example-network')

    def install_nodecellar(self):
        nc_inputs = {
            'resource_suffix': os.environ['CIRCLE_BUILD_NUM']
        }
        if utils.install_nodecellar(
                blueprint_file_name=self.blueprint_file_name,
                inputs=nc_inputs) != 0:
            raise Exception('nodecellar install failed.')
        utils.execute_scale('nc')
        self.check_resources_in_deployment('nc')

    def install_blueprints(self):
        utils.initialize_cfy_profile(
            '{0} -u admin -p {1} -t default_tenant'.format(
                self.manager_ip, self.password))
        utils.update_plugin_yaml(os.environ['CIRCLE_SHA1'], 'pkg')
        workspace_path = os.path.join(
            os.path.abspath('workspace'),
            'build')
        utils.upload_plugin(
            utils.get_wagon_path(workspace_path))
        for plugin in self.plugins_to_upload:
            utils.upload_plugin(plugin[0], plugin[1])
        self.install_network()
        self.install_nodecellar()
        utils.execute_uninstall('nc')
        utils.execute_uninstall('azure-example-network')
        self.uninstall_manager()

    def test_run_tests(self):
        self.node_instances_after_setup()
        self.install_blueprints()
