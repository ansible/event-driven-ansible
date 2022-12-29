"""
cmd.py

An ansible-rulebook event source plugin for running a custom command.
It can send events to the rule engine from the stdout.

Arguments:
    command: str
        The string with the command to execute
    send_output: bool, default: false
        Send events from the stdout.
        Each event must be a serialized JSON string
        ended with a newline character ('\n')
    deserialize: bool, default: true
        Used only if send_output is true
        Deserialize JSON data from the stdout.
        If set to false, the event will be the raw string from the stdout.

Examples:
---
- name: Example with output proccessing
  hosts: all
  sources:
    - ansible.eda.cmd:
        command: node my_custom_plugin.js
        send_output: true
  rules:
    - name: r1
      condition: event.cmd.status == "Running"
      action:
        print_event:


---
- name: Example combined with webhook plugin
  hosts: all
  sources:
    - ansible.eda.webhook:
        port: 6080
    - ansible.eda.cmd:
        command: node my_custom_plugin.js --url http://localhost:6080/eda
  rules:
    - name: r1
      condition: event.payload.status == "Running"
      action:
        print_event:
"""

import asyncio
import json
import logging
import shlex
from typing import Any, Dict

LOGGER = logging.getLogger("ansible.eda.cmd")


async def process_output(
    proc: asyncio.subprocess.Process,
    queue: asyncio.Queue,
    deserialize: bool,
    command: str,
):
    # type hint warn: proc.stdout can be None, this is not our case
    while output := await proc.stdout.readline():
        try:
            if deserialize:
                event = json.loads(output.decode())
            else:
                event = output.decode()

            await queue.put({"cmd": event, "meta": {"command": command}})
        except json.JSONDecodeError as e:
            LOGGER.error("Can not deserialize JSON data: %s", e)


async def main(queue: asyncio.Queue, args: Dict[str, Any]):
    command = str(args["command"])
    send_output = False
    stdout_mode = asyncio.subprocess.DEVNULL

    deserialize = bool(args.get("deserialize", True))
    send_output = bool(args.get("send_output", False))

    if send_output:
        stdout_mode = asyncio.subprocess.PIPE

    cmd_tokens = shlex.split(command)
    proc = await asyncio.subprocess.create_subprocess_exec(
        *cmd_tokens,
        stdout=stdout_mode,
        stderr=asyncio.subprocess.PIPE,
    )

    LOGGER.info("Process started")

    if send_output:
        try:
            _unused_stdout, stderr = await asyncio.gather(
                process_output(proc, queue, deserialize, command),
                # type hint warn: proc.stderr can be None, this is not our case
                proc.stderr.read(),
            )
            await proc.wait()
        except asyncio.CancelledError:
            LOGGER.info("Ansible-rulebook is shutting down, stopping process")
            proc.terminate()
            _unused_stdout, stderr = await proc.communicate()
    else:
        _unused_stdout, stderr = await proc.communicate()

    LOGGER.info("Process finished")

    if proc.returncode != 0:
        LOGGER.error(
            "Command failed with code %s: %s", proc.returncode, stderr.decode()
        )
