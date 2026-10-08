"""Adversarial tests for prior-art register integrity and narrow claims."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prior_art_gate", ROOT / "tools/check_prior_art.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

with (ROOT / "research/prior_art_register.json").open(encoding="utf-8") as f:
    ORIGINAL = json.load(f)


class TestPriorArtGate(unittest.TestCase):
    def mutated(self):
        return copy.deepcopy(ORIGINAL)

    def rejected(self, obj, text):
        with self.assertRaisesRegex(ValueError, text):
            gate.check(obj)

    def test_valid_initial_register(self):
        r = gate.check(ORIGINAL)
        self.assertEqual(r["copy_authorizations"], 0)
        self.assertEqual(r["novelty_claims"], 0)
        self.assertGreaterEqual(r["records"], 17)

    def test_missing_source_revision_rejected(self):
        obj = self.mutated()
        obj["records"][0]["pinned_revision"] = "main"
        self.rejected(obj, "not commit-pinned")

    def test_source_url_revision_mismatch_rejected(self):
        obj = self.mutated()
        obj["records"][0]["source_url"] = obj["records"][0]["source_url"].replace(
            obj["records"][0]["pinned_revision"], "f"*40
        )
        self.rejected(obj, "permalink")

    def test_license_approval_without_a_reference_rejected(self):
        obj = self.mutated()
        src = next(r for r in obj["records"] if r["id"] == "PA-014")
        src["license"]["identifier"] = "MIT"
        src["license"]["status"] = "VERIFIED_ROOT_LICENSE"
        self.rejected(obj, "verified license URL")

    def test_code_copied_without_authorization_rejected(self):
        obj = self.mutated()
        obj["records"][0]["source_code_copied"] = True
        self.rejected(obj, "source reuse")

    def test_novelty_from_search_rejected(self):
        obj = self.mutated()
        obj["records"][0]["novelty"] = "PROVEN_NOVEL"
        self.rejected(obj, "novelty")

    def test_missing_attribution_flag_rejected(self):
        obj = self.mutated()
        obj["records"][0]["attribution_required_in_design"] = False
        self.rejected(obj, "attribution")

    def test_duplicate_id_rejected(self):
        obj = self.mutated()
        obj["records"][1]["id"] = obj["records"][0]["id"]
        self.rejected(obj, "duplicate prior art record ID")

    def test_missing_component_category_rejected(self):
        obj = self.mutated()
        obj["records"] = [r for r in obj["records"] if r["component"] != "model_routing"]
        self.rejected(obj, "missing component coverage")

    def test_missing_reason_rejected(self):
        obj = self.mutated()
        obj["records"][0]["prior_art_overlap"] = ""
        self.rejected(obj, "reason missing")

    def test_duplicate_json_key_rejected(self):
        raw = json.dumps(ORIGINAL)
        modified = raw.replace('{"schema_version":', '{"schema_version": "wrong", "schema_version":', 1)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            gate.validate(modified)

    def test_nan_rejected(self):
        raw = json.dumps(ORIGINAL)
        modified = raw.replace('"policy":', '"extra": NaN, "policy":', 1)
        with self.assertRaisesRegex(ValueError, "nonfinite JSON"):
            gate.validate(modified)

    def test_unrecognized_source_code_use_rejected(self):
        obj = self.mutated()
        obj["records"][0]["proposed_use"] = "COPY"
        self.rejected(obj, "source reuse")

    def test_missing_full_register_rejected(self):
        obj = self.mutated()
        obj["records"] = []
        self.rejected(obj, "too few")

    def test_duplicate_root_fields_rejected(self):
        raw = json.dumps(ORIGINAL)
        tamper = raw.replace('{"schema_version":', '{"schema_version": "bogus", "schema_version":', 1)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            gate.validate(tamper)


if __name__ == "__main__":
    unittest.main()
