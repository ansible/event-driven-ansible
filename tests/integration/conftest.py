import pytest


@pytest.fixture(scope="function")
def subprocess_teardown():
    processes = []

    def _teardown(process) -> None:
        processes.append(process)

    yield _teardown
    [proc.terminate() for proc in processes]
