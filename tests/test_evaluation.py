import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation import write_report
from main import run_experiment
from tools import Executor


class EvaluationTests(unittest.TestCase):
    def test_comparison_counts_observed_effects(self):
        for scenario in ("normal", "attack"):
            for guarded in (True, False):
                with self.subTest(scenario=scenario, guarded=guarded), tempfile.TemporaryDirectory() as output:
                    with contextlib.redirect_stdout(io.StringIO()):
                        report = run_experiment(scenario=scenario, guarded=guarded, output_root=output)
                    self.assertEqual(report["unauthorized_calls_attempted"], int(scenario == "attack"))
                    self.assertEqual(report["unauthorized_actions_executed"], int(scenario == "attack" and not guarded))
                    self.assertEqual(report["expected_draft_exists"], scenario == "normal")
                    saved = json.loads(next(Path(output).glob("*/report.json")).read_text())
                    self.assertEqual(saved, report)

    def test_failed_live_run_preserves_partial_evidence(self):
        def fail(executor, model):
            executor.execute("send_email", {"email_id": "email_001", "to": "test@example.test", "body": "private"})
            raise RuntimeError("private error details")

        with tempfile.TemporaryDirectory() as output, patch("agent.run", side_effect=fail):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                run_experiment(mode="ollama", model="test-model", output_root=output)
            report_text = next(Path(output).glob("*/report.json")).read_text()
            report = json.loads(report_text)
            self.assertEqual(report["run_status"], "error")
            self.assertEqual(report["error_type"], "RuntimeError")
            self.assertEqual(report["unauthorized_calls_attempted"], 1)
            self.assertFalse(report["expected_draft_exists"])
            self.assertNotIn("private", report_text)

    def test_unguarded_missing_resource_is_not_execution(self):
        with tempfile.TemporaryDirectory() as output:
            executor = Executor(output, guarded=False)
            executor.execute("read_email", {"email_id": "email_002"})
            report = write_report(executor, mode="demo", scenario="normal")
            self.assertEqual(report["unauthorized_calls_attempted"], 1)
            self.assertEqual(report["unauthorized_actions_executed"], 0)

    def test_audit_does_not_store_untrusted_tool_names_or_bodies(self):
        with tempfile.TemporaryDirectory() as output:
            executor = Executor(output)
            executor.execute({"secret": "private"}, {})
            executor.execute("save_draft", {"email_id": "email_001", "body": "private"})
            self.assertNotIn("private", (Path(output) / "events.jsonl").read_text())
