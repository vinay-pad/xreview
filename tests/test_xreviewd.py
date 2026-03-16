import unittest


from xreviewd.claude_backend import extract_assistant_text
from xreviewd.codex_backend import collect_turn_output
from xreviewd.daemon import handle_review_request


class FakeBackend:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def review(self, prompt, cwd):
        self.calls.append((prompt, cwd))
        return f"{self.name}:{prompt[:10]}"


class ReviewRequestTests(unittest.TestCase):
    def test_handle_review_uses_selected_backend(self):
        backend = FakeBackend("claude")
        result = handle_review_request(
            {"claude": backend},
            {"reviewer": "claude", "prompt": "review this", "cwd": "/tmp/work"},
        )

        self.assertEqual(result["reviewer"], "claude")
        self.assertEqual(result["response"], "claude:review thi")
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


if __name__ == "__main__":
    unittest.main()
