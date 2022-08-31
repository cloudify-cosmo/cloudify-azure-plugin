from cloudify import ctx as _ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError
from cloudify_common_sdk.utils import CommonSDKSecret
from cloudify_common_sdk.secure_property_management import resolve_props

from .. import utils
from .. import constants
from azure_sdk.resources.compute.managed_cluster import ManagedCluster

TYPES_MATRIX = {
    'Microsoft.ContainerService/ManagedClusters': (
        ManagedCluster, 'aks', 'id'
    )
}


@operation
def initialize(resource_config=None, locations=None, ctx=None, **_):
    """ Initialize an cloudify.azure.nodes.resources.Azure node.
    This checks for resource_types in resource config and
        locations in locations.
    :param resource_config: A dict with key resource_types,
      a list of Azure types like Microsoft.ContainerService/ManagedClusters.
    :param locations: A list of locations, like [eastus1, centralus].
    :param ctx: Cloudify CTX
    :param _:
    :return:
    """

    ctx = ctx or _ctx
    ctx.logger.info('Initializing Azure Account Info')
    ctx.logger.info('Checking for these locations: {r}.'.format(r=locations))
    resource_types = resource_config.get('resource_types', [])
    ctx.logger.info('Checking for these resource types: {t}.'.format(
        t=resource_types))

    ctx.instance.runtime_properties['resources'] = get_resources(
        ctx.node, locations, resource_types, ctx.logger, ctx.deployment.id)


@operation
def deinitialize(ctx, **_):
    """Delete the resources runtime property. """
    ctx = ctx or _ctx
    del ctx.instance.runtime_properties['resources']


def get_resources(node, locations, resource_types, logger, deployment_id=None):
    """Get a dict of resources in the following structure:

    :param node: ctx.node
    :param regions: list of Azure locations, i.e. eastus1
    :param resource_types: List of resource types,
        i.e. Microsoft.ContainerService/ManagedClusters.
    :param logger: ctx logger
    :return: a dictionary of resources in the structure:
        {
            'Microsoft.ContainerService/ManagedClusters': {
                'eastus1': {
                    'resource_id': resource
                }
            }
        }
    """

    logger.info('Checking for these resource types: {t}.'.format(
        t=resource_types))
    resources = {}
    # The structure goes resources.location.resource_type.resource, so we start
    # with location.
    # then resource type.
    for resource_type in resource_types:
        logger.info(
            'Checking for this resource type: {t}.'.format(
                t=resource_type))
        # Get the class callable, the service name, and resource_id key.
        class_decl, service_name, resource_key = TYPES_MATRIX.get(
            resource_type)
        # Note that the service_name needs to be updated in the Cloudify
        # Azure plugin resource module class for supporting new types.
        if not class_decl:
            # It means that we don't support whatever they provided.
            raise NonRecoverableError(
                'Unsupported resource type: {t}.'.format(t=resource_type))
        iface = get_resource_interface(node, class_decl, logger, deployment_id)
        # Get the resource response from the API.
        # Clean it up for context serialization.
        result = iface.list()
        # Add this stuff to the resources dict.
        for resource in result:
            resource_id = getattr(resource, resource_key)
            resource_entry = {resource_id: resource.as_dict()}
            if resource.location not in resources:
                resources[resource.location] = {resource_type: resource_entry}
            elif resource_type not in resources[resource.location]:
                resources[resource.location][resource_type] = resource_entry
            else:
                resources[resource.location][resource_type][resource_id] = \
                    resource.as_dict()
    return resources


def get_resource_interface(node, class_decl, logger, deployment_id=None):
    azure_config = resolve_props(
        utils.get_client_config(node.properties),
        deployment_id)
    for k, v in azure_config.items():
        if isinstance(v, CommonSDKSecret):
            azure_config[k] = v.secret
    api_version = node.properties.get(
        'api_version', constants.API_VER_MANAGED_CLUSTER)
    return class_decl(azure_config, logger, api_version)


def get_locations(*_, **__):
    return [
        'centralus',
        'eastasia',
        'southeastasia',
        'eastus',
        'eastus2',
        'westus',
        'westus2',
        'northcentralus',
        'southcentralus',
        'westcentralus',
        'northeurope',
        'westeurope',
        'japaneast',
        'japanwest',
        'brazilsouth',
        'australiasoutheast',
        'australiaeast',
        'westindia',
        'southindia',
        'centralindia',
        'canadacentral',
        'canadaeast',
        'uksouth',
        'ukwest',
        'koreacentral',
        'koreasouth',
        'francecentral',
        'southafricanorth',
        'uaenorth',
        'australiacentral',
        'switzerlandnorth',
        'germanywestcentral',
        'norwayeast',
        'jioindiawest',
        'westus3',
        'australiacentral2'
    ]
