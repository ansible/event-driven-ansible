# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type


import json
from typing import Any, List, NoReturn, Optional

from ansible.module_utils.basic import AnsibleModule

from .client import Client, Response
from .errors import EDAError


class Controller:
    IDENTITY_FIELDS = {"users": "username"}
    ENCRYPTED_STRING = "$encrypted$"

    def __init__(self, client: Client, module: AnsibleModule) -> None:
        self.client = client
        self.module = module
        self.result = {"changed": False}

        if "update_secrets" in self.module.params:
            self.update_secrets = self.module.params.pop("update_secrets")
        else:
            self.update_secrets = True

    @staticmethod
    def get_name_field_from_endpoint(endpoint: str) -> str:
        return Controller.IDENTITY_FIELDS.get(endpoint, "name")

    def get_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        return self.client.get(endpoint, **kwargs)

    def post_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return Response(status=200, data=json.dumps(self.result))

        return self.client.post(endpoint, **kwargs)

    def patch_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return Response(status=200, data=json.dumps(self.result))

        return self.client.patch(endpoint, **kwargs)

    def delete_endpoint(self, endpoint: str, **kwargs: Any) -> Response:
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return Response(status=200, data=json.dumps(self.result))

        return self.client.delete(endpoint, **kwargs)

    def get_item_name(self, item: Any) -> Any:
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
        sample = response.copy()
        sample = sample[:2] + ["...more results snipped..."]
        msg = f"Request returned {len(response)} items, expected 1. See: {sample}"
        raise EDAError(msg)

    def get_exactly_one(
        self, endpoint: str, name: Optional[str], **kwargs: Any
    ) -> dict[str, Any]:
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
        """Run a create (post) operation unconditionally and return the result."""

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
        if not warning:
            return
        self.module.warn(
            f"The field {field} of {old.get('type', 'unknown')} {old.get('id', 'unknown')} "
            "has encrypted data and may inaccurately report task is changed."
        )

    @staticmethod
    def has_encrypted_values(obj: Any) -> bool:
        """Returns True if JSON-like python content in obj has $encrypted$
        anywhere in the data as a value
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
        """Treating $encrypted$ as a wild card,
        return False if the two values are KNOWN to be different
        return True if the two values are the same, or could potentially be same
        depending on the unknown $encrypted$ value or sub-values
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
