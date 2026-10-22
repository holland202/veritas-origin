"""Independent P1 mutation checks; malformed evidence must fail even if rehashed."""
import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


engine = module("p1_generate", "src/origin/exp003_p1.py")
verify = module("p1_verify", "tools/verify_exp003_p1.py")
SECRET = "0123456789abcdef" * 4


class TestP1Verifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = engine.study(SECRET, task_count=4, public_test_secret=True)

    def roundtrip(self, x):
        raw = json.dumps(x, sort_keys=True, allow_nan=False).encode()
        return verify.verify(raw, hashlib.sha256(raw).hexdigest())

    def assert_rejected(self, x, matching):
        with self.assertRaisesRegex(ValueError, matching):
            self.roundtrip(x)

    def test_accepts_original(self):
        result = self.roundtrip(self.data)
        self.assertEqual(result["policy_task_pairs"], 12)

    def test_rejects_digest_mismatch(self):
        raw = json.dumps(self.data).encode()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verify.verify(raw + b" ", hashlib.sha256(raw).hexdigest())

    def test_forged_truth_rehashed(self):
        forged = copy.deepcopy(self.data)
        row = forged["results"][0]
        row["truth"] = "H15" if row["truth"] != "H15" else "H14"
        self.assert_rejected(forged, "task fixture mismatch")

    def test_forged_matrix_rehashed(self):
        forged = copy.deepcopy(self.data)
        forged["results"][1]["matrix"][0][0] ^= 1
        self.assert_rejected(forged, "task fixture mismatch")

    def test_forged_secret_rehashed(self):
        forged = copy.deepcopy(self.data)
        forged["evaluator_secret_hex"] = "f" * 64
        self.assert_rejected(forged, "task fixture mismatch")

    def test_forged_fixed_proposal_rehashed(self):
        forged = copy.deepcopy(self.data)
        row = next(r for r in forged["results"] if r["policy"] == "fixed")
        row["records"][0]["probe"] = 23
        self.assert_rejected(forged, "baseline choice mismatch")

    def test_forged_observation_rehashed(self):
        forged = copy.deepcopy(self.data)
        row = next(r for r in forged["results"] if r["records"])
        row["records"][0]["outcome"] ^= 1
        self.assert_rejected(forged, "oracle outcome mismatch")

    def test_forged_summary_rehashed(self):
        forged = copy.deepcopy(self.data)
        forged["summary"]["greedy"]["solved_rate"] = -1
        self.assert_rejected(forged, "aggregate")

    def test_forged_terminal_state_rehashed(self):
        forged = copy.deepcopy(self.data)
        forged["results"][0]["remaining"] = []
        self.assert_rejected(forged, "terminal candidate mismatch")

    def test_forged_solved_rehashed(self):
        forged = copy.deepcopy(self.data)
        forged["results"][0]["solved"] = not forged["results"][0]["solved"]
        self.assert_rejected(forged, "solved flag mismatch")

    def test_duplicate_result_rehashed(self):
        forged = copy.deepcopy(self.data)
        forged["results"][1] = copy.deepcopy(forged["results"][0])
        self.assert_rejected(forged, "duplicate result")

    def test_forged_status_rehashed(self):
        forged = copy.deepcopy(self.data)
        row = next(r for r in forged["results"] if r["policy"] == "fixed")
        row["status"] = "DEFERRED"
        row["error"] = "INVALID_PROBE"
        self.assert_rejected(forged, "deferred status inconsistent")

    def test_nan_and_duplicate_keys_rehashed(self):
        raw = json.dumps(self.data).encode()
        dup = raw.replace(b"{", b'{"protocol":"EXP003-P1",', 1)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            verify.verify(dup, hashlib.sha256(dup).hexdigest())
        nan = raw.replace(b'"task_count": 4', b'"task_count": NaN')
        with self.assertRaisesRegex(ValueError, "nonfinite JSON"):
            verify.verify(nan, hashlib.sha256(nan).hexdigest())

    def test_external_deferred_replay(self):
        doc = engine.study(
            SECRET, 1, policies=("external",),
            command=[__import__("sys").executable, "-c", "print('{\"probe\":true}')"],
            acknowledge_unisolated=True, model_id="stub-only",
            model_sha256="1" * 64, public_test_secret=True,
        )
        row = doc["results"][0]
        self.assertEqual(row["status"], "DEFERRED")
        self.assertEqual(self.roundtrip(doc)["policy_task_pairs"], 1)


if __name__ == "__main__":
    unittest.main()
