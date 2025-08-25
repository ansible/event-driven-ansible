import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, List, Optional

from . import TESTS_PATH

DEFAULT_TEST_TIMEOUT: int = 25


def wait_for_kafka_ready(bootstrap_servers: str = "localhost:9092", timeout: int = 30, check_ssl: bool = False) -> None:
    """
    Wait for Kafka broker to be ready by attempting to create a producer.

    Args:
        bootstrap_servers: Kafka bootstrap servers
        timeout: Maximum time to wait in seconds
        check_ssl: Whether to check SSL/SASL ports (may not be ready immediately)

    Raises:
        Exception: If Kafka is not ready within timeout
    """
    try:
        from kafka import KafkaProducer
    except ImportError:
        print("kafka-python-ng not available, skipping health check")
        return

    # For SSL/SASL ports, just check if the port is open rather than full producer
    if check_ssl and ("9093" in bootstrap_servers or "9094" in bootstrap_servers or "9095" in bootstrap_servers):
        import socket
        host, port = bootstrap_servers.split(":")
        port = int(port)

        for attempt in range(timeout):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    print(f"Kafka broker port {bootstrap_servers} is listening")
                    return
            except Exception:
                pass
            if attempt == 0:
                print(f"Waiting for Kafka broker port {bootstrap_servers} to be listening...")
            time.sleep(1)

        print(f"Warning: Kafka broker port {bootstrap_servers} not ready after {timeout} seconds (may need SSL/SASL setup)")
        return

    for attempt in range(timeout):
        try:
            producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                request_timeout_ms=1000,
                retries=0
            )
            producer.close()
            print(f"Kafka broker at {bootstrap_servers} is ready")
            return
        except Exception as e:
            if attempt == 0:
                print(f"Waiting for Kafka broker at {bootstrap_servers} to be ready...")
            time.sleep(1)

    raise Exception(f"Kafka broker at {bootstrap_servers} not ready after {timeout} seconds")


@dataclass
class CLIRunner:
    """
    Wrapper of subprocess.run to compose cmd's for ansible-rulebook CLI
    """

    cwd: str = TESTS_PATH
    base_cmd: str = "ansible-rulebook"
    inventory: str = os.path.join(TESTS_PATH, "default_inventory.yml")
    rules: Optional[str] = None
    sources: Optional[str] = None
    extra_vars: Optional[str] = None
    envvars: Optional[str] = None
    proc_id: Optional[str] = None
    verbose: bool = False
    debug: bool = False
    timeout: float = 30.0  # Increased from 10.0 for better reliability
    env: Optional[dict[str, str]] = None

    def __post_init__(self) -> None:
        self.env = os.environ.copy() if self.env is None else self.env

    def _process_args(self) -> List[str]:
        args = [
            self.base_cmd,
        ]

        args.extend(["-i", self.inventory])

        if self.rules:
            args.extend(["--rulebook", self.rules])
        if self.sources:
            args.extend(["-S", self.sources])
        if self.extra_vars:
            args.extend(["--vars", self.extra_vars])
        if self.envvars:
            args.extend(["--env-vars", self.envvars])
        if self.proc_id:
            args.extend(["--id", self.proc_id])
        if self.verbose:
            args.append("-v")
        if self.debug:
            args.append("-vv")

        return args

    def run(self) -> subprocess.CompletedProcess[Any]:
        args = self._process_args()
        print("Running command: ", " ".join(args))

        # Set up environment with unbuffered output for more reliable stdout capture
        env = self.env.copy() if self.env else os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        return subprocess.run(
            args,
            cwd=self.cwd,
            capture_output=True,
            timeout=self.timeout,
            check=True,
            env=env,
        )

    def run_in_background(self) -> subprocess.Popen[bytes]:
        args = self._process_args()
        print("Running command: ", " ".join(args))
        return subprocess.Popen(
            args,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
        )
