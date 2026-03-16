import json
import os
import select
import subprocess
import threading
import time
from itertools import count
from typing import Dict, Iterable, List


def collect_turn_output(messages: Iterable[dict], turn_id: str) -> str:
    parts: List[str] = []
    for message in messages:
        if message.get("method") != "item/agentMessage/delta":
            continue
        params = message.get("params", {})
        if params.get("turnId") == turn_id:
            parts.append(params.get("delta", ""))
    return "".join(parts).strip()


class CodexAppServerBackend:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ids = count(1)
        self._process = None
        self._initialized = False

    def _start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        self._process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._initialized = False

    def _next_id(self) -> int:
        return next(self._ids)

    def _read_message(self, timeout: float = 180.0) -> dict:
        if self._process is None or self._process.stdout is None or self._process.stderr is None:
            raise RuntimeError("Codex app-server is not running")
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            ready, _, _ = select.select([self._process.stdout, self._process.stderr], [], [], 0.25)
            for stream in ready:
                line = stream.readline()
                if not line:
                    continue
                if stream is self._process.stderr:
                    continue
                return json.loads(line)
        raise TimeoutError("Timed out waiting for Codex app-server output")

    def _send_request(self, method: str, params: dict) -> int:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("Codex app-server stdin is unavailable")
        request_id = self._next_id()
        self._process.stdin.write(
            json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n"
        )
        self._process.stdin.flush()
        return request_id

    def _initialize(self) -> None:
        if self._initialized:
            return
        request_id = self._send_request(
            "initialize",
            {"clientInfo": {"name": "xreviewd", "version": "0.1.0"}, "capabilities": None},
        )
        while True:
            message = self._read_message()
            if message.get("id") == request_id:
                self._initialized = True
                return

    def review(self, prompt: str, cwd: str) -> str:
        cwd = cwd or os.getcwd()
        with self._lock:
            self._start()
            self._initialize()

            thread_request = self._send_request(
                "thread/start",
                {
                    "cwd": cwd,
                    "approvalPolicy": "never",
                    "sandbox": "read-only",
                    "ephemeral": True,
                    "experimentalRawEvents": False,
                    "persistExtendedHistory": False,
                    "developerInstructions": "You are xreviewd, a background review worker. Do not emit setup commentary, bootstrap narration, or tool-preparation chatter. Respond only to the user's request.",
                },
            )

            thread_id = None
            while thread_id is None:
                message = self._read_message()
                if message.get("id") == thread_request:
                    thread_id = message["result"]["thread"]["id"]

            turn_request = self._send_request(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": prompt, "text_elements": []}],
                    "cwd": cwd,
                },
            )

            turn_id = None
            notifications: List[dict] = []
            while True:
                message = self._read_message()
                if message.get("id") == turn_request:
                    turn_id = message["result"]["turn"]["id"]
                    continue
                if "method" in message:
                    notifications.append(message)
                    if turn_id and message.get("method") == "turn/completed":
                        params = message.get("params", {})
                        if params.get("turn", {}).get("id") == turn_id:
                            return collect_turn_output(notifications, turn_id)
                    if turn_id and message.get("method") == "codex/event/task_complete":
                        params = message.get("params", {})
                        if params.get("id") == turn_id:
                            text = collect_turn_output(notifications, turn_id)
                            if text:
                                return text
                            return params.get("msg", {}).get("last_agent_message", "").strip()
