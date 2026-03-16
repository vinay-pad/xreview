import json
import os
import select
import subprocess
import threading
import time
from typing import Iterable, List


def extract_assistant_text(lines: Iterable[str]) -> str:
    chunks: List[str] = []
    for line in lines:
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "assistant":
            continue
        message = event.get("message", {})
        for item in message.get("content", []):
            if item.get("type") == "text":
                chunks.append(item.get("text", ""))
    text = "".join(chunks).strip()
    if not text:
        raise RuntimeError("Claude worker returned no assistant text")
    return text


class ClaudeWorker:
    def __init__(self, cwd: str):
        self.cwd = cwd
        self.process = subprocess.Popen(
            [
                "claude",
                "-p",
                "--verbose",
                "--input-format",
                "stream-json",
                "--output-format",
                "stream-json",
                "--no-session-persistence",
                "--append-system-prompt",
                "You are xreviewd, a background review worker. Do not emit setup commentary, bootstrap narration, or tool-preparation chatter. Respond only to the user's request.",
            ],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def review(self, prompt: str, timeout: float = 180.0) -> str:
        if self.process.stdin is None or self.process.stdout is None or self.process.stderr is None:
            raise RuntimeError("Claude worker pipes are unavailable")
        payload = {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            },
        }
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

        lines: List[str] = []
        done = False
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            ready, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], 0.25)
            for stream in ready:
                line = stream.readline()
                if not line:
                    continue
                if stream is self.process.stderr:
                    continue
                lines.append(line.strip())
                if '"type":"assistant"' in line or '"type": "assistant"' in line:
                    done = True
            if done:
                return extract_assistant_text(lines)
            if self.process.poll() is not None:
                break
        raise TimeoutError("Timed out waiting for Claude worker output")

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()


class ClaudeWarmBackend:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._spares = {}

    def _spawn(self, cwd: str) -> ClaudeWorker:
        return ClaudeWorker(cwd)

    def _spawn_spare(self, cwd: str) -> None:
        try:
            worker = self._spawn(cwd)
        except Exception:
            return
        with self._lock:
            if cwd not in self._spares:
                self._spares[cwd] = worker
                return
        worker.close()

    def review(self, prompt: str, cwd: str) -> str:
        cwd = cwd or os.getcwd()
        with self._lock:
            worker = self._spares.pop(cwd, None)
        if worker is None:
            worker = self._spawn(cwd)
        replacement = threading.Thread(target=self._spawn_spare, args=(cwd,), daemon=True)
        replacement.start()
        try:
            return worker.review(prompt)
        finally:
            worker.close()
