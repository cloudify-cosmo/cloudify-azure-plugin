from cloudify import ctx as _ctx
from cloudify.decorators import operation
from cloudify.exceptions import NonRecoverableError

from ..common import utils
from ..azure_sdk.resources import compute
from ..common.connection import Boto3Connection

TYPES_MATRIX = {
    'Microsoft.ContainerService/ManagedClusters': (
        compute.managed_cluster.ManagedCluster, 'aks', 'id'
    )
}


@operation
def initialize(resource_config=None, locations=None, ctx=None, **_):
    """ Initialize an cloudify.nodes.resources.AmazonWebServices node.
    This checks for resource_types in resource config and regions in regions.

    :param resource_config: A dict with key resource_types,
      a list of AWS types like AWS::EKS::CLUSTER.
    :param regions: A list of regions, like [us-east-1, us-east-2].
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
        ctx.node, regions, resource_types, ctx.logger)


@operation
def deinitialize(ctx, **_):
    """Delete the resources runtime property. """
    ctx = ctx or _ctx
    del ctx.instance.runtime_properties['resources']


def get_resources(node, locations, resource_types, logger):
    """Get a dict of resources in the following structure:

    :param node: ctx.node
    :param regions: list of Azure locations, i.e. eastus1
    :param resource_types: List of resource types, i.e. Microsoft.ContainerService/ManagedClusters.
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

    logger.info('Checking for these locations: {r}.'.format(r=locations))
    logger.info('Checking for these resource types: {t}.'.format(
        t=resource_types))
    resources = {}
    locations = locations or get_locations(node)
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
        iface = get_resource_interface(ctx, class_decl)
        # Get the resource response from the API.
        # Clean it up for context serialization.
        result = iface.list()
        # Add this stuff to the resources dict.
        for resource in result:
            resource_id = resource[resource_key]
            resource_entry = {resource_id: resource}
            location = resource['location']
            if location not in resources:
                resources[location] = {resource_type: resource_entry}
            elif resource_type not in resources[location]:
                resources[location][resource_type] = resource_entry
            else:
                resources[location][resource_type][resource_id] = resource
    return resources


def get_locations(node):
    connection = Boto3Connection(node)
    client = connection.client('ec2')
    response = client.describe_regions()
    return [r['RegionName'] for r in response['Regions']]


def get_resource_interface(ctx, class_decl):
    azure_config = utils.get_client_config(ctx.node.properties)
    api_version = ctx.node.properties.get(
        'api_version', constants.API_VER_MANAGED_CLUSTER)
    return class_decl(azure_config, ctx.logger, api_version)
