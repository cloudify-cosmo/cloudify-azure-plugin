# #######
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
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
'''
    Utils
    ~~~~~
    Microsoft Azure plugin for Cloudify helper utilities
'''

# Deep Copy
from copy import deepcopy
# OS path
from os import path, environ
# Dict updating
from collections import Mapping
# Time format
from datetime import datetime
# UUID
from uuid import uuid4
# Config parser
from ConfigParser import SafeConfigParser
# Logger, default context
from logging import DEBUG
from cloudify import ctx
# Constants
from cloudify_azure import constants
# AzureCredentials namedtuple
from cloudify_azure.auth.oauth2 import AzureCredentials
from cloudify.context import RelationshipSubjectContext


def dict_update(orig, updates):
    '''Recursively merges two objects'''
    for key, val in updates.iteritems():
        if isinstance(val, Mapping):
            orig[key] = dict_update(orig.get(key, {}), val)
        else:
            orig[key] = updates[key]
    return orig


def get_resource_name(_ctx=ctx):
    '''
        Finds a resource's name

    :returns: The resource's name or None
    :rtype: string
    '''
    return _ctx.instance.runtime_properties.get('name') or \
        _ctx.node.properties.get('name')


def task_resource_create(resource, params,
                         name=None, use_external=None,
                         _ctx=ctx):
    '''
        Creates a new Microsoft Azure resource and
        polls, if necessary, until the operation
        has successfully completed

    :param `cloudify_azure.resources.base.Resource` resource:
        The resource interface object to perform resource
        operations on
    :param string name: The resource name, as identified in Azure. This
        defaults to *name* in *ctx.node.properties*
    :param dict params: Resource parameters to be passed as-is to Azure
    :raises: :exc:`cloudify.exceptions.RecoverableError`,
             :exc:`cloudify.exceptions.NonRecoverableError`,
             :exc:`requests.RequestException`
    '''
    # Get the resource name
    name = name or get_resource_name(_ctx)
    # Get use_external_resource boolean
    if use_external is None:
        use_external = _ctx.node.properties.get('use_external_resource')
    # Check for existing resources
    if use_external:
        return resource.get(name)
    # Generate a new name (if needed)
    name = generate_resource_name(resource, name=name, _ctx=_ctx)
    # Handle pending asynchrnous operations
    if _ctx.instance.runtime_properties.get('async_op'):
        return resource.operation_complete(
            _ctx.instance.runtime_properties.get('async_op'))
    # Create a new resource
    resource.create(name, params)


def generate_resource_name(resource, generator=None, name=None, _ctx=ctx):
    '''
        Generates a resource name (if needed)

    :param `cloudify_azure.resources.base.Resource` resource:
        The resource interface object to generate a name for.
    :param `function` generator: The unique string generator to use. This
        must be a function that does not take any parameters.
    :param string name: The resource name to use. If None, it will
        be generated.
    '''
    # Get the resource name
    name = name or get_resource_name(_ctx)
    # Generate a new name (if needed)
    if not name:
        for _ in xrange(0, 15):
            if generator:
                name = generator()
            else:
                name = str(uuid4())
            # Check if we have a duplicate name
            try:
                if not resource.exists(name):
                    break
            except ValueError:
                # Catch an HTTP 400 response for invalid name
                pass
    # Set the new name in the runtime properties
    _ctx.instance.runtime_properties['name'] = name
    return name


def task_resource_update(resource, params,
                         name=None,
                         force=False,
                         _ctx=ctx):
    '''
        Updates an existing Microsoft Azure resource and
        polls, if necessary, until the operation
        has successfully completed

    :param `cloudify_azure.resources.base.Resource` resource:
        The resource interface object to perform resource
        operations on
    :param string name: The resource name, as identified in Azure. This
        defaults to *name* in *ctx.node.properties*
    :param dict params: Resource parameters to update the resource with
    :raises: :exc:`cloudify.exceptions.RecoverableError`,
             :exc:`cloudify.exceptions.NonRecoverableError`,
             :exc:`requests.RequestException`
    '''
    # Get the resource name
    name = name or get_resource_name(_ctx)
    # Handle pending asynchrnous operations
    if _ctx.instance.runtime_properties.get('async_op'):
        return resource.operation_complete(
            _ctx.instance.runtime_properties.get('async_op'))
    # Update an existing resource
    resource.update(name, params, force=force)


def task_resource_delete(resource, name=None, _ctx=ctx):
    '''
        Deletes a Microsoft Azure resource and
        polls, if necessary, until the operation
        has successfully completed

    :param `cloudify_azure.resources.base.Resource` resource:
        The resource interface object to perform resource
        operations on
    :param string name: The resource name, as identified in Azure. This
        defaults to *name* in *ctx.node.properties*
    :raises: :exc:`cloudify.exceptions.RecoverableError`,
             :exc:`cloudify.exceptions.NonRecoverableError`,
             :exc:`requests.RequestException`
    '''
    # Get the resource name
    name = name or get_resource_name(_ctx)
    # Check for existing resources
    if _ctx.node.properties.get('use_external_resource'):
        return resource.get(name)
    # Handle pending asynchrnous operations
    if _ctx.instance.runtime_properties.get('async_op'):
        return resource.operation_complete(
            _ctx.instance.runtime_properties.get('async_op'))
    # Delete the resource
    resource.delete(name)


def get_resource_config(_ctx=ctx, args=None):
    '''
        Loads the resource config parameters and converts
        unicode key/value pairs for use with *requests*

    :returns: Resource config parameters
    :rtype: dict
    '''
    return args if args else _ctx.node.properties.get('resource_config')


def get_resource_name_ref(rel, prop=None, _ctx=ctx):
    '''
        Finds the resource associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Resource name
    :rtype: string
    '''
    if prop:
        prop = _ctx.node.properties.get(prop)
    return prop or get_ancestor_name(_ctx.instance, rel)


def get_resource_group(_ctx=ctx):
    '''
        Finds the Resource Group associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Resource Group name
    :rtype: string
    '''
    return _ctx.node.properties.get('resource_group_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_CONTAINED_IN_RG)


def get_storage_account(_ctx=ctx):
    '''
        Finds the Storage Account associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Storage Account name
    :rtype: string
    '''
    return _ctx.node.properties.get('storage_account_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_CONTAINED_IN_SA)


def get_virtual_network(_ctx=ctx):
    '''
        Finds the Virtual Network associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Virtual Network name
    :rtype: string
    '''
    return _ctx.node.properties.get('virtual_network_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_CONTAINED_IN_VN)


def get_subnet(_ctx=ctx):
    '''
        Finds the Subnet associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Subnet name
    :rtype: string
    '''
    return _ctx.node.properties.get('subnet_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_IPC_CONNECTED_TO_SUBNET)


def get_route_table(_ctx=ctx):
    '''
        Finds the Route Table associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Route Table name
    :rtype: string
    '''
    return _ctx.node.properties.get('route_table_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_CONTAINED_IN_RT)


def get_network_security_group(_ctx=ctx,
                               rel_type=constants.REL_CONTAINED_IN_NSG):
    '''
        Finds the Network Security Group associated with the current node.
        This method searches both by node properties (priority) or by
        node relationships

    :returns: Network Security Group name
    :rtype: string
    '''
    return _ctx.node.properties.get('network_security_group_name') or \
        get_ancestor_name(
            _ctx.instance, rel_type)


def create_child_logger(name,
                        plogger=None,
                        level=DEBUG):
    '''
        Creates a child logger and sets the log level

    .. note::

           If `plogger` is not specified, this method will default
           to using `ctx.logger` as the parent logger.

    Example::

        # Import
        from cloudify_azure import utils
        # Get a child Cloudify logger for a subroutine
        log = utils.create_child_logger('myclass.myfunc')
        # Use the logger as normal
        log.debug('Child logger!')

    :param string name: Name of the child logger
    :param `logging.Logger` plogger: Parent logger
    :param int level: Log level
    :returns: A configured child logger
    :rtype: :class:`logging.Logger`
    '''
    plogger = plogger or ctx.logger
    log = plogger.getChild(name)
    log.setLevel(level)
    return log


def get_retry_after(_ctx=ctx):
    '''
        Returns a retry_after override

    :returns: Override for how many seconds to wait between
        each operation status check
    :rtype: integer
    '''
    if not _ctx or not _ctx.node.properties:
        return None
    return _ctx.node.properties.get('retry_after')


def get_relationship_by_type(rels, rel_type):
    '''
        Finds a relationship by a relationship type

    Example::

        # Import
        from cloudify import ctx
        from cloudify_azure import utils
        # Find a specific relationship
        rel = utils.get_relationship_by_type(
            ctx.instance.relationships,
            'cloudify.azure.relationships.a_custom_relationship')

    :param list<`cloudify.context.RelationshipContext`> rels: \
        List of Cloudify instance relationships
    :param string rel_type: Relationship type
    :returns: Relationship object or None
    :rtype: :class:`cloudify.context.RelationshipContext`
    '''
    if not isinstance(rels, list):
        return None
    for rel in rels:
        if rel_type in rel.type_hierarchy:
            return rel
    return None


def get_relationships_by_type(rels, rel_type):
    '''
        Finds relationships by a relationship type

    Example::

        # Import
        from cloudify import ctx
        from cloudify_azure import utils
        # Find specific relationships
        rels = utils.get_relationships_by_type(
            ctx.instance.relationships,
            'cloudify.azure.relationships.a_custom_relationship')

    :param list<`cloudify.context.RelationshipContext`> rels: \
        List of Cloudify instance relationships
    :param string rel_type: Relationship type
    :returns: List of relationship objects
    :rtype: list of :class:`cloudify.context.RelationshipContext`
    '''
    ret = list()
    if not isinstance(rels, list):
        return ret
    for rel in rels:
        if rel_type in rel.type_hierarchy:
            ret.append(rel)
    return ret


def get_parent(inst, rel_type='cloudify.relationships.contained_in'):
    '''
        Gets the parent of an instance

    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string rel_type: Relationship type
    :returns: Parent context
    :rtype: :class:`cloudify.context.RelationshipSubjectContext` or None
    '''
    for rel in inst.relationships:
        if rel_type in rel.type_hierarchy:
            return rel.target
    return None


def get_parent_property(inst, prop,
                        rel_type='cloudify.relationships.contained_in'):
    '''
        Gets a property from an instance's parent

    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string prop: Property to search for
    :param string rel_type: Relationship type
    :returns: Parent node property or None
    '''
    parent = get_parent(inst, rel_type=rel_type)
    if parent:
        return parent.node.properties.get(prop)
    return None


def get_ancestor_property(inst, prop, rel_type):
    '''
        Gets a property from an ancestor (recursive search)

    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string prop: Property to search for
    :param string rel_type: Relationship type
    :returns: Ancestor node property or None
    '''
    # Find a parent of a specific type
    parent = get_parent(inst, rel_type=rel_type)
    if not parent:
        # Find a parent of any type
        parent = get_parent(inst)
        if not parent:
            return None
        # Keep searching
        return get_ancestor_property(parent.instance, prop, rel_type)
    # We found a match
    return parent.node.properties.get(prop)


def get_ancestor_name(inst, rel_type):
    '''
        Gets the name of an ancestor (recursive search)

    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string rel_type: Relationship type
    :returns: Ancestor resource name or None
    '''
    # Find a parent of a specific type
    parent = get_parent(inst, rel_type=rel_type)
    if not parent:
        # Find a parent of any type
        parent = get_parent(inst)
        if not parent:
            return None
        # Keep searching
        return get_ancestor_name(parent.instance, rel_type)
    # We found a match
    return get_resource_name(parent)


def get_full_id_reference(resource, api_fmt=True, _ctx=ctx):
    '''
        Creates a full, usable Azure ID reference

    :param `cloudify_azure.resources.base.Resource` resource:
        Resource class to map resources to
    :param boolean api_fmt: If True, returns the resource ID as a dict
        object with an *id* key. If False, returns just the ID string
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Azure ID of a resource
    :rtype: string or dict or None
    '''
    subscription_id = get_subscription_id(_ctx=_ctx)
    iface = resource(_ctx=_ctx)
    name = get_resource_name(_ctx)
    resid = '/subscriptions/{0}{1}/{2}'.format(
        subscription_id,
        iface.endpoint,
        name)
    if api_fmt:
        return {'id': resid}
    return resid


def get_full_resource_id(iface, name, api_fmt=True, _ctx=ctx):
    '''
        Creates a full, usable Azure ID reference

    :param `cloudify_azure.resources.base.Resource` iface:
        Existing resource instance interface
    :param boolean api_fmt: If True, returns the resource ID as a dict
        object with an *id* key. If False, returns just the ID string
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Azure ID of a resource
    :rtype: string or dict or None
    '''
    subscription_id = get_subscription_id(_ctx=_ctx)
    resid = '/subscriptions/{0}{1}/{2}'.format(
        subscription_id,
        iface.endpoint,
        name)
    if api_fmt:
        return {'id': resid}
    return resid


def get_rel_id_reference(resource, rel_type, api_fmt=True, _ctx=ctx):
    '''
        Finds a resource by relationship type and
        returns an Azure ID

    :param `cloudify_azure.resources.base.Resource` resource:
        Resource class to map resources to
    :param string rel_type: Cloudify relationship name
    :param boolean api_fmt: If True, returns the resource ID as a dict
        object with an *id* key. If False, returns just the ID string
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Azure ID of a resource
    :rtype: string or dict or None
    '''
    subscription_id = get_subscription_id()
    for rel in _ctx.instance.relationships:
        if rel_type in rel.type_hierarchy:
            iface = resource(_ctx=rel.target)
            name = get_resource_name(rel.target)
            resid = '/subscriptions/{0}{1}/{2}'.format(
                subscription_id,
                iface.endpoint,
                name)
            if api_fmt:
                return {'id': resid}
            return resid
    return None


def get_rel_node_name(rel_type, _ctx=ctx):
    '''
        Finds a resource by relationship type and
        returns its name

    :param string rel_type: Cloudify relationship name
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Name of a resource
    :rtype: string or None
    '''
    for rel in _ctx.instance.relationships:
        if rel_type in rel.type_hierarchy:
            return get_resource_name(rel.target)
    return None


def get_rel_id_references(resource, rel_type, api_fmt=True, _ctx=ctx):
    '''
        Finds resources by relationship type and
        returns Azure IDs

    :param `cloudify_azure.resources.base.Resource` resource:
        Resource class to map resources to
    :param string rel_type: Cloudify relationship name
    :param boolean api_fmt: If True, returns the resource IDs as a dict
        array with an *id* key. If False, returns just the ID strings
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Azure ID of resources
    :rtype: array
    '''
    ids = list()
    subscription_id = get_subscription_id()
    for rel in _ctx.instance.relationships:
        if rel_type in rel.type_hierarchy:
            iface = resource(_ctx=rel.target)
            name = get_resource_name(rel.target)
            resid = '/subscriptions/{0}{1}/{2}'.format(
                subscription_id,
                iface.endpoint,
                name)
            ids.append({'id': resid} if api_fmt else resid)
    return ids


def get_credentials(_ctx=ctx):
    '''
        Gets any Azure API access information from the
        current node properties or a provider context
        file created during manager bootstrapping.

    :returns: Azure credentials and access information
    :rtype: :class:`cloudify_azure.auth.oauth2.AzureCredentials`
    '''
    f_creds = dict()
    f_config_path = environ.get(constants.CONFIG_PATH_ENV_VAR_NAME,
                                constants.CONFIG_PATH)

    if path.exists(f_config_path):
        f_creds = get_credentials_from_file(f_config_path)
    n_creds = get_credentials_from_node(_ctx=_ctx)
    creds = dict_update(f_creds, n_creds)
    if 'endpoint_verify' not in creds:
        creds['endpoint_verify'] = True
    return AzureCredentials(**creds)


def get_credentials_from_file(config_path=constants.CONFIG_PATH):
    '''
        Gets Azure API access information from
        the provider context config file

    :returns: Azure credentials and access information
    :rtype: dict
    '''
    cred_keys = [
        'client_id', 'client_secret', 'subscription_id', 'tenant_id',
        'endpoint_resource', 'endpoint_verify', 'endpoints_resource_manager',
        'endpoints_active_directory'
    ]
    config = SafeConfigParser()
    config.read(config_path)
    return {k: config.get('Credentials', k) for k in cred_keys}


def get_credentials_from_node(_ctx=ctx):
    '''
        Gets any Azure API access information from the
        current node properties

    :returns: Azure credentials and access information
    :rtype: dict
    '''
    cred_keys = [
        'client_id', 'client_secret', 'subscription_id', 'tenant_id',
        'endpoint_resource', 'endpoints_resource_manager',
        'endpoints_active_directory'
    ]
    props = _ctx.node.properties.get('azure_config')
    properties = {k: props[k] for k in cred_keys if props.get(k)}
    if 'endpoint_verify' in props:
        properties['endpoint_verify'] = props['endpoint_verify']
    return properties


def get_subscription_id(_ctx=ctx):
    '''
        Gets the subscription ID from either the node or
        the provider context
    '''
    return get_credentials(_ctx=_ctx).subscription_id


def secure_logging_content(content, secure_keywords=constants.SECURE_KW):
    '''Scrubs logging calls containing potentially sensitive information'''
    def clean(clean_me, secure_keywords=secure_keywords):
        '''Srubs potentially sensitive data from a list or dict'''
        if isinstance(clean_me, list):
            for obj in clean_me:
                clean_me[clean_me.index(obj)] = clean(obj)
        elif isinstance(clean_me, dict):
            for key, value in clean_me.items():
                if isinstance(key, str) and key in secure_keywords:
                    clean_me[key] = '*'
                else:
                    clean(value)
        return clean_me

    content_copy = deepcopy(content)
    return clean(content_copy)


def get_rfc1123_date():
    '''
        Azure Storage headers use RFC 1123 for date representation.
        See https://msdn.microsoft.com/en-us/library/azure/dd135714.aspx
    '''
    return datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')


def get_cloudify_endpoint(_ctx):
    '''
        ctx.endpoint collapses the functionality for local and manager
        rest clients.

    :param _ctx: the NodeInstanceContext
    :return: endpoint object
    '''
    if hasattr(_ctx._endpoint, 'storage'):
        return _ctx._endpoint.storage
    return _ctx._endpoint


def get_relationship_subject_ctx(_ctx, rel_target):
    '''
        Get a RelationshipSubjectContext for a given Relationship Target
    :param _ctx: The NodeInstanceContext
    :param rel_target: The NodeInstanceContext
           relationship Target RelationshipContext
    :return: RelationshipSubjectContext
    '''
    target_context = {
        'node_name': rel_target.node.id,
        'node_id': rel_target.instance.id
    }
    return RelationshipSubjectContext(context=target_context,
                                      endpoint=get_cloudify_endpoint(_ctx),
                                      modifiable=False)
