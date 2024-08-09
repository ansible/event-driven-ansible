import logging

logging.basicConfig(filename = '/tmp/file.log',
                    level = logging.DEBUG,
                    format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s')

class Controller:
    IDENTITY_FIELDS = {"users": "username"}
    ENCRYPTED_STRING = "$encrypted$"

    def __init__(
        self,
        client,
        module
    ):
        self.client = client
        self.module = module
        self.json_output = {"changed": False}

        if "update_secrets" in self.module.params:
            self.update_secrets = self.module.params.pop("update_secrets")
        else:
            self.update_secrets = True

    @staticmethod
    def get_name_field_from_endpoint(endpoint):
        return Controller.IDENTITY_FIELDS.get(endpoint, "name")

    def get_endpoint(self, endpoint, *args, **kwargs):
        return self.client.get(endpoint, **kwargs)

    def post_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.module.check_mode:
            self.json_output["changed"] = True
            self.module.exit_json(**self.json_output)

        return self.client.post(endpoint, **kwargs)

    def patch_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.module.check_mode:
            self.json_output["changed"] = True
            self.module.exit_json(**self.json_output)

        return self.client.patch(endpoint, **kwargs)

    def delete_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.module.check_mode:
            self.json_output["changed"] = True
            self.module.exit_json(**self.json_output)

        return self.client.delete(endpoint, **kwargs)

    def get_item_name(self, item, allow_unknown=False):
        if item:
            if "name" in item:
                return item["name"]

            for field_name in Controller.IDENTITY_FIELDS.values():
                if field_name in item:
                    return item[field_name]

        if item:
            self.exit_json(
                msg="Cannot determine identity field for {0} object.".format(
                    item.get("type", "unknown")
                )
            )
        else:
            self.exit_json(msg="Cant determine identity field for Undefined object.")


    def get_one(
        self, endpoint, name=None, allow_none=True, check_exists=False, **kwargs
    ):
        new_kwargs = kwargs.copy()
        response = None

        if name:
            name_field = self.get_name_field_from_endpoint(endpoint)
            new_data = kwargs.get("data", {}).copy()
            new_data["{0}".format(name_field)] = name
            new_kwargs["data"] = new_data

            response = self.get_endpoint(endpoint, **new_kwargs)

            if response.status != 200:
                fail_msg = "Got a {0} when trying to get from {1}".format(
                    response.status, endpoint
                )
                if "detail" in response.json:
                    fail_msg += ",detail: {0}".format(response.json["detail"])
                self.module.fail_json(msg=fail_msg)

            if "count" not in response.json or "results" not in response.json:
                self.module.fail_json(msg="The endpoint did not provide count, results")

        if response.json["count"] == 0:
            if allow_none:
                return None
            else:
                self.fail_wanted_one(response, endpoint, new_kwargs.get("data"))
        elif response.json["count"] > 1:
            if name:
                # Since we did a name or ID search and got > 1 return
                # something if the id matches
                for asset in response.json["results"]:
                    if str(asset["id"]) == name:
                        return asset
            # We got > 1 and either didn't find something by ID (which means
            # multiple names)
            # Or we weren't running with a or search and just got back too
            # many to begin with.
            self.fail_wanted_one(response, endpoint, new_kwargs.get("data"))

        if check_exists:
            self.json_output["id"] = response.json["results"][0]["id"]
            self.module.exit_json(**self.json_output)

        return response.json["results"][0]


    def create_if_needed(
        self,
        existing_item,
        new_item,
        endpoint,
        on_create=None,
        auto_exit=True,
        item_type="unknown",
    ):
        # This will exit from the module on its own
        # If the method successfully creates an item and on_create param is
        # defined,
        #    the on_create parameter will be called as a method pasing in
        #    this object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item is already defined (so no create
        #    needs to happen)
        #    2. The response from EDA from calling the post on the endpont.
        #    It's up to you to process the response and exit from the module
        # Note: common error codes from the EDA API can cause the module to fail
        response = None
        if not endpoint:
            self.module.fail_json(
                msg="Unable to create new {0}, missing endpoint".format(item_type)
            )

        item_url = None
        if existing_item:
            try:
                item_url = existing_item["url"]
            except KeyError as ke:
                self.module.fail_json(
                    msg="Unable to process create for {0}, missing data {1}".format(
                        item_url, ke
                    )
                )
        else:
            # If we don't have an exisitng_item, we can try to create it
            # We will pull the item_name out from the new_item, if it exists
            item_name = self.get_item_name(new_item, allow_unknown=True)
            response = self.post_endpoint(endpoint, **{"data": new_item})
            if response.status in [200, 201]:
                self.json_output["id"] = response.json["id"]
                self.json_output["changed"] = True
            else:
                if response.json and "__all__" in response.json:
                    self.module.fail_json(
                        msg="Unable to create {0} {1}: {2}".format(
                            item_type, item_name, response.json["__all__"][0]
                        )
                    )
                elif response.json:
                    self.module.fail_json(
                        msg="Unable to create {0} {1}: {2}".format(
                            item_type, item_name, response.json
                        )
                    )
                else:
                    self.module.fail_json(
                        msg="Unable to create {0} {1}: {2}".format(
                            item_type, item_name, response.status
                        )
                    )

        # If we have an on_create method and we actually changed something we
        # can call on_create
        if on_create is not None and self.json_output["changed"]:
            on_create(self, response.json)
        elif auto_exit:
            self.module.exit_json(**self.json_output)
        else:
            if response is not None:
                last_data = response.json
                return last_data
            else:
                return

    def _encrypted_changed_warning(self, field, old, warning=False):
        if not warning:
            return
        self.warn(
            "The field {0} of {1} {2} has encrypted data "
            "and may inaccurately report task is changed.".format(
                field, old.get("type", "unknown"), old.get("id", "unknown")
            )
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
                if not Controller.fields_could_be_same(
                    old_field[key], new_field[key]
                ):
                    return False
            return True  # all sub-fields are either equal or could be equal
        else:
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
        auto_exit=True,
    ):
        # This will exit from the module on its own
        # If the method successfully updates an item and on_update param is
        # defined,
        #   the on_update parameter will be called as a method pasing in this
        #   object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item does not need to be updated
        #    2. The response from EDA from patching to the endpoint. It's up
        #    to you to process the response and exit from the module.
        # Note: common error codes from the EDA API can cause the module to fail
        response = None
        if existing_item:
            # If we have an item, we can see if it needs an update
            try:
                if item_type == "user":
                    item_name = existing_item["username"]
                else:
                    item_name = existing_item["name"]
                item_id = existing_item["id"]
            except KeyError as ke:
                self.module.fail_json(
                    msg="Unable to process update, missing data {0}".format(ke)
                )

            # Check to see if anything within the item requires to be updated
            needs_patch = self.objects_could_be_different(existing_item, new_item)

            # If we decided the item needs to be updated, update it
            self.json_output["id"] = item_id
            if needs_patch:
                response = self.patch_endpoint(
                    endpoint, **{"data": new_item, "id": item_id}
                )
                if response.status == 200:
                    # compare apples-to-apples, old API data to new API data
                    # but do so considering the fields given in parameters
                    self.json_output["changed"] |= self.objects_could_be_different(
                        existing_item,
                        response.json,
                        field_set=new_item.keys(),
                        warning=True,
                    )
                elif response.json and "__all__" in response.json:
                    self.fail_json(msg=response.json["__all__"])
                else:
                    self.fail_json(
                        **{
                            "msg": "Unable to update {0} {1}".format(
                                item_type, item_name
                            ),
                            "response": response,
                        }
                    )

        else:
            raise RuntimeError(
                "update_if_needed called incorrectly without existing_item"
            )

        # If we change something and have an on_change call it
        if on_update is not None and self.json_output["changed"]:
            if response is None:
                last_data = existing_item
            else:
                last_data = response.json
            on_update(self, last_data)
        elif auto_exit:
            self.module.exit_json(**self.json_output)
        else:
            if response is None:
                last_data = existing_item
            else:
                last_data = response.json
            return last_data

    def create_or_update_if_needed(
        self,
        existing_item,
        new_item,
        endpoint=None,
        item_type="unknown",
        on_create=None,
        on_update=None,
        auto_exit=True,
    ):
        if existing_item:
            return self.update_if_needed(
                existing_item,
                new_item,
                endpoint,
                item_type=item_type,
                on_update=on_update,
                auto_exit=auto_exit,
            )
        else:
            return self.create_if_needed(
                existing_item,
                new_item,
                endpoint,
                on_create=on_create,
                item_type=item_type,
                auto_exit=auto_exit,
            )

    def delete_if_needed(self, existing_item, endpoint, on_delete=None, auto_exit=True):
        # This will exit from the module on its own.
        # If the method successfully deletes an item and on_delete param is
        # defined,
        #   the on_delete parameter will be called as a method pasing in this
        #   object and the json from the response
        # This will return one of two things:
        #   1. None if the existing_item is not defined (so no delete needs
        #   to happen)
        #   2. The response from EDA from calling the delete on the endpont.
        #   It's up to you to process the response and exit from the module
        # Note: common error codes from the EDA API can cause the module to fail
        if existing_item:
            # If we have an item, we can try to delete it
            try:
                item_id = existing_item["id"]
                item_name = self.get_item_name(existing_item, allow_unknown=True)
            except KeyError as ke:
                self.module.fail_json(
                    msg="Unable to process delete, missing data {0}".format(ke)
                )

            response = self.delete_endpoint(endpoint, **{"id": item_id})

            if response.status in [202, 204]:
                if on_delete:
                    on_delete(self, response.json)
                self.json_output["changed"] = True
                self.json_output["id"] = item_id
                self.module.exit_json(**self.json_output)
                if auto_exit:
                    self.module.exit_json(**self.json_output)
                else:
                    return self.json_output
            else:
                if response.json and "__all__" in response.json:
                    self.module.fail_json(
                        msg="Unable to delete {0}: {1}".format(
                            item_name, response["json"]["__all__"][0]
                        )
                    )
                elif response.json:
                    # This is from a project delete (if there is an active
                    # job against it)
                    if "error" in response.json:
                        self.module.fail_json(
                            msg="Unable to delete {0}: {1}".format(
                                item_name, response["json"]["error"]
                            )
                        )
                    else:
                        self.module.fail_json(
                            msg="Unable to delete {0} {1}".format(
                                item_name, response["json"]
                            )
                        )
                else:
                    self.module.fail_json(
                        msg="Unable to delete {0} {1}".format(
                            item_name, response["status_code"]
                        )
                    )
        else:
            if auto_exit:
                self.module.exit_json(**self.json_output)
            else:
                return self.json_output