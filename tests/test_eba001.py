"""EBA-001 deterministic controls for simulated provenance boundaries.

No real attacker code, subprocesses, external files or network requests.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def open_module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner=open_module("eba_engine","src/origin/eba001.py")
replay=open_module("eba_verifier","tools/verify_eba001.py")
p0=open_module("p0_original","tools/verify_exp003_p0.py")


class RecordedScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=runner.study()

    def test_frozen_scenario_roster(self):
        self.assertEqual([x["id"] for x in self.report["scenarios"]],
                         [f"E{x}" for x in range(10)])

    def test_clean_and_illicit_transcripts_both_replay(self):
        for name in ("clean_greedy","oracle_informed"):
            item=self.report["transcripts"][name]
            p0.verify(runner.canonical(item["data"]),item["sha256"])

    def test_oracle_access_invalid_despite_valid_math(self):
        item=self.report["scenarios"][2]
        self.assertEqual(item["methodology_disposition"],
                         "INVALID_OBSERVED_ORACLE_LEAK")
        self.assertTrue(item["synthetic_true_oracle_access"])

    def test_clean_positive_within_fixture(self):
        item=self.report["scenarios"][1]
        self.assertEqual(item["methodology_disposition"],
                         "CLEAN_WITHIN_DECLARED_FIXTURE")
        self.assertFalse(item["telemetry_enforced_by_os"])

    def test_missing_receipts_remain_unknown(self):
        for i in (3,8):
            self.assertEqual(self.report["scenarios"][i]["methodology_disposition"],
                             "UNOBSERVABLE_ACCESS_PROVENANCE")

    def test_deliberately_forged_complete_log_fools_classifier(self):
        item=self.report["scenarios"][9]
        self.assertEqual(item["methodology_disposition"],
                         "CLEAN_WITHIN_DECLARED_FIXTURE")
        self.assertTrue(item["false_clean_attestation"])
        self.assertTrue(item["synthetic_true_oracle_access"])

    def test_context_schema_rejects_extra_fields(self):
        for i in (4,5):
            self.assertEqual(self.report["scenarios"][i]["methodology_disposition"],
                             "INVALID_PROPOSER_CONTEXT")

    def test_wrong_evaluator_id_is_separate(self):
        self.assertEqual(self.report["scenarios"][6]["methodology_disposition"],
                         "INVALID_EVALUATOR_IDENTITY")

    def test_self_resealed_claim_is_not_provenance(self):
        self.assertEqual(self.report["scenarios"][7]["methodology_disposition"],
                         "NOT_ESTABLISHED_SELF_ATTESTED_INTEGRITY")

    def test_seed_hidden_from_honest_context(self):
        sample=runner.public_context(("even","bit1"),[],0)
        self.assertEqual(set(sample),set(runner.CONTEXT_KEYS))
        self.assertNotIn("truth",sample)
        self.assertNotIn("task_seed",sample)

    def test_reproducible_and_pilot_only(self):
        self.assertEqual(runner.study(),self.report)
        with self.assertRaises(SystemExit):
            runner.main([])

    def test_original_p0_integrity_preserved(self):
        original=(ROOT/runner.ORIGINAL_FILE).read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),runner.ORIGINAL_SHA)

    def test_new_evidence_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,sha=runner.save_fresh(self.report,Path(tmp))
            b,sha2=runner.save_fresh(self.report,Path(tmp))
            self.assertNotEqual(a,b)
            self.assertEqual(sha,sha2)


class ReplayAndTamperingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=runner.study()

    def verify(self,d):
        raw=json.dumps(d,sort_keys=True,allow_nan=False).encode()
        return replay.verify(raw,hashlib.sha256(raw).hexdigest())

    def changed(self,update,expected):
        trial=copy.deepcopy(self.source)
        update(trial)
        with self.assertRaisesRegex(ValueError,expected):
            self.verify(trial)

    def test_independent_positive_replay(self):
        outcome=self.verify(self.source)
        self.assertEqual(outcome["mathematically_valid_external_tasks"],24)
        self.assertEqual(outcome["forged_clean_log_false_positives"],1)

    def test_sha_mismatch(self):
        raw=runner.canonical(self.source)
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            replay.verify(raw,"0"*64)

    def test_changed_oracle_answer_rejected(self):
        self.changed(lambda d:d["transcripts"]["oracle_informed"]["data"]
                     ["results"][0]["records"][0].__setitem__("outcome",99),
                     "replay mismatch")

    def test_changed_methodology_class_rejected(self):
        self.changed(lambda d:d["scenarios"][2].__setitem__(
            "methodology_disposition","CLEAN_WITHIN_DECLARED_FIXTURE"),
            "replay mismatch")

    def test_changed_evaluator_id_rejected(self):
        self.changed(lambda d:d.__setitem__("evaluator_blob_sha1","0"*40),
                     "replay mismatch")

    def test_missing_scenario_rejected(self):
        self.changed(lambda d:d["scenarios"].pop(),
                     "scenario count changed")

    def test_rehashed_output_summary_rejected(self):
        self.changed(lambda d:d["outcome_summary"].__setitem__(
            "known_false_clean",0),"replay mismatch")

    def test_false_os_attestation_rejected(self):
        self.changed(lambda d:d["scenarios"][1].__setitem__(
            "telemetry_enforced_by_os",True),"replay mismatch")

    def test_forged_validation_status_rejected(self):
        self.changed(lambda d:d.__setitem__("evidence_status","VALIDATED"),
                     "false validated")

    def test_duplicate_json_key_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            replay.parse(b'{"a":1,"a":2}')

    def test_nonfinite_json_number_rejected(self):
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            replay.parse(b'{"x":NaN}')


if __name__=="__main__":
    unittest.main()
