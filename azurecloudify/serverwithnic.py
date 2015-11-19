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

# Built-in Imports
import constants
from cloudify.exceptions import RecoverableError
import utils
import server
import nic
from cloudify import ctx
from cloudify.decorators import operation


@operation
def creation_validation(**_):
    utils.validate_node_properties(constants.VM_REQUIRED_PROPERTIES, ctx.node.properties)
    utils.validate_node_properties(constants.NIC_REQUIRED_PROPERTIES, ctx.node.properties)


@operation
def create_vm_and_nic(**_):
    if constants.NIC_CREATE_RESPONSE in ctx.instance.runtime_properties:
        create_vm()
    else:
        nic.create_a_nic()
        if constants.CREATE_RESPONSE in ctx.instance.runtime_properties:
            _set_runtime_properties()
            create_vm()
        else:
            raise RecoverableError("serverWithNic:create_vm_and_nic: NIC is not ready")


def _set_runtime_properties():
    ctx.instance.runtime_properties[constants.NIC_CREATE_RESPONSE] = True
    del ctx.instance.runtime_properties[constants.CREATE_RESPONSE]
    if constants.REQUEST_ACCEPTED in ctx.instance.runtime_properties:
        del ctx.instance.runtime_properties[constants.REQUEST_ACCEPTED]


def create_vm(**_):
    server.create_a_vm()
    if constants.CREATE_RESPONSE not in ctx.instance.runtime_properties:
        raise RecoverableError("serverWithNic:create_vm: Virtual Machine is not ready yet")


@operation
def start_vm(**_):
    server.start_a_vm()


@operation
def stop_vm(**_):
    server.stop_a_vm()


@operation
def delete_vm_and_nic(**_):
    server.delete_a_virtual_machine()
    nic.delete_a_nic()
    utils.clear_runtime_properties()




