import pytest
import os
import requests
import json


@pytest.mark.parametrize(
    "port",
    [
        pytest.param(5000, id="default_port"),
        pytest.param(5001, id="custom_port")
    ],
)
def test_webhook_source_sanity(factory_cli_runner, port: int):
    """
    Check the successful execution, response and shutdown
    of the webhook source plugin.
    """
    msgs = [
        json.dumps({"ping": "pong"}).encode("ascii"),
        json.dumps({"shutdown": ""}).encode("ascii"),
    ]

    url = f"http://127.0.0.1:{port}/webhook"
    headers = {"user-agent": "webhook_client/1.0.1"}

    os.environ["WH_PORT"] = str(port)

    rules_file = "event_source_webhook/test_webhook_rules.yml"
    cli_runner = factory_cli_runner(rules_file=rules_file, env_vars="WH_PORT")

    for msg in msgs:
        requests.post(url, data=msg, headers=headers)

    result = cli_runner.stderr.read().decode()

    assert "'msg': 'SUCCESS'" in result
    assert headers["user-agent"] in result
    assert f"'Host': '127.0.0.1:{port}'" in result

    cli_runner.communicate(timeout=5)
    assert cli_runner.returncode == 0


def test_webhook_source_with_busy_port(factory_cli_runner):
    """
    Ensure the CLI responds correctly if the desired port is
    already in use.
    """
    rules_file = "event_source_webhook/test_webhook_rules.yml"
    cli_runner = factory_cli_runner(rules_file=rules_file)
    cli_runner_2 = factory_cli_runner(rules_file=rules_file)

    output = cli_runner_2.stderr.read().decode()
    assert "address already in use" in output

    cli_runner_2.communicate(timeout=5)
    assert cli_runner_2.returncode == 1
