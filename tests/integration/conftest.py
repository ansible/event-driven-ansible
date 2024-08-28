from subprocess import Popen
from typing import Callable, Iterator

import pytest


@pytest.fixture(scope="function")
def subprocess_teardown() -> Iterator[Callable[[Popen[bytes]], None]]:
    processes: list[Popen[bytes]] = []

    def _teardown(process: Popen[bytes]) -> None:
        processes.append(process)

    yield _teardown
    for proc in processes:
        proc.terminate()
