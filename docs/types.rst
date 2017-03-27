.. highlight:: yaml

.. _types:

Types
^^^^^

Node Types
==========

.. cfy:node:: cloudify.azure.nodes.ResourceGroup

This example shows adding additional parameters, and explicitly defining the azure_config::

  resourcegroup:
    type: cloudify.azure.nodes.ResourceGroup
    properties:
      name: {concat:[ { get_input: resource_prefix }, rg ] }
      location: { get_input: location }
      azure_config:
        subscription_id: { get_input: subscription_id }
        tenant_id: { get_input: tenant_id }
        client_id: { get_input: client_id }
        client_secret: { get_input: client_secret }


.. cfy:node:: cloudify.azure.nodes.storage.StorageAccount

This example shows adding additional parameters, and explicitly defining the azure_config::

  storageaccount:
    type: cloudify.azure.nodes.storage.StorageAccount
    properties:
      name: mysa01
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      resource_config:
        accountType: Standard_LRS
      azure_config: *azure_config


.. cfy:node:: cloudify.azure.nodes.network.VirtualNetwork

This example shows adding additional parameters, and explicitly defining the azure_config::

  virtual_network:
    type: cloudify.azure.nodes.network.VirtualNetwork
    properties:
      name: myvnet01
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config


.. cfy:node:: cloudify.azure.nodes.network.Subnet

This example shows adding additional parameters, and explicitly defining the azure_config::

  subnet:
    type: cloudify.azure.nodes.network.Subnet
    properties:
      name: mysubnet
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        addressPrefix: { get_input: subnet_private_cidr }


.. cfy:node:: cloudify.azure.nodes.network.NetworkSecurityGroup

This example shows adding additional parameters, and explicitly defining the azure_config::

  networksecuritygroup:
    type: cloudify.azure.nodes.network.NetworkSecurityGroup
    properties:
      name: mynsg
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        securityRules:
        - name: nsr_ssh
          properties:
            description: SSH access
            protocol: Tcp
            sourcePortRange: '*'
            destinationPortRange: 22
            sourceAddressPrefix: '*'
            destinationAddressPrefix: '*'
            priority: 100
            access: Allow
            direction: Inbound


.. cfy:node:: cloudify.azure.nodes.network.NetworkSecurityRule

This example shows adding additional parameters, and explicitly defining the azure_config::

  network_security_rule:
    type: cloudify.azure.nodes.network.NetworkSecurityRule
    properties:
      name: mocknsr
      location: eastus
      azure_config: *azure_config
      network_security_group_name: mocknsg
      resource_config:
        description: RDP access
        protocol: Tcp
        sourcePortRange: '*'
        destinationPortRange: 3389
        sourceAddressPrefix: '*'
        destinationAddressPrefix: '*'
        priority: 100
        access: Allow
        direction: Inbound


.. cfy:node:: cloudify.azure.nodes.network.RouteTable

This example shows adding additional parameters, and explicitly defining the azure_config::

  routetable:
    type: cloudify.azure.nodes.network.RouteTable
    properties:
      name: myrt
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config


.. cfy:node:: cloudify.azure.nodes.network.Route

This example shows adding additional parameters, and explicitly defining the azure_config::

  internetroute:
    type: cloudify.azure.nodes.network.Route
    properties:
      name: myir
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        addressPrefix: 0.0.0.0/0
        nextHopType: Internet


.. cfy:node:: cloudify.azure.nodes.network.IPConfiguration

This example shows adding additional parameters, and explicitly defining the azure_config::

  ubuntuipconfig:
    type: cloudify.azure.nodes.network.IPConfiguration
    properties:
      name: myuic
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        privateIPAllocationMethod: Dynamic


.. cfy:node:: cloudify.azure.nodes.network.PublicIPAddress

This example shows adding additional parameters, and explicitly defining the azure_config::

  ubuntuipconfig:
    type: cloudify.azure.nodes.network.IPConfiguration
    properties:
      name: myuic
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        privateIPAllocationMethod: Dynamic


.. cfy:node:: cloudify.azure.nodes.compute.AvailabilitySet

This example shows adding additional parameters, and explicitly defining the azure_config::

  availabilityset:
    type: cloudify.azure.nodes.compute.AvailabilitySet
    properties:
      name: myac
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config


.. cfy:node:: cloudify.azure.nodes.compute.VirtualMachine

This example shows adding additional parameters, and explicitly defining the azure_config::

  host:
    type: cloudify.azure.nodes.compute.VirtualMachine
    properties:
      name: myhost
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      os_family: { get_input: os_family_linux }
      use_public_ip: false
      resource_config:
        hardwareProfile:
          vmSize: { get_input: standard_a2_size }
        storageProfile:
          imageReference:
            publisher: { get_input: image_publisher_centos_final }
            offer: { get_input: image_offer_centos_final }
            sku: { get_input: image_sku_centos_final }
            version: { get_input: image_version_centos_final }
        osProfile:
          computerName: { get_property: [SELF, name] }
          adminUsername: { get_input: username_centos_final }
          adminPassword: { get_input: password }
          linuxConfiguration:
            ssh:
              publicKeys:
                - path: { get_input: authorized_keys_centos }
                  keyData: { get_input: keydata }
            disablePasswordAuthentication: { get_input: public_key_auth_only }


.. cfy:node:: cloudify.azure.nodes.compute.VirtualMachineExtension

This example shows adding additional parameters, and explicitly defining the azure_config::

  webserver:
    type: cloudify.azure.nodes.compute.VirtualMachineExtension
    properties:
      name: vm1_webserver
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      resource_config:
        publisher: Microsoft.Powershell
        ext_type: DSC
        typeHandlerVersion: '2.8'
        settings:
          ModulesUrl: https://www.example.com/modules.zip
          ConfigurationFunction: windows-iis-webapp.ps1\CloudifyExample
          Properties:
            MachineName: { get_property: [vm1, name] }
            WebServerPort: { get_input: webserver_port }


.. cfy:node:: cloudify.azure.nodes.network.LoadBalancer

This example shows adding additional parameters, and explicitly defining the azure_config::

  loadbalancer:
    type: cloudify.azure.nodes.network.LoadBalancer
    properties:
      name: mylb
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
    relationships:
    - type: cloudify.azure.relationships.contained_in_resource_group
      target: resourcegroup
    - type: cloudify.azure.relationships.connected_to_ip_configuration
      target: loadbalanceripcfg


.. cfy:node:: cloudify.azure.nodes.network.LoadBalancer.BackendAddressPool

This example shows adding additional parameters, and explicitly defining the azure_config::

  loadbalancerbackendpool:
    type: cloudify.azure.nodes.network.LoadBalancer.BackendAddressPool
    properties:
      name: mylb
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
    relationships:
      - type: cloudify.azure.relationships.contained_in_load_balancer
        target: loadbalancer


.. cfy:node:: cloudify.azure.nodes.network.LoadBalancer.Probe

This example shows adding additional parameters, and explicitly defining the azure_config::

  loadbalancerprobe:
    type: cloudify.azure.nodes.network.LoadBalancer.Probe
    properties:
      name: lbprobe
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        protocol: Http
        port: { get_input: webserver_port }
        requestPath: index.html
    relationships:
    - type: cloudify.azure.relationships.contained_in_load_balancer
      target: loadbalancer
    - type: cloudify.relationships.depends_on
      target: loadbalancerbackendpool


.. cfy:node:: cloudify.azure.nodes.network.LoadBalancer.IncomingNATRule


.. cfy:node:: cloudify.azure.nodes.network.LoadBalancer.Rule

This example shows adding additional parameters, and explicitly defining the azure_config::

  loadbalancerrule:
    type: cloudify.azure.nodes.network.LoadBalancer.Rule
    properties:
      name: mylbrule
      location: { get_input: location }
      retry_after: { get_input: retry_after }
      azure_config: *azure_config
      resource_config:
        protocol: Tcp
        backendPort: { get_input: webserver_port }
        frontendPort: { get_input: loadbalancer_port }
    relationships:
    - type: cloudify.azure.relationships.contained_in_load_balancer
      target: loadbalancer
    - type: cloudify.azure.relationships.connected_to_ip_configuration
      target: loadbalanceripcfg
    - type: cloudify.azure.relationships.connected_to_lb_be_pool
      target: loadbalancerbackendpool
    - type: cloudify.azure.relationships.connected_to_lb_probe
      target: loadbalancerprobe


.. cfy:node:: cloudify.azure.nodes.storage.DataDisk
.. cfy:node:: cloudify.azure.nodes.storage.FileShare
.. cfy:node:: cloudify.azure.nodes.network.NetworkInterfaceCard


Node Types Common Behaviour
===========================

Common Properties
-----------------

All cloud resource nodes have common properties:

  * ``name``
  * ``location``
  * ``tags``
  * ``retry_after`` Because Azure's API is asynchronous, this value indicates the interval between retries.

Every time you manage a resource with Cloudify,
we create one or more clients with Azure API.
You specify the configuration for these clients using the ``azure_config`` property.
It should be a dictionary,
with the following values::

  subscription_id:
  tenant_id:
  client_id:
  client_secret:

See :cfy:datatype:``cloudify.datatypes.azure.Config``

Using Existing Resources
------------------------

It is possible to use existing resources on Azure -
whether these have been created by a different Cloudify deployment or not via Cloudify at all.

All Cloudify Azure types have a property named ``use_external_resource``,
whose default value is ``false``.
When set to ``true``,
the plugin will apply different semantics for each of the operations executed on the relevant node's instances:

If ``use_external_resource`` is set to true in the blueprint,
the ``name`` must be that resource's name in Azure.

This behavior is common to all resource types:

* ``create`` If ``use_external_resource`` is true,
  the plugin will check if the resource is available in your account.
* ``delete`` If ``use_external_resource`` is true,
  the plugin will check if the resource is available in your account.


Data Types
==========

.. cfy:datatype:: cloudify.datatypes.azure.Config
.. cfy:datatype:: cloudify.datatypes.azure.network.VirtualNetworkConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.NetworkSecurityGroupConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.NetworkSecurityRuleConfig
.. cfy:datatype:: cloudify.datatypes.azure.storage.FileShareConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.IPConfigurationConfig
.. cfy:datatype:: cloudify.datatypes.azure.compute.AvailabilitySetConfig
.. cfy:datatype:: cloudify.datatypes.azure.storage.StorageAccountConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.LoadBalancerRuleConfig
.. cfy:datatype:: cloudify.datatypes.azure.compute.VirtualMachineConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.LoadBalancerConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.RouteConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.LoadBalancerProbeConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.RouteTableConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.SubnetConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.PublicIPAddressConfig
.. cfy:datatype:: cloudify.datatypes.azure.storage.DataDiskConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.LoadBalancerIncomingNATRuleConfig
.. cfy:datatype:: cloudify.datatypes.azure.network.NetworkInterfaceCardConfig


Relationships
=============

.. cfy:rel:: cloudify.azure.relationships.contained_in_resource_group

    Sets a dependency between the resource and the resource group that contains it.


.. cfy:rel:: cloudify.azure.relationships.contained_in_virtual_network

    Sets a dependency between the resource and the virtual network that contains it.


.. cfy:rel:: cloudify.azure.relationships.contained_in_network_security_group

    Sets a dependency between the resource and the network security group that contains it.


.. cfy:rel:: cloudify.azure.relationships.contained_in_route_table

    Sets a dependency between the resource and the route table that contains it.


.. cfy:rel:: cloudify.azure.relationships.contained_in_load_balancer

    Sets a dependency between the resource and the load balancer.


.. cfy:rel:: cloudify.azure.relationships.network_security_group_attached_to_subnet

    Attaches a network security group to a subnet.


.. cfy:rel:: cloudify.azure.relationships.route_table_attached_to_subnet

    Attaches a network route table to a subnet.


.. cfy:rel:: cloudify.azure.relationships.nic_connected_to_network_security_group

    Attaches a NIC to a network security group.


.. cfy:rel:: cloudify.azure.relationships.ip_configuration_connected_to_subnet

    Sets a dependency between an IP configuration and a subnet.


.. cfy:rel:: cloudify.azure.relationships.ip_configuration_connected_to_public_ip

    Sets a dependency between an IP configuration and a public IP.


.. cfy:rel:: cloudify.azure.relationships.connected_to_storage_account

    Sets a dependency between the resource and a storage account.


.. cfy:rel:: cloudify.azure.relationships.connected_to_availability_set

    Sets a dependency between the resource and an availability set.


.. cfy:rel:: cloudify.azure.relationships.connected_to_ip_configuration

    Sets a dependency between the resource and an IP configuration.


.. cfy:rel:: cloudify.azure.relationships.connected_to_nic

    Sets a dependency between the resource and a NIC.


.. cfy:rel:: cloudify.azure.relationships.connected_to_lb_be_pool

    Sets a dependency between the resource and a LB pool.


.. cfy:rel:: cloudify.azure.relationships.connected_to_lb_probe

    Sets a dependency between the resource and a LB probe.


.. cfy:rel:: cloudify.azure.relationships.vmx_contained_in_vm

    Sets a dependency between a VM extension and a VM.


.. cfy:rel:: cloudify.azure.relationships.nic_connected_to_lb_be_pool

    Sets a dependency between a NIC and a LB pool.


.. cfy:rel:: cloudify.azure.relationships.vm_connected_to_datadisk
.. cfy:rel:: cloudify.azure.relationships.connected_to_data_disk
.. cfy:rel:: cloudify.azure.relationships.nic_connected_to_ip_configuration
.. cfy:rel:: cloudify.azure.relationships.lb_connected_to_ip_configuration
.. cfy:rel:: cloudify.azure.relationships.contained_in_storage_account
