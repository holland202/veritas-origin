"""Negative controls for the standalone EXP002 verifier.

These tests modify only temporary copies. Frozen runner and research evidence
are read-only. Re-hashing a corrupted copy deliberately bypasses the digest
guard so that the semantic checker is exercised.
"""
import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tools/verify_exp002.py"
spec = importlib.util.spec_from_file_location("exp002_standalone_verifier", SOURCE)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class TestEXP002Verifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = verifier.EVIDENCE.read_bytes()
        cls.parsed = json.loads(cls.original)

    def check_mutation(self, raw, expected_error, rehash=True):
        with tempfile.TemporaryDirectory(prefix="exp002-negative-") as scratch:
            candidate = Path(scratch) / "mutated-evidence.json"
            candidate.write_bytes(raw)
            replacement_digest = hashlib.sha256(raw).hexdigest()
            if rehash:
                # Simulate a deliberately self-consistent rewrite: this must
                # fail a semantic assertion rather than the hash comparison.
                with patch.object(verifier, "EXPECTED_SHA256", replacement_digest):
                    with self.assertRaisesRegex(
                        verifier.EvidenceError, expected_error
                    ):
                        verifier.verify(candidate)
            else:
                with self.assertRaisesRegex(
                    verifier.EvidenceError, expected_error
                ):
                    verifier.verify(candidate)

    def test_unmodified_evidence_accepted(self):
        digest, count, means, differences, criterion = verifier.verify()
        self.assertEqual(digest, verifier.EXPECTED_SHA256)
        self.assertEqual(count, 30000)
        self.assertEqual(means["ucb1"], 66.9)
        self.assertTrue(criterion)

    def test_modified_bytes_rejected_by_digest(self):
        self.check_mutation(self.original + b"\n", "SHA-256 mismatch", rehash=False)

    def test_reward_corruption_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.parsed)
        record = obj["results"][0]["records"][0]
        record["reward"] = 1 - record["reward"]
        self.check_mutation(
            json.dumps(obj).encode(), "incorrect reward", rehash=True
        )

    def test_wrong_arm_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.parsed)
        record = obj["results"][0]["records"][0]
        record["arm"] = (
            "high" if record["arm"] != "high" else "low"
        )
        self.check_mutation(
            json.dumps(obj).encode(), "incorrect arm", rehash=True
        )

    def test_false_total_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.parsed)
        obj["results"][0]["total_reward"] += 1
        self.check_mutation(
            json.dumps(obj).encode(), "total reward mismatch", rehash=True
        )

    def test_duplicate_seed_policy_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.parsed)
        obj["results"][1]["seed"] = obj["results"][0]["seed"]
        obj["results"][1]["policy"] = obj["results"][0]["policy"]
        self.check_mutation(
            json.dumps(obj).encode(), "duplicate seed-policy pair", rehash=True
        )

    def test_falsified_mean_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.parsed)
        obj["means"]["ucb1"] += 1
        self.check_mutation(
            json.dumps(obj).encode(), "incorrect mean", rehash=True
        )

    def test_falsified_criterion_rejected_even_if_rehashed(self):
        obj = copy.deepcopy(self.parsed)
        obj["criterion_met"] = not obj["criterion_met"]
        self.check_mutation(
            json.dumps(obj).encode(), "criterion mismatch", rehash=True
        )

    def test_duplicate_json_keys_rejected_even_if_rehashed(self):
        raw = self.original.replace(
            b"{\n", b'{\n  "experiment": "EXP002",\n', 1
        )
        self.assertNotEqual(raw, self.original)
        self.check_mutation(raw, "duplicate JSON key", rehash=True)

    def test_nonstandard_nan_rejected_even_if_rehashed(self):
        raw = self.original.replace(
            b'"criterion_met": true',
            b'"criterion_met": NaN',
            1,
        )
        self.assertNotEqual(raw, self.original)
        self.check_mutation(raw, "nonstandard JSON numeric constant", rehash=True)


if __name__ == "__main__":
    unittest.main()
