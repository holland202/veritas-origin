"""EXP003-P1 behavioral and boundary tests. No cloud or model access."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("engine_p1", ROOT / "src/origin/exp003_p1.py")
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)
SEED = "0123456789abcdef" * 4


class TestP1(unittest.TestCase):
    def test_task_generation_reproducible_and_unique(self):
        first = engine.make_task(SEED, 3)
        self.assertEqual(first, engine.make_task(SEED, 3))
        self.assertEqual(len(first["hypotheses"]), 16)
        self.assertEqual(len(first["matrix"]), 16)
        self.assertEqual(len({tuple(x) for x in first["matrix"]}), 16)
        self.assertTrue(all(len(row) == 24 and set(row) <= {0, 1}
                            for row in first["matrix"]))

    def test_different_secret_and_index(self):
        a = engine.make_task(SEED, 0)
        self.assertNotEqual(a["matrix"], engine.make_task(SEED, 1)["matrix"])
        self.assertNotEqual(a["matrix"], engine.make_task("f" * 64, 0)["matrix"])

    def test_deterministic_baseline_replay(self):
        a = engine.study(SEED, task_count=5, public_test_secret=True)
        b = engine.study(SEED, task_count=5, public_test_secret=True)
        self.assertEqual(a, b)
        self.assertEqual(len(a["results"]), 15)
        self.assertEqual(a["task_origin"], "PUBLIC_TEST_SECRET")

    def test_oracle_transition_and_budget(self):
        for row in engine.study(SEED, task_count=8)["results"]:
            self.assertLessEqual(len(row["records"]), 5)
            self.assertEqual(row["status"], "COMPLETE")
            self.assertIsNone(row["error"])
            pre = list(engine.HYPOTHESES)
            used = set()
            for i, event in enumerate(row["records"]):
                self.assertEqual(event["step"], i)
                self.assertEqual(event["pre"], pre)
                self.assertNotIn(event["probe"], used)
                self.assertEqual(event["outcome"], row["matrix"][
                    engine.HYPOTHESES.index(row["truth"])][event["probe"]])
                pre = [h for h in pre if row["matrix"][
                    engine.HYPOTHESES.index(h)][event["probe"]] == event["outcome"]]
                self.assertEqual(event["post"], pre)
                used.add(event["probe"])
            self.assertEqual(row["remaining"], pre)
            self.assertEqual(row["solved"], len(pre) == 1)

    def test_external_omits_oracle_and_secret(self):
        observed = []
        def proposer(command, ctx, timeout):
            observed.append(ctx)
            self.assertNotIn("truth", ctx)
            self.assertNotIn("evaluator_secret_hex", ctx)
            self.assertNotIn("task_index", ctx)
            self.assertEqual(ctx["protocol"], "EXP003-P1")
            return ctx["available_probes"][0]
        with patch.object(engine, "external_proposal", side_effect=proposer):
            result = engine.evaluate(SEED, 0, "external", ["trusted"], timeout=1)
        self.assertTrue(observed)
        self.assertEqual(result["status"], "COMPLETE")

    def test_external_invalid_proposal_fails_closed(self):
        command = [sys.executable, "-c", "print('{\"probe\": true}')"]
        row = engine.evaluate(SEED, 0, "external", command, timeout=2)
        self.assertEqual(row["status"], "DEFERRED")
        self.assertEqual(row["error"], "INVALID_PROBE")
        self.assertFalse(row["records"])

    def test_external_duplicate_key_fails_closed(self):
        command = [sys.executable, "-c", "print('{\"probe\": 0, \"probe\": 1}')"]
        row = engine.evaluate(SEED, 0, "external", command, timeout=2)
        self.assertEqual(row["status"], "DEFERRED")
        self.assertEqual(row["error"], "PROPOSER_INVALID_JSON")

    def test_unsandboxed_requires_acknowledgment(self):
        with self.assertRaisesRegex(ValueError, "unsandboxed"):
            engine.study(SEED, task_count=1, policies=("external",),
                         command=[sys.executable, "-c", "print('{}')"],
                         model_id="placeholder", model_sha256="1" * 64)

    def test_external_requires_model_metadata(self):
        with self.assertRaisesRegex(ValueError, "model id"):
            engine.study(SEED, task_count=1, policies=("external",),
                         command=[sys.executable, "-c", "print('{}')"],
                         acknowledge_unisolated=True)

    def test_external_valid_stub(self):
        code = ("import json,sys; c=json.load(sys.stdin); "
                "print(json.dumps({'probe':c['available_probes'][0]}))")
        result = engine.study(SEED, task_count=2,
                              policies=("fixed", "random", "greedy", "external"),
                              command=[sys.executable, "-c", code],
                              acknowledge_unisolated=True,
                              model_id="test-only-stub", model_sha256="1" * 64,
                              public_test_secret=True)
        self.assertEqual(len(result["results"]), 8)
        self.assertFalse(any(r["status"] == "DEFERRED" for r in result["results"]))
        self.assertEqual(result["model_metadata"]["id"], "test-only-stub")

    def test_no_implicit_run_or_model(self):
        with self.assertRaises(SystemExit):
            engine.main(["--task-count", "1"])
        with self.assertRaises(SystemExit):
            engine.main(["--pilot", "--external-command", "python3 -V"])

    def test_public_test_secret_requires_explicit_flag(self):
        with self.assertRaises(SystemExit):
            engine.main(["--pilot", "--test-secret-hex", SEED])

    def test_exclusive_evidence_write(self):
        with tempfile.TemporaryDirectory() as d:
            evidence = engine.study(SEED, 1, public_test_secret=True)
            x, hx = engine.save_fresh(evidence, Path(d))
            y, hy = engine.save_fresh(evidence, Path(d))
            self.assertNotEqual(x, y)
            self.assertEqual(hx, hy)
            self.assertEqual(json.loads(x.read_text()), evidence)

    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            engine.study(SEED, 21)
        with self.assertRaises(ValueError):
            engine.study(SEED, 1, timeout=100)
        with self.assertRaises(ValueError):
            engine.study("not-secret", 1)


if __name__ == "__main__":
    unittest.main()
