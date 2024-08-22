# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)
from __future__ import absolute_import, annotations, division, print_function

__metaclass__ = type


from typing import Any, List, NoReturn, Optional

from ansible.module_utils.basic import AnsibleModule

from .client import Client
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

    def get_endpoint(self, endpoint, **kwargs):
        return self.client.get(endpoint, **kwargs)

    def post_endpoint(self, endpoint, **kwargs):
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return self.result

        return self.client.post(endpoint, **kwargs)

    def patch_endpoint(self, endpoint, **kwargs):
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return self.result

        return self.client.patch(endpoint, **kwargs)

    def delete_endpoint(self, endpoint, **kwargs):
        # Handle check mode
        if self.module.check_mode:
            self.result["changed"] = True
            return self.result

        return self.client.delete(endpoint, **kwargs)

    def get_item_name(self, item):
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

    def fail_wanted_one(self, response, endpoint, query_params) -> NoReturn:
        url = self.client.build_url(endpoint, query_params)
        host_length = len(self.client.host)
        display_endpoint = url.geturl()[
            host_length:
        ]  # truncate to not include the base URL
        msg = (
            f"Request to {display_endpoint} returned {len(response)} items, expected 1"
        )
        raise EDAError(msg)

    def get_exactly_one(self, endpoint, name=None, **kwargs) -> dict[str, Any]:
        new_kwargs = kwargs.copy()

        result = self.get_one_or_many(endpoint, name=name, **kwargs)

        if len(result) == 0:
            return {}

        if len(result) > 1:
            if name:
                # Since we did a name or ID search and got > 1 return
                # something if the id matches
                for asset in result:
                    if str(asset["id"]) == name:
                        return asset
            # We got > 1 and either didn't find something by ID (which means
            # multiple names)
            # Or we weren't running with a or search and just got back too
            # many to begin with.
            self.fail_wanted_one(result, endpoint, new_kwargs.get("data"))

        return result[0]

    def resolve_name_to_id(self, endpoint, name, **kwargs):
        result = self.get_exactly_one(endpoint, name, **kwargs)
        if result:
            return result["id"]
        return None

    def get_one_or_many(
        self,
        endpoint: str,
        name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[Any]:
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

        return response.json["results"]

    def create_if_needed(
        self,
        existing_item,
        new_item,
        endpoint,
        on_create=None,
        item_type="unknown",
    ):
        # This will exit from the module on its own
        # If the method successfully creates an item and on_create param is
        # defined,
        #    the on_create parameter will be called as a method passing in
        #    this object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item is already defined (so no create
        #    needs to happen)
        #    2. The response from EDA from calling the post on the endpoint.
        #    It's up to you to process the response and exit from the module
        # Note: common error codes from the EDA API can cause the module to fail
        response = None
        if not endpoint:
            msg = f"Unable to create new {item_type}, missing endpoint"
            raise EDAError(msg)

        item_url = None
        if existing_item:
            try:
                item_url = existing_item["url"]
            except KeyError as e:
                msg = f"Unable to process create for {item_url}, missing data {e}"
                raise EDAError(msg) from e
        else:
            if self.module.check_mode:
                return {"changed": True}

            # If we don't have an existing_item, we can try to create it
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

        # If we have an on_create method and we actually changed something we can call on_create
        if on_create is not None and self.result["changed"]:
            on_create(self, response["json"])
        else:
            if response is not None:
                last_data = response["json"]
                return last_data
            return

    def _encrypted_changed_warning(self, field, old, warning=False):
        if not warning:
            return
        self.module.warn(
            f"The field {field} of {old.get('type', 'unknown')} {old.get('id', 'unknown')} "
            "has encrypted data and may inaccurately report task is changed."
        )

    @staticmethod
    def has_encrypted_values(obj):
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
    def fields_could_be_same(old_field, new_field):
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

    def objects_could_be_different(self, old, new, field_set=None, warning=False):
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
            elif self.has_encrypted_values(new_field) or field not in new:
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
        existing_item,
        new_item,
        endpoint,
        item_type,
        on_update=None,
    ):
        # This will exit from the module on its own
        # If the method successfully updates an item and on_update param is
        # defined,
        #   the on_update parameter will be called as a method passing in this
        #   object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item does not need to be updated
        #    2. The response from EDA from patching to the endpoint. It's up
        #    to you to process the response and exit from the module.
        # Note: common error codes from the EDA API can cause the module to fail
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
                endpoint, **{"data": new_item, "id": item_id}
            )
            if response.status == 200:
                # compare apples-to-apples, old API data to new API data
                # but do so considering the fields given in parameters
                self.result["changed"] |= self.objects_could_be_different(
                    existing_item,
                    response.json,
                    field_set=new_item.keys(),
                    warning=True,
                )
                return self.result
            if response.json and "__all__" in response.json:
                raise EDAError(response.json["__all__"])
            msg = f"Unable to update {item_type} {item_name}"
            raise EDAError(msg)

        # If we change something and have an on_change call it
        if on_update is not None and self.result["changed"]:
            if response is None:
                last_data = existing_item
            else:
                last_data = response["json"]
            on_update(self, last_data)
        else:
            if response is None:
                last_data = existing_item
            else:
                last_data = response["json"]
            return last_data

    def create_or_update_if_needed(
        self,
        existing_item,
        new_item,
        endpoint=None,
        item_type="unknown",
        on_create=None,
        on_update=None,
    ):
        if existing_item:
            return self.update_if_needed(
                existing_item,
                new_item,
                endpoint,
                item_type=item_type,
                on_update=on_update,
            )
        return self.create_if_needed(
            existing_item,
            new_item,
            endpoint,
            item_type=item_type,
            on_create=on_create,
        )

    def delete_if_needed(self, existing_item, endpoint, on_delete=None):
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
            if on_delete:
                on_delete(self, response.json)
            self.result["changed"] = True
            self.result["id"] = item_id
            return self.result
        if response.json and "__all__" in response.json:
            msg = f"Unable to delete {item_name}: {response['json']['__all__'][0]}"
            raise EDAError(msg)
        if response.json:
            # This is from a project delete (if there is an active
            # job against it)
            if "error" in response.json:
                msg = f"Unable to delete {item_name}: {response['json']['error']}"
                raise EDAError(msg)
            msg = f"Unable to delete {item_name}: {response['json']}"
            raise EDAError(msg)
        msg = f"Unable to delete {item_name}: {response['status_code']}"
        raise EDAError(msg)
