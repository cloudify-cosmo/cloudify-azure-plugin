# Microsoft Azure plugin for Cloudify

## Examples

### linux-nodecellar

This example blueprint shows how to deploy the classic Nodecellar application by Cloudify. This is a 2-tier application (front-end web application and a back-end database server) with support for front-end horizontal scaling. Since a Cloudify agent is required to be installed for monitoring, this blueprint requires a manager already exist in Azure and a few inputs connecting this deployment to the manager's virtual network (so they can communicate for agent installation).

```bash
# Upload the blueprint to a manager
cfy blueprints upload -p "examples/linux-nodecellar/linux-nodecellar.yaml" -b nc01
# Create a deployment (blueprint instance)
cfy deployments create -d nc01 -b nc01 -i "{path/to/inputs.yaml}"
# Execute the deployment
cfy executions start -w install -d nc01 -l
# Scale up by 2 front-end nodes
cfy executions start -w scale -p '{"delta": 2, "scalable_entity_name": "frontend"}' -d nc01 -l
```

### local-data-disks

This example blueprint demonstrates how to use the *DataDisk* and *FileShare* node types. As the name suggests, this is to be deployed using *cfy local* and there is no application or post-deployment processes that run.

```bash
# Initialize and instantiate a deployment
cfy local init --install-plugins -p "examples/local-data-disks/local-data-disks.yaml" -i "{path/to/inputs.yaml}"
# Execute the deployment
cfy local execute -w install --task-retries=30 --task-retry-interval=30  --debug
```

### windows-iis-loadbalanced

This example blueprint shows how to create a simple IIS web application running on Windows Server while utilizing the Azure Load Balancer. This blueprint also supports horizontal scaling (with appropriate load balancer hooks). A Cloudify agent is required for this blueprint so, like the *linux-nodecellar* blueprint, this will require that a manager already exists in Azure and there are a few inputs needed to connect this deployment to the existing manager's virtual network.

```bash
# Upload the blueprint to a manager
cfy blueprints upload -p "examples/windows-iis-loadbalanced/windows-iis-loadbalanced.yaml" -b iis01
# Create a deployment (blueprint instance)
cfy deployments create -d iis01 -b iis01 -i "{path/to/inputs.yaml}"
# Execute the deployment
cfy executions start -w install -d iis01 -l
# Scale up by 3 nodes
cfy executions start -w scale -p '{"delta": 3, "scalable_entity_name": "frontend"}' -d iis01 -l
```

### manager

This is the Cloudify manager bootstrap blueprint (and resources). It can be copied into the code downloaded from the [cloudify-manager-blueprints](https://github.com/cloudify-cosmo/cloudify-manager-blueprints) repository. Note - this only works for managers being bootstrapped to Red Hat-based operating systems.


## Changelog

**2016-10-10**

* Added *DataDisk* type. This update allows Data Disks to be controlled more granularly. This update also allows for Data Disks to be detatched or detached and deleted during deployment teardown. Multiple Data Disks per VM are supported.
* Added *FileShare* type. Azure does not support sharing a Data Disk between multiple VMs, but they do have a File Share storage object that allows VMs, regardless of platform, to connect to a networked shared storage.
* Improved scaling support (see the *linux-nodecellar* example blueprint).
* Updated *linux-nodecellar* and *windows-iis-loadbalanced* example blueprints.
* Added *local-data-disks* example blueprint to demonstrate using the new DataDisk and FileShare types.
