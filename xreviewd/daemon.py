import argparse
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from xreviewd.claude_backend import ClaudeWarmBackend
from xreviewd.codex_backend import CodexAppServerBackend


def handle_review_request(backends, payload):
    reviewer = payload.get("reviewer")
    prompt = payload.get("prompt", "")
    cwd = payload.get("cwd") or os.getcwd()
    if reviewer not in backends:
        raise ValueError(f"Unknown reviewer: {reviewer}")
    if not prompt or not prompt.strip():
        raise ValueError("prompt is required")
    started_at = time.monotonic()
    response = backends[reviewer].review(prompt, cwd)
    return {
        "reviewer": reviewer,
        "response": response,
        "timing": {"backend_seconds": round(time.monotonic() - started_at, 6)},
    }


class XReviewHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address, request_handler_class, backends):
        super().__init__(server_address, request_handler_class)
        self.backends = backends


class XReviewHandler(BaseHTTPRequestHandler):
    def _write_json(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path != "/health":
            self._write_json(404, {"error": "not found"})
            return
        self._write_json(200, {"ok": True})

    def do_POST(self):
        if self.path != "/v1/review":
            self._write_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        try:
            result = handle_review_request(self.server.backends, payload)
        except ValueError as exc:
            self._write_json(400, {"error": str(exc)})
            return
        except Exception as exc:  # pragma: no cover - exercised in live probes
            self._write_json(500, {"error": str(exc)})
            return
        self._write_json(200, result)


def build_backends():
    return {"claude": ClaudeWarmBackend(), "codex": CodexAppServerBackend()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    server = XReviewHTTPServer((args.host, args.port), XReviewHandler, build_backends())
    server.serve_forever()


if __name__ == "__main__":
    main()
