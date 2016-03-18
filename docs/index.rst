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


External Links
==============
.. toctree::

    Cloudify 3.3.1 documentation <http://docs.getcloudify.org/3.3.1/>
    Source on GitHub <https://github.com/cloudify-cosmo/cloudify-azure-plugin/>
