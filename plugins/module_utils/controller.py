# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

"""Controller for managing Event-Driven Ansible resources.

This module provides the Controller class for managing resources
on the EDA controller via API, including create, update, delete,
and other operations on resources.
"""

from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type


import json
from typing import Any, List, NoReturn, Optional

from ansible.module_utils.basic import AnsibleModule

from .client import Client, Response
from .errors import EDAError


class Controller:
    """Controller for managing Event-Driven Ansible resources.

    Provides high-level methods for working with resources
    on the EDA controller, including CRUD operations and special actions
    like copying and restarting activations.
    """

    #: Mapping of endpoints to identity fields for special resource types
    IDENTITY_FIELDS = {"users": "username"}

    #: Marker for encrypted values in API responses
    ENCRYPTED_STRING = "$encrypted$"

    def __init__(self, client: Client, module: AnsibleModule) -> None:
        """Initialize the controller.

        :param client: HTTP client for making API requests
        :param module: Ansible module instance for accessing parameters and results
        """
        self.client = client
        self.module = module
        self.result = {"changed": False}

        if "update_secrets" in self.module.params:
            self.update_secrets = self.module.params.pop("update_secrets")
        else:
            self.update_secrets = True

    @staticmethod
    def get_name_field_from_endpoint(endpoint: str) -> str:
        """Get the identity field name for an endpoint.

        Returns the name of the field used to identify a resource
        (usually 'name', but may be different for some resources).

        :param endpoint: API endpoint of the resource
        :returns: Identity field name ('name' or type-specific)
        """
        return Controller.IDENTITY_FIELDS.get(endpoint, "name")

    def get_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        """Execute a GET request to the endpoint.

        :param endpoint: API endpoint for the request
        :param kwargs: Additional parameters for the request
        :returns: Response object from the API
        """
        return self.client.get(endpoint, **kwargs)

    def post_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        """Execute a POST request to the endpoint.

        Respects check mode - if enabled, returns a mock successful response
        without making the actual request.

        :param endpoint: API endpoint for the request
        :param kwargs: Additional parameters for the request (usually data)
        :returns: Response object from the API or mock response in check mode
        """
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return Response(status=200, data=json.dumps(self.result))

        return self.client.post(endpoint, **kwargs)

    def patch_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        """Execute a PATCH request to the endpoint.

        Respects check mode - if enabled, returns a mock successful response
        without making the actual request.

        :param endpoint: API endpoint for the request
        :param kwargs: Additional parameters for the request (usually data and id)
        :returns: Response object from the API or mock response in check mode
        """
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return Response(status=200, data=json.dumps(self.result))

        return self.client.patch(endpoint, **kwargs)

    def delete_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        """Execute a DELETE request to the endpoint.

        Respects check mode - if enabled, returns a mock successful response
        without making the actual request.

        :param endpoint: API endpoint for the request
        :param kwargs: Additional parameters for the request (usually id)
        :returns: Response object from the API or mock response in check mode
        """
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return Response(status=200, data=json.dumps(self.result))

        return self.client.delete(endpoint, **kwargs)

    def get_item_name(self, item: Any) -> Any:
        """Get the name of an item from its data.

        Extracts the value of the item's identity field (usually 'name',
        but may be another field, e.g., 'username' for users).

        :param item: Item data from the API
        :returns: Value of the item's identity field
        """
        if item:
            if "name" in item:
                return item["name"]

            for field_name in Controller.IDENTITY_FIELDS.values():
                if field_name in item:
                    return item[field_name]

        if item:
            msg = f"Cannot determine identity field for {item.get('type', 'unknown')} object."
            raise EDAError(msg)
        msg = "Cant determine identity field for Undefined object."
        raise EDAError(msg)

    def fail_wanted_one(self, response: list[Any]) -> NoReturn:
        """Raise an error when multiple results are received instead of one.

        :param response: List of received items
        """
        sample = response.copy()
        sample = sample[:2] + ["...more results snipped..."]
        msg = f"Request returned {len(response)} items, expected 1. See: {sample}"
        raise EDAError(msg)

    def get_exactly_one(
        self, endpoint: str, name: Optional[str], **kwargs: Any
    ) -> dict[str, Any]:
        """Get exactly one item by name.

        Searches for an item and verifies that exactly one result is found.
        If 0 items are found, returns an empty dictionary.
        If more than one is found - raises an error.

        :param endpoint: API endpoint for the search
        :param name: Name of the item to search for
        :param kwargs: Additional parameters for the search
        :returns: Data of the found item or empty dictionary
        """
        result = self.get_one_or_many(endpoint, name=name, **kwargs)
        matches = []
        name_field = self.get_name_field_from_endpoint(endpoint)

        for asset in result:
            if str(asset[name_field]) == name:
                matches.append(asset)

        if len(matches) == 0:
            return {}

        if len(matches) == 1:
            return matches[0]

        self.fail_wanted_one(result)

    def resolve_name_to_id(
        self, endpoint: str, name: str, **kwargs: Any
    ) -> Optional[int]:
        """Convert a resource name to its ID.

        Finds a resource by name and returns its ID.

        :param endpoint: API endpoint for the search
        :param name: Resource name
        :param kwargs: Additional parameters for the search
        :returns: ID of the found resource or None if not found
        """
        result = self.get_exactly_one(endpoint, name, **kwargs)
        if result:
            if isinstance(result["id"], int):
                return result["id"]
            raise EDAError(
                f"The endpoint did not provide an id as integer: {result['id']}"
            )
        return None

    def get_one_or_many(
        self,
        endpoint: str,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[dict[str, Any]]:
        """Get one or more items from an endpoint.

        Executes a GET request to the endpoint and returns a list of found items.
        Can filter by name if specified.

        :param endpoint: API endpoint for the request
        :param name: Name to filter results by (optional)
        :param kwargs: Additional parameters for the request
        :returns: List of found items
        """
        new_kwargs = kwargs.copy()

        if name:
            name_field = self.get_name_field_from_endpoint(endpoint)
            new_data = kwargs.get("data", {}).copy()
            new_data[name_field] = name
            new_kwargs["data"] = new_data

        response = self.get_endpoint(endpoint, **new_kwargs)

        if response.status != 200:
            fail_msg = f"Got a {response.status} when trying to get from {endpoint}"

            if "detail" in response.json:
                fail_msg += f",detail: {response.json['detail']}"
            raise EDAError(fail_msg)

        if "count" not in response.json or "results" not in response.json:
            raise EDAError("The endpoint did not provide count, results")

        if response.json["count"] == 0:
            return []

        # type safeguard
        results = response.json["results"]
        if not isinstance(results, list):
            raise EDAError("The endpoint did not provide a list of dictionaries")
        for result in results:
            if not isinstance(result, dict):
                raise EDAError("The endpoint did not provide a list of dictionaries")
        return results

    def create_if_needed(
        self,
        new_item: dict[str, Any],
        endpoint: str,
        item_type: str = "unknown",
    ) -> dict[str, bool]:
        """Create a new item if necessary.

        Executes a POST request to create a new resource.
        Used when it's known that the item does not exist.

        :param new_item: Data for the new item
        :param endpoint: API endpoint for creation
        :param item_type: Item type for error messages
        :returns: Dictionary with 'changed' and 'id' keys
        """
        response = None
        if not endpoint:
            msg = f"Unable to create new {item_type}, missing endpoint"
            raise EDAError(msg)

        if self.module.check_mode:
            return {"changed": True}

        # We don't have an existing_item, we can try to create it
        # We will pull the item_name out from the new_item, if it exists
        item_name = self.get_item_name(new_item)
        response = self.post_endpoint(endpoint, **{"data": new_item})
        if response.status in [200, 201]:
            self.result["id"] = response.json["id"]
            self.result["changed"] = True
            return self.result
        if response.json and "__all__" in response.json:
            msg = f"Unable to create {item_type} {item_name}: {response.json['__all__'][0]}"
            raise EDAError(msg)
        if response.json:
            msg = f"Unable to create {item_type} {item_name}: {response.json}"
            raise EDAError(msg)
        msg = f"Unable to create {item_type} {item_name}: {response.status}"
        raise EDAError(msg)

    def create(
        self, new_item: dict[str, Any], endpoint: str, item_type: str = "unknown"
    ) -> dict[str, bool]:
        """Unconditionally execute a create (POST) operation and return the result.

        Creates a new resource without preliminary existence checks.

        :param new_item: Data for the new item
        :param endpoint: API endpoint for creation
        :param item_type: Item type for error messages
        :returns: Dictionary with 'changed' key
        """

        response = self.post_endpoint(endpoint, data=new_item)

        if response.status in [201, 202]:
            self.result["changed"] = True
            return self.result

        error_msg = f"Unable to create {item_type} {new_item}: {response.status} {response.data}"
        if response.json:
            error_msg = f"Unable to create {item_type} {new_item}: {response.json}"

        raise EDAError(error_msg)

    def _encrypted_changed_warning(
        self, field: str, old: dict[str, Any], warning: bool = False
    ) -> None:
        """Issue a warning about an encrypted field.

        Shows a warning when a field contains encrypted data
        and changes may be detected inaccurately.

        :param field: Name of the field with encrypted data
        :param old: Old item data
        :param warning: Whether to show the warning
        """
        if not warning:
            return
        self.module.warn(
            f"The field {field} of {old.get('type', 'unknown')} {old.get('id', 'unknown')} "
            "has encrypted data and may inaccurately report task is changed."
        )

    @staticmethod
    def has_encrypted_values(obj: Any) -> bool:
        """Check for encrypted values in an object.

        Recursively checks whether the object (dict, list, or value)
        contains the $encrypted$ marker anywhere in the data structure.

        :param obj: Object to check (dict, list, or scalar value)
        :returns: True if encrypted values are found
        """
        if isinstance(obj, dict):
            for val in obj.values():
                if Controller.has_encrypted_values(val):
                    return True
        elif isinstance(obj, list):
            for val in obj:
                if Controller.has_encrypted_values(val):
                    return True
        elif obj == Controller.ENCRYPTED_STRING:
            return True
        return False

    @staticmethod
    def fields_could_be_same(old_field: Any, new_field: Any) -> bool:
        """Check if fields could be the same.

        Compares two fields, treating $encrypted$ as a wildcard.
        Returns False if values are definitely different.
        Returns True if values are the same or could be the same
        depending on unknown encrypted values.

        :param old_field: Old field value
        :param new_field: New field value
        :returns: True if fields are the same or could be the same
        """
        if isinstance(old_field, dict) and isinstance(new_field, dict):
            if set(old_field.keys()) != set(new_field.keys()):
                return False
            for key in new_field.keys():
                if not Controller.fields_could_be_same(old_field[key], new_field[key]):
                    return False
            return True  # all sub-fields are either equal or could be equal
        if old_field == Controller.ENCRYPTED_STRING:
            return True

        return bool(new_field == old_field)

    def objects_could_be_different(
        self,
        old: dict[str, Any],
        new: dict[str, Any],
        field_set: Optional[set[str]] = None,
        warning: bool = False,
    ) -> bool:
        """Check if objects could be different.

        Compares two objects, considering encrypted fields and the
        update_secrets setting. Returns True if objects differ or could differ.

        :param old: Old object data
        :param new: New object data
        :param field_set: Set of fields to compare (if None, all fields from new)
        :param warning: Whether to show warnings about encrypted fields
        :returns: True if objects differ or could differ
        """
        if field_set is None:
            field_set = set(fd for fd in new.keys())
        for field in field_set:
            new_field = new.get(field, None)
            old_field = old.get(field, None)

            if old_field != new_field:
                if self.update_secrets or (
                    not self.fields_could_be_same(old_field, new_field)
                ):
                    return True  # Something doesn't match, or something
                    # might not match
            elif self.has_encrypted_values(new_field):
                if self.update_secrets or (
                    not self.fields_could_be_same(old_field, new_field)
                ):
                    # case of 'field not in new' - user password write-only
                    # field that API will not display
                    self._encrypted_changed_warning(field, old, warning=warning)
                    return True
        return False

    def update_if_needed(
        self,
        existing_item: dict[str, Any],
        new_item: dict[str, Any],
        endpoint: str,
        item_type: str,
    ) -> dict[str, bool]:
        """Update an item if necessary.

        Compares the existing item with new data and executes
        a PATCH request if differences are found.

        :param existing_item: Existing item data from the API
        :param new_item: New data for the update
        :param endpoint: API endpoint for the update
        :param item_type: Item type for error messages
        :returns: Dictionary with 'changed' and 'id' keys
        """
        response = None
        if not existing_item:
            raise RuntimeError(
                "update_if_needed called incorrectly without existing_item"
            )

        # If we have an item, we can see if it needs an update
        try:
            if item_type == "user":
                item_name = existing_item["username"]
            else:
                item_name = existing_item["name"]
            item_id = existing_item["id"]
        except KeyError as e:
            msg = f"Unable to process update, missing data {e}"
            raise EDAError(msg) from e

        # Check to see if anything within the item requires to be updated
        needs_patch = self.objects_could_be_different(existing_item, new_item)

        # If we decided the item needs to be updated, update it
        self.result["id"] = item_id
        if needs_patch:
            if self.module.check_mode:
                return {"changed": True}

            response = self.patch_endpoint(
                endpoint, **{"data": new_item, "id": self.result["id"]}
            )
            if response.status == 200:
                # compare apples-to-apples, old API data to new API data
                # but do so considering the fields given in parameters
                self.result["changed"] |= self.objects_could_be_different(
                    existing_item,
                    response.json,
                    field_set=set(new_item.keys()),
                    warning=True,
                )
                return self.result
            if response.json and "__all__" in response.json:
                raise EDAError(response.json["__all__"])
            msg = f"Unable to update {item_type} {item_name}"
            raise EDAError(msg)

        return self.result

    def create_or_update_if_needed(
        self,
        existing_item: dict[str, Any],
        new_item: dict[str, Any],
        endpoint: str,
        item_type: str = "unknown",
    ) -> dict[str, bool]:
        """Create or update an item as needed.

        Creates if the item doesn't exist, or updates
        if the item exists and there are differences.

        :param existing_item: Existing item data or empty dictionary
        :param new_item: New item data
        :param endpoint: API endpoint for the operation
        :param item_type: Item type for error messages
        :returns: Dictionary with 'changed' and 'id' keys
        """
        if existing_item:
            return self.update_if_needed(
                existing_item,
                new_item,
                endpoint,
                item_type=item_type,
            )
        return self.create_if_needed(
            new_item,
            endpoint,
            item_type=item_type,
        )

    def delete_if_needed(
        self, existing_item: dict[str, Any], endpoint: str
    ) -> dict[str, Any]:
        """Delete an item if it exists.

        Executes a DELETE request to remove the resource if it exists.
        If the item doesn't exist, returns result unchanged.

        :param existing_item: Existing item data or empty dictionary
        :param endpoint: API endpoint for deletion
        :returns: Dictionary with 'changed' and 'id' keys
        """
        if not existing_item:
            return self.result

        # If we have an item, we can try to delete it
        try:
            item_id = existing_item["id"]
            item_name = self.get_item_name(existing_item)
        except KeyError as e:
            msg = f"Unable to process delete, missing data {e}"
            raise EDAError(msg) from e

        if self.module.check_mode:
            return {"changed": True}

        response = self.delete_endpoint(endpoint, **{"id": item_id})

        if response.status in [202, 204]:
            self.result["changed"] = True
            self.result["id"] = item_id
            return self.result
        if response.json and "__all__" in response.json:
            msg = f"Unable to delete {item_name}: {response.json['__all__'][0]}"
            raise EDAError(msg)
        if response.json:
            # This is from a project delete (if there is an active
            # job against it)
            if "error" in response.json:
                msg = f"Unable to delete {item_name}: {response.json['error']}"
                raise EDAError(msg)
            msg = f"Unable to delete {item_name}: {response.json}"
            raise EDAError(msg)
        msg = f"Unable to delete {item_name}: {response.status}"
        raise EDAError(msg)

    def copy_if_needed(
        self,
        name: str,
        copy_from: str,
        endpoint: str,
        item_type: str = "unknown",
    ) -> dict[str, bool]:
        """Copy an item if needed.

        Creates a copy of an existing resource with a new name.

        :param name: Name for the new item
        :param copy_from: Name or ID of the source item to copy
        :param endpoint: API endpoint for copying
        :param item_type: Item type for error messages
        :returns: Dictionary with 'changed' and 'id' keys
        """
        response = None
        if not copy_from:
            msg = f"Unable to copy {item_type}, missing copy_from parameter"
            raise EDAError(msg)
        if not endpoint:
            msg = f"Unable to copy {item_type}, missing endpoint"
            raise EDAError(msg)

        if self.module.check_mode:
            return {"changed": True}

        response = self.post_endpoint(endpoint, data={"name": name})
        if response.status in [200, 201]:
            self.result["id"] = response.json["id"]
            self.result["changed"] = True
            return self.result
        if response.json and "__all__" in response.json:
            raise EDAError(response.json["__all__"])
        msg = f"Unable to copy from {item_type} {copy_from}: {response.status}"
        raise EDAError(msg)

    def restart_if_needed(
        self,
        existing_item: dict[str, Any],
        endpoint: str,
    ) -> dict[str, bool]:
        """Restart an activation if needed.

        Executes a restart of an existing EDA activation.

        :param existing_item: Existing activation data with ID
        :param endpoint: API endpoint for restart
        :returns: Dictionary with 'changed' and 'id' keys
        """
        response = None
        if not endpoint:
            msg = "Unable to restart activation, missing endpoint"
            raise EDAError(msg)
        if not existing_item:
            msg = "Unable to restart activation, missing activation parameter"
            raise EDAError(msg)
        if self.module.check_mode:
            return {"changed": True}

        item_id = existing_item["id"]
        response = self.post_endpoint(endpoint, data={"id": item_id})
        if response.status in [200, 201, 204]:
            self.result["id"] = item_id
            self.result["changed"] = True
            return self.result
        if response.json and "__all__" in response.json:
            raise EDAError(response.json["__all__"])
        msg = f"Error restarting activation with ID: {existing_item['id']}"
        raise EDAError(msg)
