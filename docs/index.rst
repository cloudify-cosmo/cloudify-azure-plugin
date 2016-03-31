.. Microsoft Azure plugin for Cloudify documentation master file, created by
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Microsoft Azure plugin for Cloudify's documentation!
========================================================

This is the documentation for the Microsoft Azure plugin for Cloudify.

Contents
========

Core
----

.. toctree::
   :maxdepth: 1
   :glob:

   cloudify_azure/*


Authentication & Authorization
------------------------------

.. toctree::
   :maxdepth: 1
   :glob:

   cloudify_azure/auth/*


Resource Interfaces
-------------------

.. toctree::
   :maxdepth: 1
   :glob:

   cloudify_azure/resources/*

Network
^^^^^^^

.. toctree::
   :maxdepth: 1
   :glob:

   cloudify_azure/resources/network/*

Storage
^^^^^^^

.. toctree::
   :maxdepth: 1
   :glob:

   cloudify_azure/resources/storage/*

Compute
^^^^^^^

.. toctree::
   :maxdepth: 1
   :glob:

   cloudify_azure/resources/compute/*


Notes
-----

Timing & The Microsoft Azure cloud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Timing is a tricky subject when dealing with the Azure cloud as
some operations can take seconds while others can take up to 20
minutes in real-world deployments.

Azure APIs make an effort to
mitigate this by responding to asynchronous operations with a
"retry after" number to indicate the number of seconds to wait
before checking the status of an operation again.  Unfortunately,
this number is more often a woeful underestimate and relying on it
will result in a high percentage of Cloudify executions leading to
failure because of too many task retries before an Azure resource
reports it's successfully created or destroyed.

For instance, creating a Resource Group is generally a synchronous
operation as it almost always reports success immediately.  But,
a Storage Account will almost never do this and will generally report
that the operation was done asynchrnously and will tell the consumer to
wait, say, 25 seconds before retrying.  By default, Cloudify limits the
number of task retries to 11 which means that the Storage Account will
need to report a successful operation with (25*11) 275 seconds (4.58 minutes).

Storage Accounts can take up to 20 minutes to report a success and the default
task retry limitations prevent this in many cases.  There are really only
two options to mitigate this issue on the Cloudify side of things.

 **#1** is to
 take the reported "retry after" value from Azure with a grain of salt and
 override it to something like 120 seconds which would give each operation a
 maximum of 1,320 seconds (22 minutes) to complete.  The downside is that
 an operation that only takes 10 seconds to complete will still wait a minimum
 of 120 seconds before continuing, possibly delaying the overall deployment
 completion time.  This is the only option that can be leveraged from using the
 plugin itself (and not modifying external elements).  The "retry after" wait time
 can be set on a per-node basis in the blueprint by setting the `retry_after` property.

 **#2** is to
 increase the maximum amount of retries to something much greater than the default.
 For instance, increasing the maximum retry count to 60 would allow operations to be
 checked using the reported "retry after" value (say, 25 seconds) but for many more
 iterations leading to a total operation timeout of (25*60) 1500 seconds (25 minutes).
 Setting this value can be done using the `--task-retries` flag in local executions or
 during Manager bootstrapping.


Linux VM public key authentication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `osProfile.linuxConfiguration.ssh.publicKeys` properties are available
when creating a new Linux VM and they specify an array of public keys that can
be placed on a Linux VM.  Using this requires the use of two subkeys named
`path` and `keyData`.  `path` is an absolute filesystem path denoting where
the public key will be placed (generally, you will want this in
/home/yourusername/.ssh/authorized_keys to enable remote SSH access).
`keyData` is a literal string containing the PKCS8-formatted public key. If
your public key current starts with something like "----- BEGIN PUBLIC KEY -----",
your key is in the SSH2 format and must be converted using the steps in the
next paragraph.  If it starts with "ssh-rsa " then it is in the PKCS8 format
and you can use it with your blueprint.  Note - when specifying your key data
in a YAML file you may wish to use double-quotes and line escapes
to preserve the key data if you want to use multiple lines (see the following
snippet).

.. code-block:: yaml

    vm_os_pubkeys:
    -   path: {concat:[ '/home/', { get_input: vm_os_username }, '/.ssh/authorized_keys' ]}
        keyData:
            "ssh-rsa AAAAB3NzaC1yc2EAAAADAAABAAABAQCUJy5McWvvqoKMkwPn+Evnvb67\
            9BGySsd0SMtuCVz8A1oG7Tke60psxWkO/DAOXn6Alm/UkoY9wqGSCJRCEvTOJvSP\
            vHNo2nTdibzNFl8NnJsHWJAbeuu5RuvMaqiIv0GUKCSAtSl/5+aFbKO0QEA74kVN\
            48PB3gXNxzL5/wkv/SZEa65lhbJHo0y/SwsazssrQ3i9p/dlwg6tZZtEFJDK9a7r\
            MYa3Xq5lbBtYeUU9MTAsX+u5HnEPFLYkzCsKC9pfv7kA+zX37wN5n0e4rAG3AaGp\
            U9yT/Oy8xKxHao82asi6NM3JIzJlwymk4Kf0F4D+A5hbpAdy9zW1YXovQppb"


If you already have a SSH2-formatted public key, you can easily convert it
to a PKCS8-formatted key for use with Azure using the following command
(on Fedora 23 - small adjustments may be needed for other systems running
different versions of OpenSSL).

.. code-block:: bash

    ssh-keygen -f /path/to/linuxvm.pub.pem -i -m PKCS8


VirtualMachineExtension Limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Microsoft has imposed an odd limitation on running multiple Virtual Machine
Extensions of the same type (CustomScriptExtension, for instance).  This
introduces an even further limitation within the scope of a Cloudify
blueprint using this plugin.  Cloudify Agents for Windows require that
WinRM be accessible on the target host and this is currently only
achievable by using a CustomScriptExtension to enable and configure
WinRM-HTTP (unencrypted, port 5985).  So, since the built in
cloudify.azure.nodes.compute.VirtualMachine node type has to use
this Virtual Machine Extension, it means that users will not be able to
specify a cloudify.azure.nodes.compute.VirtualMachineExtension in their
blueprint if it is to be of type CustomScriptExtension (since there already
is one to enable WinRM on the host).  This is not true for Linux as it relies on
SSH and SSH is enabled on Azure Linux hosts by default (no script needed).

One workaround for this, if you have a strong need to include your own scripts,
is to override this built-in script.  You can achieve this by changing the
script name and/or URI list of the node type.  This is what the type defines
by default:

.. code-block:: yaml

    interfaces:
      cloudify.interfaces.lifecycle:
        create: pkg.cloudify_azure.resources.compute.virtualmachine.create
        configure:
          implementation: pkg.cloudify_azure.resources.compute.virtualmachine.configure
          inputs:
            ps_entry:
              default: ps_enable_winrm_http.ps1
            ps_urls:
              default:
              - https://server-fqdn/ps_enable_winrm_http.ps1
        delete: pkg.cloudify_azure.resources.compute.virtualmachine.delete

The inputs ps_entry and ps_urls can be overriden if you create a new node
type.  It's recommended that, if you do this, you still reference the
default script within your override script as to still enable WinRM (unless
you intend to remove or replace this functionality).  Without the default
script functionality in place, WinRM will not be enabled properly and the
Cloudify Agent will not be able to connect to the host.


Azure Storage Services REST API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As of this writing (March 2016) the Microsoft Azure Storage Services API is an
awkward, XML-only RESTful service that behaves disimilarly to their other
Resource Manager REST APIs.  While this plugin does not support this interface,
there are some bits of information that should be shared in case future
developers or users wish to implement pieces of the API in their applications.

The API uses *Shared Key Authentication* in order to authenticate API requests.
This is, quite possibly, the least intuitive way to authenticate to a
modern API.  You can find the official Microsoft explanation here -
https://msdn.microsoft.com/en-us/library/azure/dd179428.aspx

TL;DR; When you create a Storage Account resource (using this plugin, or
otherwise), you have access to two unique Access Keys.  You can find them
in the Azure UI if you click the key icon when looking at your
Storage Account.  Generally, you want to protect these keys and not
give them out to users / applications for use.  Instead, you want to create
a *Signature String* that will accompany requests.

The link above explains how to craft a Signature String and how to make
requests using GET parameters that align with your Signature String format.
If you're working in Python, here's a small example of how to construct
a Signature String.

**Python - create the Signature String**

.. code-block:: python

    import base64
    import hmac
    import hashlib

    # Beautiful, isn't it?
    # Basically, we specify the current date, API version,
    # Storage Account name, and the operation we want to perform (list)
    # The goal of this string is to match the request GET parameters and
    # headers that this string will accompany later. If, for instance,
    # the date is not the same date we specify in a header later, this
    # operation will fail.
    sts = 'GET\n\n\n\n\n\n\n\n\n\n\n\n{0}\n{1}\n/{2}/\n{3}'.format(
        'x-ms-date:Tue, 22 Mar 2016 02:30:00 GMT',
        'x-ms-version:2015-02-21',
        'your_storage_acct',
        'comp:list')

    # Maths and stuff...
    # Decode the base64 Storage Account key, use it as our HMAC key.
    # Take the previously created String to Sign and use it as the HMAC message.
    # Perform an HMAC using SHA-256 digest and encode the result as base64.
    sss = base64.b64encode(
        hmac.new(base64.b64decode(key), sts, hashlib.sha256).digest())


**BASH - create the API request using the Signature String**

.. code-block:: bash

    curl -X GET \
    -H "x-ms-version: 2015-02-21" \
    -H "x-ms-date: Tue, 22 Mar 2016 02:30:00 GMT" \
    -H "Authorization: SharedKey your_storage_acct:ZLr5mNVKE3ToBs9HhNzwIDa79N0SLZeaVpXgE32fqGA=" \
    "https://your_storage_acct.blob.core.windows.net/?comp=list"


External Links
==============
.. toctree::

    Cloudify 3.3.1 documentation <http://docs.getcloudify.org/3.3.1/>
    Source on GitHub <https://github.com/cloudify-cosmo/cloudify-azure-plugin/>
