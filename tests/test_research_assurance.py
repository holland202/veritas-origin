"""RA-001 positive, adversarial and SV Gate integration tests.

Historical originals are NEVER changed; faults run in temporary directories
or in-memory JSON. The SV integration tests use a pinned EXTERNAL checkout,
not a copy or reimplementation of its MIT Gate.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name, ROOT / path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assurance=load("ra001_assurance","tools/research_assurance.py")
bridge=load("ra001_sv_bridge","tools/sv_research_bridge.py")


class ArchiveAssuranceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected=assurance.audit(ROOT)
        cls.raw=assurance.protected_bytes(ROOT, assurance.EXP003_PATH)
        cls.doc=assurance.strict_json(cls.raw)
        cls.ledger=assurance.strict_json(
            assurance.protected_bytes(ROOT,assurance.LEDGER_PATH)
        )

    def replica(self):
        context=tempfile.TemporaryDirectory()
        temporary=Path(context.name)
        for relative in assurance.PINNED:
            origin=ROOT/relative
            target=temporary/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(origin,target)
        return context,temporary

    def test_baseline_passes_bounded_positive_control(self):
        self.assertEqual(self.expected["verdict"],"ARCHIVE_CONSISTENT_ONLY")
        self.assertEqual(self.expected["pilot_evaluations"],36)
        self.assertEqual(self.expected["pilot_probes"],86)
        self.assertEqual(self.expected["archive_files_pinned"],len(assurance.PINNED))
        self.assertEqual(self.expected["human_publication_approval"],"NOT_GRANTED")

    def test_exact_independent_sha_for_archives(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(),
                         assurance.EXP003_SHA256)
        self.assertEqual(assurance.git_blob_sha1(self.raw),
                         assurance.PINNED[assurance.EXP003_PATH][0])

    def test_archive_evidence_byte_mutation(self):
        temp,root=self.replica()
        try:
            target=root/assurance.EXP003_PATH
            raw=target.read_bytes()
            target.write_bytes(raw.replace(b'"EXP003-P0"',b'"EXP003-XX"',1))
            with self.assertRaisesRegex(ValueError,"Git blob mismatch"):
                assurance.audit(root)
        finally:
            temp.cleanup()

    def test_manifest_resealing_cannot_change_compiled_pin(self):
        temp,root=self.replica()
        try:
            target=root/assurance.LEDGER_PATH
            raw=target.read_bytes()
            data=assurance.strict_json(raw)
            data["evidence_sha256"]=hashlib.sha256(b"fabricated").hexdigest()
            target.write_text(json.dumps(data,sort_keys=True))
            with self.assertRaisesRegex(ValueError,"Git blob mismatch"):
                assurance.audit(root)
        finally:
            temp.cleanup()

    def test_missing_historical_artifact(self):
        temp,root=self.replica()
        try:
            (root/assurance.PILOT_PATH).unlink()
            with self.assertRaisesRegex(ValueError,"missing historical"):
                assurance.audit(root)
        finally:
            temp.cleanup()

    def test_frozen_protocol_or_code_change(self):
        for name in ("experiments/exp003/PROTOCOL_P0.md",
                     "src/origin/exp003.py","tools/verify_exp003_p0.py"):
            with self.subTest(path=name):
                temp,root=self.replica()
                try:
                    target=root/name
                    target.write_bytes(target.read_bytes()+b"\n# RETROACTIVE TAMPER\n")
                    with self.assertRaisesRegex(ValueError,"Git blob mismatch"):
                        assurance.verify_archive(root)
                finally:
                    temp.cleanup()

    def test_report_change(self):
        temp,root=self.replica()
        try:
            target=root/"reports/exp003/EXP003_P0_AZURE_PILOT.md"
            target.write_bytes(target.read_bytes().replace(
                b"2.0000",b"0.0000",1))
            with self.assertRaisesRegex(ValueError,"Git blob mismatch"):
                assurance.audit(root)
        finally:
            temp.cleanup()

    def test_symlinked_archive_is_refused(self):
        temp,root=self.replica()
        try:
            filepath=root/assurance.EXP003_PATH
            other=filepath.parent/"replaced.json"
            filepath.rename(other)
            filepath.symlink_to(other.name)
            with self.assertRaisesRegex(ValueError,"symlink refused"):
                assurance.verify_archive(root)
        finally:
            temp.cleanup()

    def test_unregistered_path_does_not_escape_root(self):
        with self.assertRaisesRegex(ValueError,"unregistered historical path"):
            assurance.protected_bytes(ROOT,"../../etc/passwd")

    def test_missing_policy_record(self):
        payload=copy.deepcopy(self.doc)
        payload["results"].pop()
        with self.assertRaisesRegex(ValueError,"inventory incomplete"):
            assurance.rebuild_p0_summary(payload)

    def test_falsified_probe_count(self):
        payload=copy.deepcopy(self.doc)
        payload["results"][0]["records"].pop()
        with self.assertRaisesRegex(ValueError,"probe totals changed"):
            assurance.rebuild_p0_summary(payload)

    def test_falsified_completion_claim(self):
        counts=assurance.rebuild_p0_summary(self.doc)
        forged=copy.deepcopy(self.ledger)
        claim=next(c for c in forged["claims"] if c["id"]=="EXP003-P0-C01")
        claim["numerator_by_policy"]["greedy"]=11
        with self.assertRaisesRegex(ValueError,"false completion claim"):
            assurance.verify_claim_ledger(forged,counts)

    def test_falsified_ledger_counts(self):
        counts=assurance.rebuild_p0_summary(self.doc)
        forged=copy.deepcopy(self.ledger)
        claim=next(c for c in forged["claims"] if c["id"]=="EXP003-P0-C02")
        claim["total_probes_by_policy"]["greedy"]=0
        with self.assertRaisesRegex(ValueError,"false probe-count claim"):
            assurance.verify_claim_ledger(forged,counts)

    def test_false_confirmatory_promotion(self):
        counts=assurance.rebuild_p0_summary(self.doc)
        forged=copy.deepcopy(self.ledger)
        claim=next(c for c in forged["claims"] if c["id"]=="EXP003-P0-C02")
        claim["timing"]="CONFIRMATORY_PREREGISTERED"
        with self.assertRaisesRegex(ValueError,"improperly promoted"):
            assurance.verify_claim_ledger(forged,counts)

    def test_claim_cannot_self_approve(self):
        counts=assurance.rebuild_p0_summary(self.doc)
        forged=copy.deepcopy(self.ledger)
        forged["approval_state"]="APPROVED"
        with self.assertRaisesRegex(ValueError,"cannot grant publication"):
            assurance.verify_claim_ledger(forged,counts)

    def test_fake_model_evaluation_prohibited(self):
        counts=assurance.rebuild_p0_summary(self.doc)
        forged=copy.deepcopy(self.ledger)
        claim=next(c for c in forged["claims"] if c["id"]=="EXP003-P0-C04")
        claim["external_model_evaluated"]=True
        with self.assertRaisesRegex(ValueError,"no external model"):
            assurance.verify_claim_ledger(forged,counts)

    def test_duplicate_json_key_rejected(self):
        raw=b'{"a":1,"a":2}'
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            assurance.strict_json(raw)

    def test_nonfinite_json_rejected(self):
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            assurance.strict_json(b'{"mean":NaN}')

    def test_ledger_is_original_git_blob(self):
        raw=assurance.protected_bytes(ROOT,assurance.LEDGER_PATH)
        self.assertEqual(assurance.git_blob_sha1(raw),
                         assurance.PINNED[assurance.LEDGER_PATH][0])


class SovereignBridgeTests(unittest.TestCase):
    def test_default_bridge_has_no_authority(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C01")
        self.assertEqual(packet["capability"]["authorized"],False)
        self.assertEqual(packet["record"]["verification"]["status"],
                         "INSUFFICIENT_EVIDENCE")
        self.assertEqual(packet["record"]["metadata"]["human_approval_verified"],
                         False)
        self.assertEqual(packet["runtime"]["thermal_status"],"unknown")

    def test_unknown_claim_cannot_be_published(self):
        with self.assertRaisesRegex(ValueError,"claim id missing"):
            bridge.bridge_intent(ROOT,"SYNTHETIC_APPROVED_CLAIM")

    def test_bridge_has_explicit_restricted_action(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C02")
        self.assertEqual(packet["policy"],{"allow_only":["publish_research_claim"]})
        self.assertEqual(packet["record"]["action"]["requested"],
                         "publish_research_claim")
        self.assertNotIn("credentials",json.dumps(packet).lower())


class PinnedActualSovereignVeritasGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        target=os.environ.get("SV_REPO_PATH")
        if not target:
            raise unittest.SkipTest("External SV source not available; CI fetch required")
        external=Path(target).resolve()
        if not (external/"sovereign_veritas/decision.py").is_file():
            raise AssertionError("SV_REPO_PATH was set but source missing")
        sys.path.insert(0,str(external))
        from sovereign_veritas.decision import Gate
        from sovereign_veritas.evidence import EvidenceRecord
        from sovereign_veritas.capability import Capability
        from sovereign_veritas.runtime import RuntimeState
        cls.Gate=Gate
        cls.EvidenceRecord=EvidenceRecord
        cls.Capability=Capability
        cls.RuntimeState=RuntimeState

    def decision(self,packet):
        rec=packet["record"]
        cap=packet["capability"]
        rt=packet["runtime"]
        evidence=self.EvidenceRecord(
            record_id="RA001_SYNTHETIC_GATE_TEST",
            input_digest=rec["input_digest"],
            verification=rec["verification"],
            action=rec["action"],
            metadata=rec["metadata"],
            evidence_quality=rec["evidence_quality"],
        )
        capability=self.Capability(
            name=cap["name"],
            authorized=cap["authorized"],
            required_evidence=tuple(cap["required_evidence"]),
            parent=cap["parent"],
            min_evidence_quality=cap["min_evidence_quality"],
            max_steps=cap["max_steps"],
        )
        runtime=self.RuntimeState(
            platform="synthetic-ci-fixture",
            python_version="3.12",
            thermal_status=rt["thermal_status"],
            compute_budget=rt["compute_budget"],
            power_status=rt["power_status"],
        )
        return self.Gate().evaluate(evidence,capability,runtime,
                                    policy=packet["policy"])

    def test_actual_gate_refuses_auto_promotion(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C03")
        decision=self.decision(packet)
        self.assertEqual(decision.decision,"REFUSE")
        self.assertIn("capability_not_authorized",decision.reasons)

    def test_actual_gate_refuses_failed_verifier(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C03")
        packet["record"]["verification"]["status"]="FAIL"
        decision=self.decision(packet)
        self.assertEqual(decision.decision,"REFUSE")
        self.assertIn("verification_not_passed",decision.reasons)

    def test_synthetic_authority_still_defers_missing_research_review(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C03")
        packet["capability"]["authorized"]=True  # SYNTHETIC ONLY
        packet["runtime"].update(thermal_status="cool",compute_budget="available",
                                 power_status="stable")
        result=self.decision(packet)
        self.assertEqual(result.decision,"DEFER")
        self.assertIn("verification_insufficient_evidence",result.reasons)
        self.assertIn("missing_required_evidence:human_approval_verified",
                      result.reasons)

    def test_synthetic_string_approval_does_not_count(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C03")
        packet["capability"]["authorized"]=True  # SYNTHETIC ONLY
        packet["record"]["verification"]["status"]="PASS" # SYNTHETIC ONLY
        packet["runtime"].update(thermal_status="cool",compute_budget="available",
                                 power_status="stable")
        packet["record"]["metadata"].update({
            key:True for key in bridge.EVIDENCE_FIELDS
        })
        packet["record"]["metadata"]["human_approval_verified"]="true"
        result=self.decision(packet)
        self.assertEqual(result.decision,"DEFER")
        self.assertIn("missing_required_evidence:human_approval_verified",
                      result.reasons)

    def test_synthetic_all_allow_reachable_not_real_approval(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C03")
        packet["capability"]["authorized"]=True  # SYNTHETIC ONLY
        packet["record"]["verification"]["status"]="PASS" # SYNTHETIC ONLY
        packet["runtime"].update(thermal_status="cool",compute_budget="available",
                                 power_status="stable")
        packet["record"]["metadata"].update({
            key:True for key in bridge.EVIDENCE_FIELDS  # NOT authenticated
        })
        result=self.decision(packet)
        self.assertEqual(result.decision,"ALLOW")
        self.assertEqual(result.reasons,())

    def test_synthetic_permission_cannot_publish_unlisted_action(self):
        packet=bridge.bridge_intent(ROOT,"EXP003-P0-C03")
        packet["capability"]["authorized"]=True
        packet["record"]["verification"]["status"]="PASS"
        packet["runtime"].update(thermal_status="cool",compute_budget="available",
                                 power_status="stable")
        packet["record"]["metadata"].update({key:True for key in bridge.EVIDENCE_FIELDS})
        packet["record"]["action"]["requested"]="deploy_model"
        self.assertEqual(self.decision(packet).decision,"REFUSE")


if __name__=="__main__":
    unittest.main()
