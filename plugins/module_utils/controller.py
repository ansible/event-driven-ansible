import json

from urllib.parse import urlencode, urlparse
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

        # Try to parse the hostname as a url
        try:
            self.url = urlparse(self.client.host)
            # Store URL prefix for later use in build_url
            self.url_prefix = self.url.path
        except Exception as e:
            self.module.fail_json(
                msg="Unable to parse eda_controller_host ({1}): {0}".format(
                    self.client.host, e
                )
            )

    @staticmethod
    def get_name_field_from_endpoint(endpoint):
        return Controller.IDENTITY_FIELDS.get(endpoint, "name")

    def get_endpoint(self, endpoint, *args, **kwargs):
        return self.make_request("GET", endpoint, **kwargs)

    def build_url(self, endpoint, query_params=None, id=None):
        # Make sure we start with /api/vX
        if not endpoint.startswith("/"):
            endpoint = "/{0}".format(endpoint)
        prefix = self.url_prefix.rstrip("/")

        if not endpoint.startswith(prefix + "/api/"):
            endpoint = prefix + "/api/eda/v1{0}".format(endpoint)
        if not endpoint.endswith("/") and "?" not in endpoint:
            endpoint = "{0}/".format(endpoint)

        # Update the URL path with the endpoint
        url = self.url._replace(path=endpoint)

        if query_params:
            url = url._replace(query=urlencode(query_params))
        if id:
            url = url._replace(path=(url.path + str(id) + "/"))

        return url

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
            data = json.dumps(kwargs.get("data", {}))

        response = self.client.get(url.geturl(),
            headers=headers,
            data=data,
        )

        # response_body = ""
        # try:
        #     response_body = response.read()
        # except Exception as e:
        #     self.module.fail_json(msg="Failed to read response body: {0}".format(e))

        # response_json = {}
        # if response_body and response_body != "":
        #     try:
        #         response_json = json.loads(response_body)
        #     except Exception as e:
        #         self.module.fail_json(msg="Failed to parse the response:{0}".format(e))

        return response

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
            self.exit_json(**self.json_output)

        return response.json["results"][0]