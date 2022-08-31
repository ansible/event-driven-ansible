import pytest
import os
import http.server
import threading
from ..utils import TESTS_PATH

EVENT_SOURCE_DIR = os.path.dirname(__file__)


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        base_dir = os.path.join(TESTS_PATH, EVENT_SOURCE_DIR, "webserver_files")
        super().__init__(*args, **kwargs, directory=base_dir)

    def log_message(self, format, *args):
        # do not log http.server messages
        pass


@pytest.fixture(scope="function")
def init_webserver():
    handler = HttpHandler
    port: int = 8000
    httpd = http.server.HTTPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    yield
    httpd.shutdown()


@pytest.mark.parametrize(
    "endpoint, expected_response",
    [
        pytest.param("", 200, id="valid_endpoint"),
        pytest.param("nonexistant", 404, id="invalid_endpoint"),
    ],
)
def test_url_check_source_sanity(
    init_webserver, factory_cli_runner, endpoint, expected_response
):
    """
    Ensure the url check plugin queries the desired endpoint
    and receives the expected response.
    """

    os.environ["URL_ENDPOINT"] = endpoint

    rules_file = f"{EVENT_SOURCE_DIR}/test_url_check_rules.yml"
    cli_runner = factory_cli_runner(rules_file=rules_file, env_vars="URL_ENDPOINT")

    result = cli_runner.stderr.read1().decode()

    assert f"'status_code': {expected_response}" in result
