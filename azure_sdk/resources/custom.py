
from importlib import import_module

from ..common import AzureResource

class AzureCustomResourceError(Exception):
    pass


class CustomAzureResource(AzureResource):

    def __init__(self,
                 azure_config,
                 logger,
                 api_version,
                 custom_resource_module,
                 custom_resource_class_name,
                 custom_resource_object_name,
                 create_fn_name=None,
                 update_fn_name=None,
                 delete_fn_name=None):
        super(CustomAzureResource, self).__init__(azure_config)
        self.logger = logger
        try:
            self.client_module = import_module(custom_resource_module)
        except ModuleNotFoundError:
            raise AzureCustomResourceError(
                'Custom Azure Resource requires you to provide parameters '
                'client_module_path and client_class_name. The parameters '
                'that you provided client_module_path {client_module_path} '
                'and client_class_name {client_class_name} did not resolve.'
                'This is the equivalent of the Python code: '
                'from {client_module_path} import {client_class_name}. '
                'Check that this is the correct import path and if so raise '
                'an issue with the Cloudify team in order to look into '
                'client versions'.format(
                    client_module_path=custom_resource_class_name,
                    client_class_name=custom_resource_object_name)
            )
        self.client_class_name = custom_resource_class_name
        self._client = self.get_client(
            self.credentials,
            self.subscription_id,
            api_version=api_version)
        self.custom_resource = getattr(
            self.client, custom_resource_object_name)
        self.create_fn_name = create_fn_name or 'create_or_update'
        self.update_fn_name = update_fn_name or 'create_or_update'
        self.delete_fn_name = delete_fn_name or 'delete'

    def get_client(self, *args, **kwargs):
        client_obj = getattr(self.client_module, self.client_class_name)
        return client_obj(*args, **kwargs)

    def get(self, *args, **kwargs):
        self.logger.info(
            "Get custom resource with these parameters {0}".format(
                args, kwargs))
        result = self.custom_resource.get(*args, **kwargs).as_dict()
        self.logger.info(
            'Get custom resource result: {result}'.format(
                result=result))
        return result

    def create(self, *args, **kwargs):
        self.logger.info(
            "Create/Update custom resource with these parameters {0}".format(
                args, kwargs))
        call = getattr(self.custom_resource, self.create_fn_name)
        result = call(*args, **kwargs).as_dict()
        self.logger.info(
            'Create/Update custom resource result: {result}'.format(
                result=result))
        return result

    def update(self, *args, **kwargs):
        return self.create(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.logger.info(
            "Delete custom resource with these parameters {0}".format(
                args, kwargs))
        call = getattr(self.custom_resource, self.delete_fn_name)
        result = call(*args, **kwargs).as_dict()
        self.logger.info(
            'Delete custom resource result: {result}'.format(
                result=result))
        return result
