import json
import os
import subprocess
import time

import pytest
import requests

from ..utils import TESTS_PATH, CLIRunner


def wait_for_events(proc: subprocess.Popen, timeout: float = 15.0):
    """
    Wait for events to be processed by ansible-rulebook, or timeout.
    Requires the process to be running in debug mode.
    """
    start = time.time()
    if not proc.stdout:  # pragma: no cover
        return
    while stdout := proc.stdout.readline().decode():
        if "Waiting for events" in stdout:
            break
        time.sleep(0.1)
        if time.time() - start > timeout:
            raise TimeoutError("Timeout waiting for events")


@pytest.mark.parametrize(
    "port",
    [
        pytest.param(5000, id="default_port"),
        pytest.param(5001, id="custom_port"),
    ],
)
def test_webhook_source_sanity(subprocess_teardown, port: int):
    """
    Check the successful execution, response and shutdown
    of the webhook source plugin.
    """
    msgs = [
        json.dumps({"ping": "pong"}).encode("ascii"),
        json.dumps({"shutdown": ""}).encode("ascii"),
    ]

    url = f"http://localhost:{port}/webhook"

    env = os.environ.copy()
    env["WH_PORT"] = str(port)
    env["SECRET"] = "secret"

    rules_file = TESTS_PATH + "/event_source_webhook/test_webhook_rules.yml"

    proc = CLIRunner(
        rules=rules_file, envvars="WH_PORT,SECRET", env=env, debug=True
    ).run_in_background()
    subprocess_teardown(proc)

    wait_for_events(proc)

    for msg in msgs:
        headers = {"Authorization": "Bearer secret"}
        requests.post(url, data=msg, headers=headers)

    try:
        stdout, _unused_stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        stdout, _unused_stderr = proc.communicate()

    assert "Rule fired successfully" in stdout.decode()
    assert f"'Host': 'localhost:{port}'" in stdout.decode()
    assert proc.returncode == 0


def test_webhook_source_with_busy_port(subprocess_teardown):
    """
    Ensure the CLI responds correctly if the desired port is
    already in use.
    """
    rules_file = TESTS_PATH + "/event_source_webhook/test_webhook_rules.yml"
    proc1 = CLIRunner(rules=rules_file, debug=True).run_in_background()
    subprocess_teardown(proc1)

    wait_for_events(proc1)

    proc2 = CLIRunner(rules=rules_file, debug=True).run_in_background()
    proc2.wait(timeout=15)
    stdout, _unused_stderr = proc2.communicate()
    assert "address already in use" in stdout.decode()
    assert proc2.returncode == 1


def test_webhook_source_hmac_sanity(subprocess_teardown):
    """
    Check the successful execution, response and shutdown
    of the webhook source plugin.
    """
    msgs = [
        (
            json.dumps({"ping": "pong"}).encode("ascii"),
            "sha256=23fff24c4b9835c6179de19103c6c640150d07d8a72c987b030b541a9d988736",
        ),
        (
            json.dumps({"shutdown": ""}).encode("ascii"),
            "185e5a6124894d6fed1c69c8bea049da241adec83b468c867c4e83627e64d9b9",
        ),
    ]

    port = 5000
    url = f"http://localhost:{port}/webhook"

    env = os.environ.copy()
    env["WH_PORT"] = str(port)
    env["HMAC_SECRET"] = "secret"
    env["HMAC_ALGO"] = "sha256"

    rules_file = TESTS_PATH + "/event_source_webhook/test_webhook_hmac_rules.yml"

    proc = CLIRunner(
        rules=rules_file, envvars="WH_PORT,HMAC_SECRET,HMAC_ALGO", env=env, debug=True
    ).run_in_background()
    subprocess_teardown(proc)

    wait_for_events(proc)

    for msg, digest in msgs:
        headers = {"x-hub-signature-256": digest}
        requests.post(url, data=msg, headers=headers)

    try:
        stdout, _unused_stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        proc.terminate()
        stdout, _unused_stderr = proc.communicate()

    assert "Rule fired successfully" in stdout.decode()
    assert f"'Host': 'localhost:{port}'" in stdout.decode()
    assert proc.returncode == 0


def test_webhook_source_with_unsupported_hmac_algo(subprocess_teardown):
    """
    Ensure the CLI responds correctly if the desired HMAC algorithm is not supported.
    """

    port = 5000
    env = os.environ.copy()
    env["WH_PORT"] = str(port)
    env["HMAC_SECRET"] = "secret"
    env["HMAC_ALGO"] = "invalid_hmac_algo"

    rules_file = TESTS_PATH + "/event_source_webhook/test_webhook_hmac_rules.yml"
    proc = CLIRunner(
        rules=rules_file, envvars="WH_PORT,HMAC_SECRET,HMAC_ALGO", env=env, debug=True
    ).run_in_background()
    proc.wait(timeout=15)
    stdout, _unused_stderr = proc.communicate()
    assert f"Unsupported HMAC algorithm: {env['HMAC_ALGO']}" in stdout.decode()
    assert proc.returncode == 1
