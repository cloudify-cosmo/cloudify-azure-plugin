# #######
# Copyright (c) 2016-2020 Cloudify Platform Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
    Utils
    ~~~~~
    Microsoft Azure plugin for Cloudify helper utilities
"""

from collections import Mapping

from cloudify import ctx

from cloudify_azure import constants


def dict_update(orig, updates):
    """Recursively merges two objects"""
    if updates and isinstance(updates, dict):
        for key, val in updates.items():
            if isinstance(val, Mapping):
                orig[key] = dict_update(orig.get(key, {}), val)
            else:
                orig[key] = updates[key]
    return orig


def runtime_properties_cleanup(ctx, force=False):
    # cleanup runtime properties
    if not force and ctx.instance.runtime_properties.get('async_op'):
        return
    for key in list(ctx.instance.runtime_properties.keys()):
        del ctx.instance.runtime_properties[key]


def get_resource_name(_ctx=ctx):
    """
        Finds a resource's name

    :returns: The resource's name or None
    :rtype: string
    """
    return _ctx.instance.runtime_properties.get('name') or \
        _ctx.node.properties.get('name')


def get_resource_config(_ctx=ctx, args=None):
    """
        Loads the resource config parameters and converts
        unicode key/value pairs for use with *requests*

    :returns: Resource config parameters
    :rtype: dict
    """
    return args if args else _ctx.node.properties.get('resource_config')


def get_resource_name_ref(rel, prop=None, _ctx=ctx):
    """
        Finds the resource associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Resource name
    :rtype: string
    """
    if prop:
        prop = _ctx.node.properties.get(prop)
    return prop or get_ancestor_name(_ctx.instance, rel)


def get_resource_group(_ctx=ctx):
    """
        Finds the Resource Group associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Resource Group name
    :rtype: string
    """

    return _ctx.node.properties.get('resource_group_name') or \
        _ctx.instance.runtime_properties.get('resource_group') or \
        get_ancestor_name(_ctx.instance, constants.REL_CONTAINED_IN_RG)


def get_virtual_network(_ctx=ctx):
    """
        Finds the Virtual Network associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Virtual Network name
    :rtype: string
    """
    return _ctx.node.properties.get('virtual_network_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_CONTAINED_IN_VN)


def get_route_table(_ctx=ctx):
    """
        Finds the Route Table associated with the current node. This
        method searches both by node properties (priority) or by
        node relationships

    :returns: Route Table name
    :rtype: string
    """
    return _ctx.node.properties.get('route_table_name') or \
        get_ancestor_name(
            _ctx.instance, constants.REL_CONTAINED_IN_RT)


def get_network_security_group(_ctx=ctx,
                               rel_type=constants.REL_CONTAINED_IN_NSG):
    """
        Finds the Network Security Group associated with the current node.
        This method searches both by node properties (priority) or by
        node relationships

    :returns: Network Security Group name
    :rtype: string
    """
    return _ctx.node.properties.get('network_security_group_name') or \
        get_ancestor_name(
            _ctx.instance, rel_type)


def get_retry_after(_ctx=ctx):
    """
        Returns a retry_after override

    :returns: Override for how many seconds to wait between
        each operation status check
    :rtype: integer
    """
    if not _ctx or not _ctx.node.properties:
        return None
    return _ctx.node.properties.get('retry_after')


def get_relationship_by_type(rels, rel_type):
    """
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
    """
    if not isinstance(rels, list):
        return None
    for rel in rels:
        ctx.logger.debug(
            'Attempting to find rel of type {rel_type} in {hierarchy}.'.format(
                rel_type=rel_type, hierarchy=rel.type_hierarchy))
        if isinstance(rel_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_type):
                return rel
        else:
            if rel_type in rel.type_hierarchy:
                return rel
    return None


def get_relationships_by_type(rels, rel_type):
    """
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
    """
    ret = list()
    if not isinstance(rels, list):
        return ret
    for rel in rels:
        ctx.logger.debug(
            'Attempting to find rel of type {rel_type} in {hierarchy}.'.format(
                rel_type=rel_type, hierarchy=rel.type_hierarchy))
        if isinstance(rel_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_type):
                ret.append(rel)
        else:
            if rel_type in rel.type_hierarchy:
                ret.append(rel)
    return ret


def get_parent(inst, rel_type='cloudify.relationships.contained_in'):
    """
        Gets the parent of an instance

    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string rel_type: Relationship type
    :returns: Parent context
    :rtype: :class:`cloudify.context.RelationshipSubjectContext` or None
    """
    ctx.logger.debug('Attempting to find parent for : {0}'.format(inst.id))
    for rel in inst.relationships:
        ctx.logger.debug(
            'Attempting to find rel of type {rel_type} in {hierarchy}.'.format(
                rel_type=rel_type, hierarchy=rel.type_hierarchy))
        if isinstance(rel_type, tuple):
            for i in rel_type:
                if i in rel.type_hierarchy:
                    return rel.target
        else:
            if rel_type in rel.type_hierarchy:
                return rel.target


def get_ancestor_name(inst, rel_type):
    """
        Gets the name of an ancestor (recursive search)

    :param `cloudify.context.NodeInstanceContext` inst: Cloudify instance
    :param string rel_type: Relationship type
    :returns: Ancestor resource name or None
    """

    ctx.logger.debug('Attempting to find ancestor for : {0}'.format(inst.id))
    # Find a parent of a specific type
    parent = get_parent(inst, rel_type=rel_type)
    if not parent:
        # Find a parent of any type
        parent = get_parent(inst)
        if not parent:
            return
        # Keep searching
        return get_ancestor_name(parent.instance, rel_type)
    # We found a match
    return get_resource_name(parent)


def get_rel_node_name(rel_type, _ctx=ctx):
    """
        Finds a resource by relationship type and
        returns its name

    :param string rel_type: Cloudify relationship name
    :param `cloudify.ctx` _ctx: Cloudify context
    :returns: Name of a resource
    :rtype: string or None
    """
    for rel in _ctx.instance.relationships:
        if isinstance(rel_type, tuple):
            if any(x in rel.type_hierarchy for x in rel_type):
                return get_resource_name(rel.target)
        else:
            if rel_type in rel.type_hierarchy:
                return get_resource_name(rel.target)
    return None


def secure_logging_content(content, secure_keywords=constants.SECURE_KW):
    """
    This function takes dict and check against secure_keywords
    to hide that sensitive values when logging
    """
    def _log(content, secure_keywords, log_message="", parent_hide=False):
        """
        ::param data : dict to check againt sensitive_keys
        ::param sensitive_keys : a list of keys we want to hide the values for
        ::param log_message : a string to append the message to
        ::param parent_hide : boolean flag to pass if the parent key is
                              in sensitive_keys
        """
        for key in content:
            # check if key in sensitive_keys or parent_hide
            hide = parent_hide or (key in secure_keywords)
            value = content[key]
            # handle dict value incase sensitive_keys was inside another key
            if isinstance(value, dict):
                # call _log function recusivly to handle the dict value
                log_message += "{0} : \n".format(key)
                v = _log(value, secure_keywords, "", hide)
                log_message += "  {0}".format("  ".join(v.splitlines(True)))
            else:
                # if hide true hide the value with "*"
                log_message += "{0} : {1}\n".format(key, '*'*len(value)
                                                         if hide else value)
        return log_message

    log_message = _log(content, secure_keywords)
    return log_message


def cleanup_empty_params(data):
    """
        This method will remove key with empty values, and handle renaming
        of old [REST] to [SDK] for example dnsSettings will be dns_settings
        and some more special cases can't be handled here, will be handled
        manually
    :param data: dict that holds all parameters that will be passed to sdk api
    """

    def convert_key_val(key):
        new_key = key[0].lower()
        for character in key[1:]:
            # Append an underscore if the character is uppercase.
            if character.isupper():
                new_key += '_'
            new_key += character.lower()
        return new_key

    if type(data) is dict:
        new_data = {}
        for key in data:
            if data[key]:
                val = cleanup_empty_params(data[key])
                if val:
                    new_data[convert_key_val(key)] = val
        return new_data
    elif type(data) is list:
        new_data = []
        for index in range(len(data)):
            if data[index]:
                val = cleanup_empty_params(data[index])
                if val:
                    new_data.append(val)
        return new_data
    else:
        return data


def handle_resource_config_params(data, resource_config):
    """
        This method will merge the resource_config and handle properties keys,
         that is required in [REST] but in [SDK] it's values is considered
    :param data: dict that holds all parameters that will be passed to sdk api
    :param resource_config: dict the parameters values from blueprint
    """

    def handle_properties_keys(data):
        if type(data) is dict:
            new_data = {}
            for key in data:
                if data[key]:
                    val = handle_properties_keys(data[key])
                    if val:
                        if key == 'properties':
                            new_data = dict_update(new_data, val)
                        else:
                            new_data[key] = val
            return new_data
        elif type(data) is list:
            new_data = []
            for index in range(len(data)):
                if data[index]:
                    val = handle_properties_keys(data[index])
                    if val:
                        new_data.append(val)
            return new_data
        else:
            return data
    if resource_config:
        resource_config = handle_properties_keys(resource_config)
        data = dict_update(
            data,
            resource_config
        )
    return cleanup_empty_params(data)
