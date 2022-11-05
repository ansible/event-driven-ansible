import pytest
import os
from .utils import CLIRunner, TESTS_PATH
from time import sleep


@pytest.fixture(scope="function")
def factory_cli_runner():
    """
    Factory that returns an instance of the CLI with
    teardown.
    """
    runners = []

    def _cli_runner(rules_file: str, env_vars: str = None):
        ruleset = os.path.join(TESTS_PATH, rules_file)

        runner = CLIRunner(
            rules=ruleset, debug=True, envvars=env_vars
        ).run_in_background()

        # Ensure ansible-events is running
        for i in range(10):
            buffer = runner.stderr.peek().decode()
            if 'Calling main' in buffer:
                break
            else:
                runner.stderr.read1()
                sleep(1)

        runners.append(runner)
        return runner

    yield _cli_runner
    for runner in runners:
        runner.terminate()
