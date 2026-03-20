import contextlib
import importlib.machinery
import importlib.util
import io
import pathlib
from types import SimpleNamespace
import unittest
from unittest import mock


from xreviewd.claude_backend import ClaudeWorker, extract_assistant_text
from xreviewd.codex_backend import CodexAppServerBackend, collect_turn_output
import xreviewd.daemon as daemon_module
from xreviewd.daemon import handle_review_request


XREVIEWCTL_PATH = pathlib.Path(__file__).resolve().parents[1] / "bin" / "xreviewctl"
XREVIEWCTL_LOADER = importlib.machinery.SourceFileLoader("xreviewctl_script", str(XREVIEWCTL_PATH))
XREVIEWCTL_SPEC = importlib.util.spec_from_loader("xreviewctl_script", XREVIEWCTL_LOADER)
xreviewctl = importlib.util.module_from_spec(XREVIEWCTL_SPEC)
XREVIEWCTL_SPEC.loader.exec_module(xreviewctl)


class FakeBackend:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def review(self, prompt, cwd):
        self.calls.append((prompt, cwd))
        return f"{self.name}:{prompt[:10]}"


class FakePipe:
    def __init__(self, lines=None):
        self.lines = list(lines or [])
        self.writes = []

    def readline(self):
        if self.lines:
            return self.lines.pop(0)
        return ""

    def write(self, data):
        self.writes.append(data)

    def flush(self):
        return None


class FakeProcess:
    def __init__(self, stdout_lines=None, stderr_lines=None, poll_values=None):
        self.stdin = FakePipe()
        self.stdout = FakePipe(stdout_lines)
        self.stderr = FakePipe(stderr_lines)
        self._poll_values = list(poll_values or [])

    def poll(self):
        if self._poll_values:
            return self._poll_values.pop(0)
        return 0


class ReviewRequestTests(unittest.TestCase):
    def test_handle_review_uses_selected_backend(self):
        backend = FakeBackend("claude")
        fake_time = SimpleNamespace(monotonic=mock.Mock(side_effect=[10.0, 12.5]))
        with mock.patch.object(daemon_module, "time", fake_time, create=True):
            result = handle_review_request(
                {"claude": backend},
                {"reviewer": "claude", "prompt": "review this", "cwd": "/tmp/work"},
            )

        self.assertEqual(result["reviewer"], "claude")
        self.assertEqual(result["response"], "claude:review thi")
        self.assertEqual(result["timing"]["backend_seconds"], 2.5)
        self.assertEqual(backend.calls, [("review this", "/tmp/work")])

    def test_handle_review_rejects_unknown_reviewer(self):
        with self.assertRaises(ValueError):
            handle_review_request({}, {"reviewer": "nope", "prompt": "x"})

    def test_handle_review_requires_prompt(self):
        with self.assertRaises(ValueError):
            handle_review_request({}, {"reviewer": "claude", "prompt": ""})


class ClaudeBackendTests(unittest.TestCase):
    def test_extract_assistant_text_from_stream_json(self):
        text = extract_assistant_text(
            [
                '{"type":"system","subtype":"init"}',
                '{"type":"assistant","message":{"content":[{"type":"text","text":"Hello"}]}}',
            ]
        )

        self.assertEqual(text, "Hello")

    def test_review_waits_for_full_stream_before_returning(self):
        worker = ClaudeWorker.__new__(ClaudeWorker)
        worker.process = FakeProcess(
            stdout_lines=[
                '{"type":"assistant","message":{"content":[{"type":"text","text":"Hello"}]}}\n',
                '{"type":"assistant","message":{"content":[{"type":"text","text":" world"}]}}\n',
            ],
            poll_values=[None, None, 0],
        )

        def fake_select(streams, _write, _error, _timeout):
            ready = [stream for stream in streams if getattr(stream, "lines", None)]
            return ready, [], []

        with mock.patch("xreviewd.claude_backend.select.select", side_effect=fake_select):
            self.assertEqual(worker.review("review me", timeout=0.1), "Hello world")

    def test_review_raises_runtime_error_from_stderr_without_waiting_for_timeout(self):
        worker = ClaudeWorker.__new__(ClaudeWorker)
        worker.process = FakeProcess(
            stderr_lines=["authentication failed\n"],
            poll_values=[1],
        )

        def fake_select(streams, _write, _error, _timeout):
            ready = [stream for stream in streams if getattr(stream, "lines", None)]
            return ready, [], []

        with mock.patch("xreviewd.claude_backend.select.select", side_effect=fake_select):
            with self.assertRaisesRegex(RuntimeError, "authentication failed"):
                worker.review("review me", timeout=0.1)


class CodexBackendTests(unittest.TestCase):
    def test_collect_turn_output_accumulates_deltas_until_completion(self):
        messages = [
            {"method": "item/agentMessage/delta", "params": {"threadId": "t1", "turnId": "turn-1", "itemId": "1", "delta": "Hel"}},
            {"method": "item/agentMessage/delta", "params": {"threadId": "t1", "turnId": "turn-1", "itemId": "1", "delta": "lo"}},
            {"method": "turn/completed", "params": {"threadId": "t1", "turn": {"id": "turn-1"}}},
        ]

        self.assertEqual(collect_turn_output(messages, "turn-1"), "Hello")

    def test_collect_turn_output_ignores_non_matching_turns(self):
        messages = [
            {"method": "item/agentMessage/delta", "params": {"threadId": "t1", "turnId": "turn-2", "itemId": "1", "delta": "Nope"}},
            {"method": "item/agentMessage/delta", "params": {"threadId": "t1", "turnId": "turn-1", "itemId": "1", "delta": "OK"}},
            {"method": "codex/event/task_complete", "params": {"id": "turn-1", "msg": {"last_agent_message": "OK"}}},
        ]

        self.assertEqual(collect_turn_output(messages, "turn-1"), "OK")

    def test_read_message_raises_runtime_error_from_stderr(self):
        backend = CodexAppServerBackend()
        backend._process = FakeProcess(stderr_lines=['{"error":"boom"}\n'])

        def fake_select(streams, _write, _error, _timeout):
            ready = [stream for stream in streams if getattr(stream, "lines", None)]
            return ready, [], []

        with mock.patch("xreviewd.codex_backend.select.select", side_effect=fake_select):
            with self.assertRaisesRegex(RuntimeError, 'boom'):
                backend._read_message(timeout=0.1)


class XReviewCtlTests(unittest.TestCase):
    def test_review_prints_timing_summary_when_enabled(self):
        class FakeHTTPResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return (
                    b'{"response":"review output","timing":{"daemon_start_seconds":1.25,'
                    b'"request_seconds":2.5,"total_seconds":3.75}}'
                )

        args = SimpleNamespace(reviewer="codex", cwd="/tmp/work", timeout=10, timing=True)
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch.object(xreviewctl, "start_daemon") as start_daemon:
            with mock.patch.object(xreviewctl.urllib.request, "urlopen", return_value=FakeHTTPResponse()):
                with mock.patch.object(xreviewctl.sys, "stdin", io.StringIO("review this")):
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        self.assertEqual(xreviewctl.review(args), 0)

        start_daemon.assert_called_once()
        self.assertEqual(stdout.getvalue().strip(), "review output")
        self.assertIn("daemon_start=1.250s", stderr.getvalue())
        self.assertIn("request=2.500s", stderr.getvalue())
        self.assertIn("total=3.750s", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
