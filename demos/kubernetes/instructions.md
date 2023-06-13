# Ansible Rulebook + Kubernetes

## Description

In this demo, we will configure a single-node K8s development environment,
and we will set up ansible-rulebook CLI to consume events from the
cluster using the Kubernetes event source. Upon triggering this watcher
method the ansible-rulebook CLI will run a playbook to execute any additional
action in response to this event.

## Instructions

### Installing a development environment

The method to install a small development environment is straightforward. The reasoning
for choosing K3D is based on the fact that GitHub actions support Ubuntu with Docker so
the next steps can be easily integrated into a functional end-to-end GitHub actions workflow.

```
# Installing kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
# Installing K3D
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
# Creating a cluster
k3d cluster create testcluster --api-port 6443 --servers 1 --agents 1 --port "30500-31000:30500-31000@server:0"
# Test the cluster
kubectl get nodes
```

### Rulebook return parameters

When an event is triggered and returned, there are two keys in the
result dictionary, `type`, and `resource`.

These output parameters come from the
[stream method](https://github.com/kubernetes-client/python/blob/master/kubernetes/base/watch/watch.py#L116)
in the watch class monitoring for changes in the state of the cluster.

The possible values of type are the types of event such as "ADDED", "DELETED", etc.
The resource value is a dictionary representing the watched object.

For example, a condition that can be monitored is:

```
condition: event.type == "ADDED" and event.resource.kind == 'Pod'
```

The previous condition will be met after there was `ADDED` a new object of the kind `Pod`.

For the further implementation of additional rules, the user must know the
representation of the watched object.
This logic will be handled in the rulebook rules and not in the event source plugin
enabling users to use the Python Kubernetes client without restrictions.

### Monitoring resources

For a better reference review the main list of APIs and methods that are
[supported](https://github.com/kubernetes-client/python/blob/master/kubernetes/README.md).

#### Monitoring for new ADDED Pods

1. Have ansible-rulebook CLI and its dependencies installed
2. Have ansible.eda collection installed with the Kubernetes event source
3. Start the rulebook CLI:
```
  # Go to the Kubernetes demos folder and run:
  ansible-rulebook -i inventory.yml -r rulebook_monitor_pods.yml
```
4. Once the ansible-rulebook is running, add a pod to the cluster by running:
```
kubectl apply -f k8s_deployment_no_namespace.yml
```

An event for the new Pod creation should be triggered and
the `demos/kubernetes/example_playbook.yml` playbook executed.

#### Monitoring for a new ADDED deployment

It is possible also to monitor deployments, for instance,
run the rulebook to check the status of the deployments:

```
ansible-rulebook -i inventory.yml -r rulebook_monitor_deployment.yml
```

Or by namespaces:

```
ansible-rulebook -i inventory.yml -r rulebook_monitor_deploymentns.yml
```

And then create the deployments:

```
kubectl apply -f k8s_deployment_no_namespace.yml
```

Or create a deployment in a namespace:

```
kubectl apply -f k8s_deployment_namespace.yml
kubectl apply -f k8s_deployment_with_namespace.yml

```

#### Monitoring for a new ADDED custom resource

Custom resources can be monitored also, any resource as long it has
a valid API and method to watch for changes should work without any
major change.

Let's watch for changes in the CR.

```
ansible-rulebook -i inventory.yml -r rulebook_monitor_cr.yml
```

Create a custom resource definition with its custom object:
```
kubectl apply -f k8s_crontab_crd.yml
kubectl apply -f k8s_crontab_cr.yml
```