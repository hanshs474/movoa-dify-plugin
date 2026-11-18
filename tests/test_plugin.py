import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import _client as movoa  # noqa: E402
from tools._common import explain  # noqa: E402


def fake_transport(seq):
    calls = []
    idx = 0

    def _t(method, url, body, headers):
        nonlocal idx
        calls.append((method, url, body, headers))
        code, payload = seq[min(idx, len(seq) - 1)]
        idx += 1
        return code, json.dumps(payload).encode("utf-8")

    _t.calls = calls
    return _t


class TestMovoaDifyPlugin(unittest.TestCase):
    def test_submit_and_wait(self):
        t = fake_transport([
            (200, {"code": 0, "data": {"id": "task-123", "status": "pending"}}),
            (200, {"code": 0, "data": {"status": "processing"}}),
            (200, {"code": 0, "data": {"status": "success", "videos": ["https://cdn.movoa.ai/v.mp4"]}}),
        ])
        tid = movoa.submit("a paper boat", api_key="test-fixture-token", transport=t)
        self.assertEqual(tid, "task-123")
        url = movoa.wait(tid, api_key="test-fixture-token", timeout=5, poll_every=0.01, transport=t)
        self.assertEqual(url, "https://cdn.movoa.ai/v.mp4")

    def test_explain_errors(self):
        self.assertIn("apikeys", explain(movoa.AuthError("bad")))
        self.assertIn("pricing", explain(movoa.PlanError("plan")))
        self.assertIn("credits", explain(movoa.QuotaError("low")))
        self.assertIn("filter", explain(movoa.RejectedError("blocked")))

    def test_live_wrong_key(self):
        with self.assertRaises(movoa.AuthError):
            movoa.submit("test", api_key="invalid-test-fixture-token")


if __name__ == "__main__":
    unittest.main()
