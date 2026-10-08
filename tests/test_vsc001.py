"""Behavioral and adversarial regression tests for VSC-001 toy simulation."""
import copy
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def mod(label,path):
    spec=importlib.util.spec_from_file_location(label,ROOT/path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


engine=mod("vsc_engine","src/origin/vsc001.py")
verifier=mod("vsc_standalone","tools/verify_vsc001.py")


class VSC001BehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=engine.study(101,2,3,12,public_test_seed=True)

    def test_registered_six_controls(self):
        self.assertEqual(len(engine.MODES),6)
        self.assertIn("oracle_balanced",engine.MODES)
        self.assertIn("verified_natural",engine.MODES)
        self.assertIn("verified_progress",engine.MODES)
        self.assertIn("recursive_natural",engine.MODES)

    def test_reproducible_different_seeds(self):
        self.assertEqual(self.doc,engine.study(101,2,3,12,public_test_seed=True))
        self.assertNotEqual(self.doc["runs"],engine.study(103,2,3,12)["runs"])

    def test_independent_calibration_and_test_streams(self):
        p=engine.pool(5,"initial",8)
        q=engine.pool(5,"selection",8)
        r=engine.pool(5,"conformal",8)
        s=engine.pool(5,"test",8)
        self.assertNotEqual(p,q)
        self.assertNotEqual(q,r)
        self.assertNotEqual(r,s)

    def test_per_arm_identical_seed_model(self):
        for row in self.doc["runs"]:
            initial=[a["initial_test_mse_by_band"] for a in row["arms"]]
            self.assertTrue(all(x==initial[0] for x in initial))

    def test_candidate_streams_shared_for_uniform_policy_arms(self):
        row=self.doc["runs"][0]["arms"]
        streams={}
        for arm in row:
            streams[arm["mode"]]=[(e["band"],e["x"]) for e in arm["events"]]
        baseline=streams["oracle_natural"]
        for mode in ("noisy_natural","verified_natural","recursive_natural"):
            self.assertEqual(baseline,streams[mode])
        self.assertNotEqual(baseline,streams["oracle_balanced"])

    def test_all_policy_events_bounded(self):
        for row in self.doc["runs"]:
            for arm in row["arms"]:
                self.assertEqual(len(arm["events"]),36)
                self.assertEqual(arm["accepted"]+arm["rejected"],36)
                self.assertEqual(len(arm["history"]),3)
                self.assertTrue(math.isfinite(arm["final_test_macro_mse"]))
                self.assertTrue(all(v>=0 for v in arm["final_test_mse_by_band"]))

    def test_verified_never_trains_intentionally_corrupted_sample(self):
        for row in self.doc["runs"]:
            for arm in row["arms"]:
                if arm["mode"].startswith("verified_"):
                    self.assertEqual(arm["false_labels_admitted"],0)
                    self.assertEqual(arm["rejected"],
                                     sum(x["injected"] for x in arm["events"]))
                    self.assertTrue(all(not e["accepted"] for e in arm["events"]
                                        if e["injected"]))

    def test_unverified_includes_faulty_labels(self):
        row=self.doc["runs"][0]
        noisy=next(a for a in row["arms"] if a["mode"]=="noisy_natural")
        verified=next(a for a in row["arms"] if a["mode"]=="verified_natural")
        self.assertEqual(noisy["false_labels_admitted"],verified["rejected"])
        self.assertGreater(noisy["false_labels_admitted"],0)

    def test_verified_oracle_cost_explicit(self):
        for row in self.doc["runs"]:
            for arm in row["arms"]:
                count=len(arm["events"])
                expected=32+(2*count if arm["mode"].startswith("verified_")
                             else 0 if arm["mode"]=="recursive_natural" else count)
                self.assertEqual(arm["train_oracle_calls"],expected)

    def test_recursive_never_gets_training_oracle_label(self):
        rec=next(a for a in self.doc["runs"][0]["arms"]
                 if a["mode"]=="recursive_natural")
        self.assertTrue(all(e["reference"] is None
                            and e["oracle_calls"]==0 for e in rec["events"]))

    def test_progress_allocation_is_signed_decrease(self):
        prior=[1.,1.,1.,1.]
        later=[1.5,0.5,1.5,1.5]
        a=engine.progress_weights(prior,later)
        self.assertGreater(a[1],0.6)
        self.assertAlmostEqual(sum(a),1.)
        self.assertEqual(engine.progress_weights(prior,[2.]*4),
                         list(engine.NATURAL))

    def test_worsening_band_no_positive_progress(self):
        prior=[1.,1.,1.,1.]
        now=[0.8,1.6,1.,1.]
        weights=engine.progress_weights(prior,now)
        self.assertGreater(weights[0],weights[1])

    def test_final_heldout_does_not_choose_curriculum(self):
        original_pool=engine.pool
        def changed_only_final(seed,domain,n):
            out=original_pool(seed,domain,n)
            if domain=="test":
                return [[(x,y+9) for x,y in group] for group in out]
            return out
        base=engine.study(321,1,2,4)
        with patch.object(engine,"pool",side_effect=changed_only_final):
            changed=engine.study(321,1,2,4)
        for a,b in zip(base["runs"][0]["arms"],changed["runs"][0]["arms"]):
            self.assertEqual(a["events"],b["events"])
            self.assertEqual(a["history"],b["history"])
            self.assertNotEqual(a["final_test_macro_mse"],b["final_test_macro_mse"])

    def test_conformal_range_no_guarantee_claim(self):
        for row in self.doc["runs"]:
            for arm in row["arms"]:
                for c in arm["conformal_by_band"]:
                    self.assertTrue(0<=c["coverage"]<=1)
                    self.assertGreaterEqual(c["width"],0)
                    self.assertTrue(math.isfinite(c["q"]))

    def test_no_implicit_run(self):
        with self.assertRaises(SystemExit):
            engine.main(["--seeds","1"])
        with self.assertRaises(SystemExit):
            engine.main(["--pilot","--test-seed-base","4"])

    def test_study_limits(self):
        with self.assertRaises(ValueError):
            engine.study(0,n_seeds=9)
        with self.assertRaises(ValueError):
            engine.study(0,rounds=0)
        with self.assertRaises(ValueError):
            engine.study(0,candidates_per_round=51)
        with self.assertRaises(ValueError):
            engine.study(-5)

    def test_exclusive_evidence_writer(self):
        with tempfile.TemporaryDirectory() as d:
            a,h=engine.save_new(self.doc,Path(d))
            b,k=engine.save_new(self.doc,Path(d))
            self.assertNotEqual(a,b)
            self.assertEqual(h,k)
            self.assertEqual(hashlib.sha256(a.read_bytes()).hexdigest(),h)

    def test_status_is_only_simulated(self):
        self.assertEqual(self.doc["status"],"EXPLORATORY_SIMULATED_NOT_VALIDATED")
        self.assertEqual(self.doc["seed_origin"],"PUBLIC_TEST_SEED")
        self.assertTrue(any("oracle" in x.lower() for x in self.doc["limitations"]))


class VSC001VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=engine.study(109,1,2,8,public_test_seed=True)

    def inspect(self,doc):
        raw=json.dumps(doc,sort_keys=True,allow_nan=False).encode()
        return verifier.verify(raw,hashlib.sha256(raw).hexdigest())

    def rejected(self,doc,reason):
        with self.assertRaisesRegex(ValueError,reason):
            self.inspect(doc)

    def test_independent_verifier_passes(self):
        report=self.inspect(self.doc)
        self.assertEqual(report["arms_replayed"],6)
        self.assertEqual(report["candidate_events"],96)

    def test_original_bytes_digest(self):
        raw=json.dumps(self.doc).encode()
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            verifier.verify(raw+b" ",hashlib.sha256(raw).hexdigest())

    def test_rehashed_modified_teacher_label(self):
        x=copy.deepcopy(self.doc)
        x["runs"][0]["arms"][2]["events"][0]["reference"]+=0.5
        self.rejected(x,"replay mismatch")

    def test_rehashed_forged_accepted_corruption(self):
        x=copy.deepcopy(self.doc)
        arm=next(a for a in x["runs"][0]["arms"] if a["mode"]=="verified_natural")
        corrupt=next(i for i,e in enumerate(arm["events"]) if e["injected"])
        arm["events"][corrupt]["accepted"]=True
        self.rejected(x,"replay mismatch")

    def test_rehashed_fake_oracle_budget(self):
        x=copy.deepcopy(self.doc)
        x["runs"][0]["arms"][3]["train_oracle_calls"]-=1
        self.rejected(x,"replay mismatch")

    def test_rehashed_fake_heldout_score(self):
        x=copy.deepcopy(self.doc)
        x["runs"][0]["arms"][0]["final_test_macro_mse"]=0.
        self.rejected(x,"replay mismatch")

    def test_rehashed_fake_curriculum_weights(self):
        x=copy.deepcopy(self.doc)
        x["runs"][0]["arms"][4]["history"][1]["weights"]=[0.25]*4
        self.rejected(x,"replay mismatch")

    def test_rehashed_summary_forgery(self):
        x=copy.deepcopy(self.doc)
        x["summary"]["oracle_balanced"]["final_test_macro_mse"]=-42.
        self.rejected(x,"replay mismatch")

    def test_missing_arm(self):
        x=copy.deepcopy(self.doc)
        x["runs"][0]["arms"].pop()
        self.rejected(x,"arms missing")

    def test_status_forgery(self):
        x=copy.deepcopy(self.doc)
        x["status"]="PRODUCTION_VALIDATED"
        self.rejected(x,"invalid status")

    def test_nominal_confidence_forgery(self):
        x=copy.deepcopy(self.doc)
        x["constants"]["nominal_coverage"]=1.
        self.rejected(x,"replay mismatch")

    def test_duplicate_json_keys_rejected(self):
        raw=json.dumps(self.doc,sort_keys=True).encode()
        tampered=raw.replace(b'{"candidates_per_round":',
                             b'{"protocol":"VSC-001","candidates_per_round":',1)
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            verifier.verify(tampered,hashlib.sha256(tampered).hexdigest())

    def test_nonfinite_json_rejected(self):
        raw=json.dumps(self.doc,sort_keys=True).encode()
        raw=raw.replace(b'"n_seeds": 1',b'"n_seeds": NaN',1)
        with self.assertRaisesRegex(ValueError,"nonfinite JSON"):
            verifier.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_boolean_seed_rejected(self):
        x=copy.deepcopy(self.doc)
        x["seed_base"]=True
        self.rejected(x,"seed base invalid")


if __name__=="__main__":
    unittest.main()
