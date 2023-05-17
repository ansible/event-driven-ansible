import os

from ..utils import TESTS_PATH, CLIRunner


def test_cmd_source_with_webhook():
    ruleset = os.path.join(TESTS_PATH, "event_source_cmd", "test_cmd_rules_webhook.yml")

    result = CLIRunner(rules=ruleset).run()

    assert "cmd plugin SUCCESS" in result.stdout.decode()


def test_cmd_source_with_stdout_raw():
    ruleset = os.path.join(
        TESTS_PATH, "event_source_cmd", "test_cmd_rules_stdout_raw.yml"
    )

    result = CLIRunner(rules=ruleset).run()

    assert "cmd plugin SUCCESS" in result.stdout.decode()


def test_cmd_source_with_stdout():
    ruleset = os.path.join(TESTS_PATH, "event_source_cmd", "test_cmd_rules_stdout.yml")

    result = CLIRunner(rules=ruleset).run()

    assert "cmd plugin SUCCESS" in result.stdout.decode()
    assert "cmd plugin SUCCESS meta" in result.stdout.decode()


def test_cmd_source_with_stdout_wrong_output():
    ruleset = os.path.join(
        TESTS_PATH, "event_source_cmd", "test_cmd_rules_stdout_bad_payload.yml"
    )

    result = CLIRunner(rules=ruleset).run()

    assert (
        "ansible.eda.cmd - ERROR - Can not deserialize JSON data:"
        in result.stderr.decode()
    )


def test_cmd_source_with_stdout_with_error():
    ruleset = os.path.join(
        TESTS_PATH, "event_source_cmd", "test_cmd_rules_stdout_error.yml"
    )

    result = CLIRunner(rules=ruleset).run()

    assert "ansible.eda.cmd - ERROR - Command failed" in result.stderr.decode()


def test_cmd_source_with_stdout_with_shutdown():
    ruleset = os.path.join(
        TESTS_PATH, "event_source_cmd", "test_cmd_rules_stdout_shutdown.yml"
    )

    result = CLIRunner(rules=ruleset, debug=True).run()

    assert (
        "Ansible-rulebook is shutting down, stopping process" in result.stdout.decode()
    )
    assert "Process finished" in result.stdout.decode()
    assert "Command failed with code -15" in result.stdout.decode()
