"""kubernetes.py.

An ansible-rulebook event source plugin
that can fetch dinamically any Kubernetes resource
supported in the official Kubernetes Python client.

Arguments:
---------
    api - the API instance to be invoked
    (i.e. CoreV1Api or CustomObjectsApi)
    method - the state of the resource
    (i.e. list_pod_for_all_namespaces or list_namespaced_custom_object)
    params - the method's paramters
    (i.e. {} in the case of fetching a namespaced pods list)

Examples:
--------
    - name: Check the state of a custom resourceeee
      ansible.eda.kubernetes:
        api: CustomObjectsApi
        method: list_namespaced_custom_object
        params:
          group: metrics.k8s.io
          version: v1beta1
          namespace: default
          plural: pods

    - name: Check a Kubernetes resource content (get pods)
      ansible.eda.kubernetes:
        api: CoreV1Api
        method: list_pod_for_all_namespaces
        params: {}

"""

import asyncio
import inspect
import logging
import os
from typing import Any

from kubernetes import client, config, watch  # pylint: disable=W0406
from kubernetes.client.rest import ApiException  # pylint: disable=W0406,E0401

logger = logging.getLogger(__name__)


async def main(  # pylint: disable=R0914
    queue: asyncio.Queue,
    args: dict[str, Any],
) -> None:
    """Watch for Kubernetes events."""
    k8s_event_api = args.get("api", "")
    k8s_event_method = args.get("method", "")
    k8s_event_params = args.get("params", {})

    # We make sure we can connect to the Kubernetes cluster
    load_kubernetes_config()

    api_instance, watcher_k8s = load_kubernetes_api(k8s_event_api)

    # Each method has different parameters we will need to
    # define in the watch stream call, we make sure we get a list of
    # those method parameters, like at least the instance itself
    # (self),or i.e. the namespace
    resource_method = getattr(api_instance, k8s_event_method)
    resource_method_parameters = inspect.getfullargspec(resource_method).args
    resource_method_parameters.remove("self")
    method_params = k8s_event_params
    # We make sure the method parameters are consistent with what it wass passed
    check_method_parameters(resource_method_parameters, method_params.keys())

    last_resource_version = 0

    extra_parameters = {
        "watch": True,
        "timeout_seconds": 10,
        "resource_version": last_resource_version,
    }
    watcher_params = dict(method_params, **extra_parameters)

    try:
        while True:
            # We watch for the method passed unpacking the parameters
            for event in watcher_k8s.stream(resource_method, **watcher_params):
                logger.info("Object found :: %s", event)
                # In the case we find an object we return it
                await queue.put(
                    {
                        "type": event["type"],
                        "resource": event["raw_object"],
                    },
                )
                await asyncio.sleep(1)
                watcher_params["resource_version"] = event["raw_object"]["metadata"][
                    "resourceVersion"
                ]
    except ApiException as apierr:
        err_t = 404
        if apierr.status == err_t:
            # Unless we have objects we shouldnt be doing anything
            pass
        else:
            logging.info("Error while watching for event stream :: %s", apierr)
            raise


def load_kubernetes_api(k8s_event_api: str) -> dict:
    """Get the main client class instance with no parameters.

    All the clients have the following
    syntax i.e. client.AppsV1Api() or client.AppsV1Api
    """
    api_instance = getattr(client, k8s_event_api)()
    k8s_watcher = watch.Watch()
    return api_instance, k8s_watcher


def check_method_parameters(
    resource_method_parameters: dict,
    method_params: dict,
) -> None:
    """Check the parameters keys.

    This method makees sure the method parameters are consistent with respect the input
    """
    if set(resource_method_parameters) != set(method_params):
        logger.error("The parameters %s do not match", resource_method_parameters)
        return


def load_kubernetes_config() -> None:
    """Load the initial kubeconfig details.

    We load the config depending where we execute the events source from
    """
    try:
        if "KUBERNETES_PORT" in os.environ:
            config.load_incluster_config()
        elif "KUBECONFIG" in os.environ:
            config.load_kube_config(os.getenv("KUBECONFIG"))
        else:
            config.load_kube_config()
    except Exception:
        logging.exception(
            "---\n"
            "The Python Kubernetes client could not be configured"
            "at this time. You need a working Kubernetes environment"
            "to make this event source to work, Check the following:\n"
            "Use the env var KUBECONFIG like:\n"
            "    export KUBECONFIG=~/.kube/config\n"
            "Or run ADA from within the cluster.",
        )
        raise


if __name__ == "__main__":
    """MockQueue if running directly."""

    class MockQueue:
        """A fake queue."""

        async def put(self: str, event: str) -> str:
            """Print the event."""
            print(event)  # noqa: T201

    asyncio.run(
        main(
            MockQueue(),
            {"api": "CoreV1Api", "method": "list_pod_for_all_namespaces", "params": {}},
        ),
    )
