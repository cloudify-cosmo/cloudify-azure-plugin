
from importlib import import_module

from ..common import AzureResource

from msrestazure.azure_exceptions import CloudError


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
                 delete_fn_name=None,
                 get_fn_name=None,
                 get_params=None):
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
        if api_version:
            self._client = self.get_client(
                self.credentials,
                self.subscription_id,
                api_version=api_version)
        else:
            self._client = self.get_client(
                self.credentials,
                self.subscription_id)
        self.custom_resource = self.get_client_attributes(
            custom_resource_object_name)
        self.create_fn_name = create_fn_name or 'create_or_update'
        self.update_fn_name = update_fn_name or 'create_or_update'
        self.delete_fn_name = delete_fn_name or 'delete'
        self.get_fn_name = get_fn_name or 'get'
        self.get_params = get_params

    def get_client(self, *args, **kwargs):
        client_obj = getattr(self.client_module, self.client_class_name)
        return client_obj(*args, **kwargs)

    def get_client_attributes(self, attribute_name, client=None):
        client = client or self.client
        attribute_names = attribute_name.split('.')
        if len(attribute_names) == 1:
            return getattr(client, attribute_name)
        return self.get_client_attributes(
            '.'.join(attribute_name[1:]), getattr(client, attribute_name[0]))

    def get(self, *args, **kwargs):
        if not args and not kwargs:
            kwargs.update(**self.get_params)
        self.logger.info(
            "Get custom resource with these parameters {0}".format(
                args, kwargs))
        call = getattr(self.custom_resource, self.get_fn_name)
        try:
            result = call(*args, **kwargs).as_dict()
        except CloudError:
            result = None
        self.logger.info(
            'Get custom resource result: {result}'.format(
                result=result))
        return result

    def _create_or_update(self, fn_name, *args, **kwargs):
        self.logger.info(
            "Create/Update custom resource with these parameters {0}".format(
                args, kwargs))
        try:
            call = getattr(self.custom_resource, fn_name)
        except AttributeError:
            self.logger.error(
                'Available attributes: {}'.format(
                    dir(self.custom_resource)))
            raise
        response = call(*args, **kwargs)
        if hasattr(response, 'wait'):
            response.wait()
            response = response.result()
        result = response.as_dict()
        self.logger.info(
            'Create/Update custom resource result: {result}'.format(
                result=result))
        return result

    def create(self, *args, **kwargs):
        return self._create_or_update(self.create_fn_name, *args, **kwargs)

    def update(self, *args, **kwargs):
        return self._create_or_update(self.update_fn_name, *args, **kwargs)

    def delete(self, *args, **kwargs):
        self.logger.info(
            "Delete custom resource with these parameters {0}".format(
                args, kwargs))
        call = getattr(self.custom_resource, self.delete_fn_name)
        response = call(*args, **kwargs)
        if hasattr(response, 'wait'):
            response.wait()
            response = response.result()
        if response:
            result = response.as_dict()
            self.logger.info(
                'Delete custom resource result: {result}'.format(
                    result=result))
            return result
