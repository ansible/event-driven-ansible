import pytest
import os
import http.server
import threading
from ..utils import CLIRunner, TESTS_PATH
from subprocess import TimeoutExpired

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
    thread.start()
    yield
    httpd.shutdown()


@pytest.mark.parametrize(
    "endpoint, expected_resp_data, expected_resp_code",
    [
        pytest.param("", "UP", 200, id="valid_endpoint"),
        pytest.param("nonexistant", "UNAVAILABLE", 404, id="invalid_endpoint"),
    ],
)
def test_url_check_source_sanity(
    init_webserver, endpoint, expected_resp_data, expected_resp_code
):
    """
    Ensure the url check plugin queries the desired endpoint
    and receives the expected response.
    """

    os.environ["URL_ENDPOINT"] = endpoint

    ruleset = os.path.join(
        TESTS_PATH, "event_source_url_check", "test_url_check_rules.yml"
    )

    runner = CLIRunner(rules=ruleset, envvars="URL_ENDPOINT").run_in_background()

    try:
        result_stdout, _stderr = runner.communicate(timeout=5)
    except TimeoutExpired:
        runner.terminate()
        result_stdout, _stderr = runner.communicate()

    assert f'"msg": "{expected_resp_data}"' in result_stdout.decode()


def test_url_check_source_error_handling():
    """
    Ensure the url check source plugin responds correctly
    when the desired HTTP server is unreachable
    """

    ruleset = os.path.join(
        TESTS_PATH, "event_source_url_check", "test_url_check_rules.yml"
    )

    runner = CLIRunner(rules=ruleset).run_in_background()

    try:
        result_stdout, _stderr = runner.communicate(timeout=5)
    except TimeoutExpired:
        runner.terminate()
        result_stdout, _stderr = runner.communicate()

    assert '"msg": "DOWN"' in result_stdout.decode()
