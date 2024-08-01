# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import annotations

import re
from json import dumps, loads
from os import environ
from socket import IPPROTO_TCP, getaddrinfo

from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible.module_utils.six import PY2
from ansible.module_utils.six.moves.http_cookiejar import CookieJar
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import urlencode, urlparse
from ansible.module_utils.urls import ConnectionError, Request, SSLValidationError


class ItemNotDefined(Exception):
    pass


class EDAControllerModule(AnsibleModule):
    url = None
    AUTH_ARGSPEC = dict(
        eda_controller_host=dict(
            required=False,
            fallback=(env_fallback, ["EDA_CONTROLLER_HOST"]),
        ),
        eda_controller_username=dict(
            required=False,
            fallback=(env_fallback, ["EDA_CONTROLLER_USERNAME"]),
        ),
        eda_controller_password=dict(
            no_log=True,
            required=False,
            fallback=(env_fallback, ["EDA_CONTROLLER_PASSWORD"]),
        ),
        validate_certs=dict(
            type="bool",
            required=False,
            fallback=(env_fallback, ["EDA_CONTROLLER_VERIFY_SSL"]),
        ),
        request_timeout=dict(
            type="float",
            required=False,
            fallback=(env_fallback, ["EDA_CONTROLLER_REQUEST_TIMEOUT"]),
        ),
    )
    short_params = {
        "host": "eda_controller_host",
        "username": "eda_controller_username",
        "password": "eda_controller_password",
        "verify_ssl": "validate_certs",
        "request_timeout": "request_timeout",
    }
    host = "127.0.0.1"
    username = None
    password = None
    verify_ssl = True
    request_timeout = 10
    version_checked = False
    error_callback = None
    warn_callback = None

    def __init__(
        self,
        argument_spec=None,
        direct_params=None,
        error_callback=None,
        warn_callback=None,
        **kwargs
    ):
        full_argspec = {}
        full_argspec.update(EDAControllerModule.AUTH_ARGSPEC)
        full_argspec.update(argument_spec)
        kwargs["supports_check_mode"] = True

        self.error_callback = error_callback
        self.warn_callback = warn_callback

        self.json_output = {"changed": False}

        if direct_params is not None:
            self.params = direct_params
        else:
            super().__init__(argument_spec=full_argspec, **kwargs)

        # Parameters specified on command line will override
        for short_param, long_param in self.short_params.items():
            direct_value = self.params.get(long_param)
            if direct_value is not None:
                setattr(self, short_param, direct_value)

        # Perform some basic validation
        if not re.match("^https{0,1}://", self.host):
            self.host = f"https://{self.host}"

        # Try to parse the hostname as a url
        try:
            self.url = urlparse(self.host)
            # Store URL prefix for later use in build_url
            self.url_prefix = self.url.path
        except Exception as e:
            self.fail_json(
                msg=f"Unable to parse eda_controller_host ({self.host}): {e}"
            )

        # Remove ipv6 square brackets
        remove_target = "[]"
        for char in remove_target:
            self.url.hostname.replace(char, "")
        # Try to resolve the hostname
        try:
            proxy_env_var_name = f"{self.url.scheme}_proxy"
            if not environ.get(proxy_env_var_name) and not environ.get(
                proxy_env_var_name.upper()
            ):
                addrinfolist = getaddrinfo(
                    self.url.hostname, self.url.port, proto=IPPROTO_TCP
                )
                for family, kind, proto, canonical, sockaddr in addrinfolist:
                    sockaddr[0]
        except Exception as e:
            self.fail_json(
                msg=f"Unable to resolve eda_controller_host ({self.url.hostname}): {e}"
            )

    def build_url(self, endpoint, query_params=None, id=None):
        # Make sure we start with /api/vX
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        prefix = self.url_prefix.rstrip("/")
        if not endpoint.startswith(prefix + "/api/"):
            endpoint = prefix + f"/api/eda/v1{endpoint}"
        if not endpoint.endswith("/") and "?" not in endpoint:
            endpoint = f"{endpoint}/"

        # Update the URL path with the endpoint
        url = self.url._replace(path=endpoint)

        if query_params:
            url = url._replace(query=urlencode(query_params))
        if id:
            url = url._replace(path=(url.path + str(id) + "/"))
        return url

    def fail_json(self, **kwargs):
        if self.error_callback:
            self.error_callback(**kwargs)
        else:
            super().fail_json(**kwargs)

    def exit_json(self, **kwargs):
        super().exit_json(**kwargs)

    def warn(self, warning):
        if self.warn_callback is not None:
            self.warn_callback(warning)
        else:
            super().warn(warning)


class EDAControllerAPIModule(EDAControllerModule):
    IDENTITY_FIELDS = {"users": "username"}
    ENCRYPTED_STRING = "$encrypted$"

    def __init__(
        self,
        argument_spec,
        direct_params=None,
        error_callback=None,
        warn_callback=None,
        **kwargs
    ):
        kwargs["supports_check_mode"] = True

        super().__init__(
            argument_spec=argument_spec,
            direct_params=direct_params,
            error_callback=error_callback,
            warn_callback=warn_callback,
            **kwargs
        )
        self.session = Request(
            cookies=CookieJar(),
            timeout=self.request_timeout,
            validate_certs=self.verify_ssl,
        )

        if "update_secrets" in self.params:
            self.update_secrets = self.params.pop("update_secrets")
        else:
            self.update_secrets = True

    @staticmethod
    def get_name_field_from_endpoint(endpoint):
        return EDAControllerAPIModule.IDENTITY_FIELDS.get(endpoint, "name")

    def get_item_name(self, item, allow_unknown=False):
        if item:
            if "name" in item:
                return item["name"]

            for field_name in EDAControllerAPIModule.IDENTITY_FIELDS.values():
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

    def head_endpoint(self, endpoint, *args, **kwargs):
        return self.make_request("HEAD", endpoint, **kwargs)

    def get_endpoint(self, endpoint, *args, **kwargs):
        return self.make_request("GET", endpoint, **kwargs)

    def patch_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output["changed"] = True
            self.exit_json(**self.json_output)

        return self.make_request("PATCH", endpoint, **kwargs)

    def post_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output["changed"] = True
            self.exit_json(**self.json_output)

        return self.make_request("POST", endpoint, **kwargs)

    def delete_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output["changed"] = True
            self.exit_json(**self.json_output)

        return self.make_request("DELETE", endpoint, **kwargs)

    def get_all_endpoint(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        if "next" not in response["json"]:
            raise RuntimeError(
                f"Expected list from API at {endpoint}, got: {response}"
            )
        next_page = response["json"]["next"]

        if response["json"]["count"] > 10000:
            self.fail_json(
                msg="The number of items being queried is higher than 10,000."
            )

        while next_page is not None:
            next_response = self.get_endpoint(next_page)
            response["json"]["results"] = (
                response["json"]["results"] + next_response["json"]["results"]
            )
            next_page = next_response["json"]["next"]
            response["json"]["next"] = next_page
        return response

    def get_one(
        self, endpoint, name=None, allow_none=True, check_exists=False, **kwargs
    ):
        new_kwargs = kwargs.copy()
        response = None

        if name:
            name_field = self.get_name_field_from_endpoint(endpoint)
            new_data = kwargs.get("data", {}).copy()
            new_data[name_field] = name
            new_kwargs["data"] = new_data

            response = self.get_endpoint(endpoint, **new_kwargs)

            if response["status_code"] != 200:
                fail_msg = f"Got a {response['status_code']} when trying to get from {endpoint}"
                if "detail" in response.get("json", {}):
                    fail_msg += f",detail: {response['json']['detail']}"
                self.fail_json(msg=fail_msg)

            if "count" not in response["json"] or "results" not in response["json"]:
                self.fail_json(msg="The endpoint did not provide count,results")

        if response["json"]["count"] == 0:
            if allow_none:
                return None
            else:
                self.fail_wanted_one(response, endpoint, new_kwargs.get("data"))
        elif response["json"]["count"] > 1:
            if name:
                # Since we did a name or ID search and got > 1 return
                # something if the id matches
                for asset in response["json"]["results"]:
                    if str(asset["id"]) == name:
                        return asset
            # We got > 1 and either didn't find something by ID (which means
            # multiple names)
            # Or we weren't running with a or search and just got back too
            # many to begin with.
            self.fail_wanted_one(response, endpoint, new_kwargs.get("data"))

        if check_exists:
            self.json_output["id"] = response["json"]["results"][0]["id"]
            self.exit_json(**self.json_output)

        return response["json"]["results"][0]

    def fail_wanted_one(self, response, endpoint, query_params):
        sample = response.copy()
        if len(sample["json"]["results"]) > 1:
            sample["json"]["results"] = sample["json"]["results"][:2] + [
                "...more results snipped..."
            ]
        url = self.build_url(endpoint, query_params)
        host_length = len(self.host)
        display_endpoint = url.geturl()[host_length:]  # truncate to not include the base URL
        self.fail_json(
            msg=f"Request to {display_endpoint} returned {response['json']['count']} items, expected 1",
            query=query_params,
            response=sample,
            total_results=response["json"]["count"],
        )

    def get_exactly_one(self, endpoint, name=None, **kwargs):
        return self.get_one(endpoint, name=name, allow_none=False, **kwargs)

    def resolve_name_to_id(self, endpoint, name):
        return self.get_exactly_one(endpoint, name)["id"]

    def make_request(self, method, endpoint, *args, **kwargs):
        # In case someone is calling us directly; make sure we were given a
        # method, let's not just assume a GET
        if not method:
            raise Exception("The HTTP method must be defined")

        if method in ["POST"]:
            url = self.build_url(endpoint)
        elif method in ["DELETE", "PATCH", "PUT"]:
            url = self.build_url(endpoint, id=kwargs.get("id"))
        else:
            url = self.build_url(endpoint, query_params=kwargs.get("data"))

        # Extract the headers, this will be used in a couple of places
        headers = kwargs.get("headers", {})

        if method in ["POST", "PUT", "PATCH"]:
            headers.setdefault("Content-Type", "application/json")
            kwargs["headers"] = headers

        data = (
            None  # Important, if content type is not JSON, this should not
            # be dict type
        )
        if headers.get("Content-Type", "") == "application/json":
            data = dumps(kwargs.get("data", {}))

        try:
            response = self.session.open(
                method,
                url.geturl(),
                url_username=self.username,
                url_password=self.password,
                force_basic_auth=True,
                headers=headers,
                timeout=self.request_timeout,
                validate_certs=self.verify_ssl,
                follow_redirects=True,
                data=data,
            )
        except SSLValidationError as ssl_err:
            self.fail_json(
                msg=f"Couldn't establish connection to host ({url.netloc}): {ssl_err}."
            )
        except ConnectionError as con_err:
            self.fail_json(
                msg=f"Network error while connecting to host ({url.netloc}): {con_err}."
            )
        except HTTPError as he:
            # Sanity check: Did the server send back some kind of internal
            # error?
            if he.code >= 500:
                self.fail_json(
                    msg=f"The host sent back a server error ({url.path}): {he}."
                )
            # Sanity check: Did we fail to authenticate properly?  If so,
            # fail out now; this is always a failure.
            elif he.code == 401:
                self.fail_json(
                    msg=f"Invalid authentication credentials for {url.path}."
                )
            # Sanity check: Did we get a forbidden response, which means that
            # the user isn't allowed to do this? Report that.
            elif he.code == 403:
                self.fail_json(
                    msg=f"You do not have permission to {method} to {url.path}."
                )
            # Sanity check: Did we get a 404 response?
            # Requests with primary keys will return a 404 if there is no
            # response, and we want to consistently trap these.
            elif he.code == 404:
                if kwargs.get("return_none_on_404", False):
                    return None
                self.fail_json(
                    msg=f"The requested object could not be found {url.path}."
                )
            # Sanity check: Did we get a 405 response?
            # A 405 means we used a method that isn't allowed. Usually this
            # is a bad request.
            elif he.code == 405:
                self.fail_json(
                    msg=f"Can not make a request with {method} to endpoint {url.path}"
                )
            # Sanity check: Did we get some other kind of error? If so,
            # write an appropriate error message.
            elif he.code >= 400:
                # We are going to return a 400 so the module can decide what
                # to do with it
                page_data = he.read()
                try:
                    return {"status_code": he.code, "json": loads(page_data)}
                # JSONDecodeError only available on Python 3.5+
                except ValueError:
                    return {"status_code": he.code, "text": page_data}
            elif he.code == 204 and method == "DELETE":
                # A 204 is a normal response for a delete function
                pass
            else:
                self.fail_json(
                    msg=f"Unexpected return code when calling {url.geturl()}: {he}"
                )
        except Exception as e:
            self.fail_json(
                msg=f"Unknown error trying to connect to {url.geturl()}: {type(e).__name__} {e}"
            )

        response_body = ""
        try:
            response_body = response.read()
        except Exception as e:
            self.fail_json(msg=f"Failed to read response body: {e}")

        response_json = {}
        if response_body and response_body != "":
            try:
                response_json = loads(response_body)
            except Exception as e:
                self.fail_json(msg=f"Failed to parse the response:{e}")

        if PY2:
            status_code = response.getcode()
        else:
            status_code = response.status
        return {"status_code": status_code, "json": response_json}

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
                self.fail_json(
                    msg=f"Unable to process delete, missing data {ke}"
                )

            response = self.delete_endpoint(endpoint, **{"id": item_id})

            if response["status_code"] in [202, 204]:
                if on_delete:
                    on_delete(self, response["json"])
                self.json_output["changed"] = True
                self.json_output["id"] = item_id
                self.exit_json(**self.json_output)
                if auto_exit:
                    self.exit_json(**self.json_output)
                else:
                    return self.json_output
            else:
                if "json" in response and "__all__" in response["json"]:
                    self.fail_json(
                        msg=f"Unable to delete {item_name}: {response['json']['__all__'][0]}"
                    )
                elif "json" in response:
                    # This is from a project delete (if there is an active
                    # job against it)
                    if "error" in response["json"]:
                        self.fail_json(
                            msg=f"Unable to delete {item_name}: {response['json']['error']}"
                        )
                    else:
                        self.fail_json(
                            msg=f"Unable to delete {item_name} {response['json']}"
                        )
                else:
                    self.fail_json(
                        msg=f"Unable to delete {item_name} {response['status_code']}"
                    )
        else:
            if auto_exit:
                self.exit_json(**self.json_output)
            else:
                return self.json_output

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
            self.fail_json(
                msg=f"Unable to create new {item_type}, missing endpoint"
            )

        item_url = None
        if existing_item:
            try:
                item_url = existing_item["url"]
            except KeyError as ke:
                self.fail_json(
                    msg=f"Unable to process create for {item_url}, missing data {ke}"
                )
        else:
            # If we don't have an exisitng_item, we can try to create it
            # We will pull the item_name out from the new_item, if it exists
            item_name = self.get_item_name(new_item, allow_unknown=True)
            response = self.post_endpoint(endpoint, **{"data": new_item})
            if response["status_code"] in [200, 201]:
                self.json_output["id"] = response["json"]["id"]
                self.json_output["changed"] = True
            else:
                if "json" in response and "__all__" in response["json"]:
                    self.fail_json(
                        msg=f"Unable to create {item_type} {item_name}: {response['json']['__all__'][0]}"
                    )
                elif "json" in response:
                    self.fail_json(
                        msg=f"Unable to create {item_type} {item_name}: {response['json']}"
                    )
                else:
                    self.fail_json(
                        msg=f"Unable to create {item_type} {item_name}: {response['status_code']}"
                    )

        # If we have an on_create method and we actually changed something we
        # can call on_create
        if on_create is not None and self.json_output["changed"]:
            on_create(self, response["json"])
        elif auto_exit:
            self.exit_json(**self.json_output)
        else:
            if response is not None:
                last_data = response["json"]
                return last_data
            else:
                return

    def _encrypted_changed_warning(self, field, old, warning=False):
        if not warning:
            return
        self.warn(
            f"The field {field} of {old.get('type', 'unknown')} {old.get('id', 'unknown')} has encrypted data "
            "and may inaccurately report task is changed."
        )

    @staticmethod
    def has_encrypted_values(obj):
        """Returns True if JSON-like python content in obj has $encrypted$
        anywhere in the data as a value
        """
        if isinstance(obj, dict):
            for val in obj.values():
                if EDAControllerAPIModule.has_encrypted_values(val):
                    return True
        elif isinstance(obj, list):
            for val in obj:
                if EDAControllerAPIModule.has_encrypted_values(val):
                    return True
        elif obj == EDAControllerAPIModule.ENCRYPTED_STRING:
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
                if not EDAControllerAPIModule.fields_could_be_same(
                    old_field[key], new_field[key]
                ):
                    return False
            return True  # all sub-fields are either equal or could be equal
        else:
            if old_field == EDAControllerAPIModule.ENCRYPTED_STRING:
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
                self.fail_json(
                    msg=f"Unable to process update, missing data {ke}"
                )

            # Check to see if anything within the item requires to be updated
            needs_patch = self.objects_could_be_different(existing_item, new_item)

            # If we decided the item needs to be updated, update it
            self.json_output["id"] = item_id
            if needs_patch:
                response = self.patch_endpoint(
                    endpoint, **{"data": new_item, "id": item_id}
                )
                if response["status_code"] == 200:
                    # compare apples-to-apples, old API data to new API data
                    # but do so considering the fields given in parameters
                    self.json_output["changed"] |= self.objects_could_be_different(
                        existing_item,
                        response["json"],
                        field_set=new_item.keys(),
                        warning=True,
                    )
                elif "json" in response and "__all__" in response["json"]:
                    self.fail_json(msg=response["json"]["__all__"])
                else:
                    self.fail_json(
                        **{
                            "msg": f"Unable to update {item_type} {item_name}",
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
                last_data = response["json"]
            on_update(self, last_data)
        elif auto_exit:
            self.exit_json(**self.json_output)
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
        return self.create_if_needed(
            existing_item,
            new_item,
            endpoint,
            on_create=on_create,
            item_type=item_type,
            auto_exit=auto_exit,
        )
