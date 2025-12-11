import http.server
import os
import threading
import time
from typing import Any, Callable, Generator

import pytest

from .. import TESTS_PATH
from ..utils import DEFAULT_TEST_TIMEOUT, CLIRunner

EVENT_SOURCE_DIR = os.path.dirname(__file__)


class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        base_dir = os.path.join(TESTS_PATH, EVENT_SOURCE_DIR, "webserver_files")
        super().__init__(*args, **kwargs, directory=base_dir)

    def log_message(self, format: str, *args: Any) -> None:
        # do not log http.server messages
        pass


@pytest.fixture(scope="function")
def init_webserver() -> Generator[Any, Any, Any]:
    handler = HttpHandler
    port: int = 8000
    httpd = http.server.HTTPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()
    yield
    httpd.shutdown()


@pytest.mark.timeout(timeout=DEFAULT_TEST_TIMEOUT, method="signal")
@pytest.mark.parametrize(
    "endpoint, expected_resp_data",
    [
        pytest.param("", "Endpoint available", id="valid_endpoint"),
        pytest.param("nonexistent", "Endpoint unavailable", id="invalid_endpoint"),
    ],
)
def test_url_check_source_sanity(
    init_webserver: None,
    subprocess_teardown: Callable[..., None],
    endpoint: str,
    expected_resp_data: str,
) -> None:
    """
    Ensure the url check plugin queries the desired endpoint
    and receives the expected response.
    """

    os.environ["URL_ENDPOINT"] = endpoint

    ruleset = os.path.join(
        TESTS_PATH, "event_source_url_check", "test_url_check_rules.yml"
    )

    runner = CLIRunner(rules=ruleset, envvars="URL_ENDPOINT").run_in_background()
    subprocess_teardown(runner)

    assert runner.stdout is not None
    while line := runner.stdout.readline().decode():
        if "msg" in line:
            assert f'"msg": "{expected_resp_data}"' in line
            break


@pytest.mark.timeout(timeout=DEFAULT_TEST_TIMEOUT, method="signal")
def test_url_check_source_error_handling(
    subprocess_teardown: Callable[..., None],
) -> None:
    """
    Ensure the url check source plugin responds correctly
    when the desired HTTP server is unreachable
    """

    ruleset = os.path.join(
        TESTS_PATH, "event_source_url_check", "test_url_check_rules.yml"
    )

    runner = CLIRunner(rules=ruleset).run_in_background()
    subprocess_teardown(runner)

    assert runner.stdout is not None
    while line := runner.stdout.readline().decode():
        if "msg" in line:
            assert "Endpoint down" in line
            break


@pytest.mark.timeout(timeout=DEFAULT_TEST_TIMEOUT, method="signal")
def test_url_check_source_urls(
    init_webserver: None,
) -> None:
    """
    Ensure the url check source plugin reports correctly the status
    of all the urls, and not only until the first failure
    """

    ruleset = os.path.join(
        TESTS_PATH, "event_source_url_check", "test_url_check_rules_urls.yml"
    )

    runner = CLIRunner(rules=ruleset).run_in_background()
    # enough time to checks all the URLs
    time.sleep(10)
    runner.terminate()

    (stdout, stderr) = runner.communicate()
    assert stdout is not None
    msgs = [line for line in stdout.decode().splitlines() if "msg" in line]
    assert len(msgs) == 3
    assert len([line for line in msgs if "Endpoint available" in line]) == 1
    assert len([line for line in msgs if "Endpoint unavailable" in line]) == 1
    assert len([line for line in msgs if "Endpoint down" in line]) == 1
