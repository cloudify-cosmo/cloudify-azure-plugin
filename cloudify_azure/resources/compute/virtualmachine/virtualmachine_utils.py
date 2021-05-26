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

import json
from cloudify import ctx


def check_if_configuration_changed(ctx, update_payload, current_vm):
    for prop in ['location', 'tags', 'plan', 'availability_set',
                 'eviction_policy', 'billing_profile', 'priority',
                 'hardware_profile']:
        update_property_value = update_payload.get(prop)
        current_vm_property_value = current_vm.get(prop)
        if update_property_value and ordered(
                update_property_value) != ordered(current_vm_property_value):
            ctx.logger.info("{prop} changed.".format(prop=prop))
            ctx.logger.info("update payload: {content}.".format(
                content=update_property_value))
            ctx.logger.info("current configuration: {content}.".format(
                content=current_vm_property_value))
            return True

    for prop in ['os_profile', 'storage_profile', 'network_profile']:
        if prop == 'network_profile':
            update_property_value = update_payload.get(prop).as_dict()
        else:
            update_property_value = update_payload.get(prop, {})

        current_vm_property_value = current_vm.get(prop, {})
        if diff_dictionaries(update_property_value, current_vm_property_value):
            ctx.logger.info("{prop} changed.".format(prop=prop))
            ctx.logger.info("update payload: {content}.".format(
                content=update_property_value))
            ctx.logger.info("current configuration: {content}.".format(
                content=current_vm_property_value))
            return True

    # if update_payload.get('tags') and ordered(update_payload.get('tags',
    # {})) != ordered(current_vm.get('tags', {})):
    #     ctx.logger.info("Tags changed.")
    #     return True
    # if update_payload.get('plan') and ordered(update_payload.get('plan',
    # {})) != ordered(current_vm.get('plan', {})):
    #     ctx.logger.info("Plan changed.")
    #     return True
    # if update_payload.get('availability_set') and  ordered(
    # update_payload.get('availability_set', {})) != ordered(current_vm.get(
    # 'availability_set', {})):
    #     ctx.logger.info("availability_set changed.")
    #     return True
    # # spot configuration
    # if update_payload.get('eviction_policy') and update_payload.get(
    # 'eviction_policy') != current_vm.get('eviction_policy'):
    #     ctx.logger.info("eviction_policy changed.")
    #     return True
    # if update_payload.get('billing_profile') and ordered(
    # update_payload.get('billing_profile')) != ordered(current_vm.get(
    # 'billing_profile')):
    #     ctx.logger.info("billing_profile changed.")
    #     return True
    # if update_payload.get('priority') and update_payload.get('priority')
    # != current_vm.get('priority'):
    #     ctx.logger.info("priority changed.")
    #     return True
    #
    # if update_payload.get('hardware_profile') and ordered(
    # update_payload.get('hardware_profile')) != ordered(current_vm.get(
    # 'hardware_profile')):
    #     ctx.logger.info("hardware_profile changed.")
    #     return True

    # if diff_dictionaries(update_payload.get('os_profile',{}),
    # current_vm.get('os_profile',{})):
    #     ctx.logger.info("os_profile changed.")
    #     return True
    #
    # if diff_dictionaries(update_payload.get('storage_profile',{}),
    # current_vm.get('storage_profile',{})):
    #     ctx.logger.info("storage_profile changed.")
    #     return True

    # update_network_profile = update_payload.get('network_profile').as_dict()
    # if diff_dictionaries(update_network_profile,
    #                      current_vm.get('network_profile', {})):
    #     ctx.logger.info("network_profile changed.")
    #     return True

    return False


def diff_dictionaries(update_dict, current_conf_dict):
    """
    Returns True if update_dict has changes in a key that doesn't appear in
    current_conf_dict.
    """
    for key in update_dict:
        if isinstance(update_dict.get(key), dict):
            res = diff_dictionaries(update_dict.get(key), current_conf_dict.get(key,{}))
            if res:
                return True
        elif ordered(update_dict.get(key)) != ordered(
                current_conf_dict.get(key)):
            ctx.logger.info('changes found in diff dict: key={}\n'.format(key))
            ctx.logger.info('update_dict: {}'.format(ordered(update_dict.get(key))))
            ctx.logger.info(
                'current_conf_dict: {}'.format(ordered(
                current_conf_dict.get(key))))
            return True


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    if isinstance(obj, str):
        return obj.lower()
    if isinstance(obj, (int, float)):
        return str(obj)
    else:
        return obj
