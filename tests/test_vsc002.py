"""VSC-002 positive controls, negatives, leakage and rehashed-evidence mutations."""
import copy
import hashlib
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


engine=load("vsc002_runner","src/origin/vsc002.py")
verify=load("vsc002_checker","tools/verify_vsc002.py")


class VSC002ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=engine.study(20261009,2,3)

    def test_six_plus_strong_controls(self):
        self.assertEqual(len(engine.ARMS),8)
        for p in ("gold_natural","gold_balanced","gold_error",
                  "gold_progress","checked_progress","gold_replay"):
            self.assertIn(p,engine.ARMS)

    def test_all_eight_arms_same_start(self):
        for row in self.data["runs"]:
            start=[arm["history"][0]["id_mse_by_band"] for arm in row["arms"]]
            self.assertTrue(all(x==start[0] for x in start))

    def test_longitudinal_reporting_has_generation_zero(self):
        for row in self.data["runs"]:
            for arm in row["arms"]:
                self.assertEqual([x["generation"] for x in arm["history"]],[0,1,2,3])
                self.assertEqual(len(arm["rounds"]),3)
                self.assertTrue(all(math.isfinite(x["id_macro_mse"])
                                    for x in arm["history"]))

    def test_fixed_oracle_queries_equal_across_nonrecursive_arms(self):
        for row in self.data["runs"]:
            for arm in row["arms"]:
                self.assertEqual(arm["totals"]["new_oracle_queries"],
                                 0 if arm["mode"]=="pseudo_only" else 24)
                self.assertTrue(all(r["new_oracle_queries"]==8
                                    for r in arm["history"][1:])
                                if arm["mode"]!="pseudo_only"
                                else all(r["new_oracle_queries"]==0
                                         for r in arm["history"][1:]))

    def test_gold_natural_replay_and_mixed_same_gold_candidates(self):
        for row in self.data["runs"]:
            by={a["mode"]:a for a in row["arms"]}
            natural=[[(e["id"],e["oracle_label"]) for e in gen["oracle_events"]]
                     for gen in by["gold_natural"]["rounds"]]
            for name in ("mixed_pseudo","gold_replay"):
                counterpart=[[(e["id"],e["oracle_label"]) for e in gen["oracle_events"]]
                             for gen in by[name]["rounds"]]
                self.assertEqual(natural,counterpart)

    def test_balanced_oracle_covers_rare_band(self):
        for row in self.data["runs"]:
            balanced=next(x for x in row["arms"] if x["mode"]=="gold_balanced")
            for g,h in zip(balanced["rounds"],balanced["history"][1:]):
                self.assertEqual(sum(e["band"]==3 for e in g["oracle_events"]),2)
                self.assertAlmostEqual(h["new_trusted_band_entropy"],1.0)
                self.assertEqual(h["selected_rare_fraction"],0.25)

    def test_constrained_pseudolabels_have_no_oracle_calls(self):
        for row in self.data["runs"]:
            rec=next(x for x in row["arms"] if x["mode"]=="pseudo_only")
            self.assertEqual(rec["totals"]["new_oracle_queries"],0)
            self.assertEqual(rec["totals"]["pseudolabel_updates"],3*24)
            self.assertTrue(all(not x["oracle_events"] for x in rec["rounds"]))

    def test_anchor_replay_and_mixed_same_compute_count(self):
        for row in self.data["runs"]:
            by={a["mode"]:a for a in row["arms"]}
            self.assertEqual(by["gold_replay"]["totals"]["updates"],3*24)
            self.assertEqual(by["mixed_pseudo"]["totals"]["updates"],3*24)
            self.assertEqual(by["gold_natural"]["totals"]["updates"],3*8)
            self.assertEqual(by["gold_replay"]["totals"]["replay_updates"],3*16)
            self.assertEqual(by["mixed_pseudo"]["totals"]["pseudolabel_updates"],3*16)

    def test_checked_label_consistency_and_actual_defer(self):
        rejects=0
        for row in self.data["runs"]:
            by={a["mode"]:a for a in row["arms"]}
            checked=by["checked_progress"]
            self.assertEqual(checked["totals"]["pseudolabel_updates"],0)
            for round_ in checked["rounds"]:
                for event in round_["oracle_events"]:
                    allowed=(abs(event["offered_pseudo"]-event["oracle_label"])
                             <=engine.CHECK_TOLERANCE)
                    self.assertEqual(event["accepted"],allowed)
                    rejects+=not allowed
        self.assertGreater(rejects,0)

    def test_signed_progress_does_not_reward_worsening(self):
        weights=engine.curriculum("gold_progress",[1.,1.,1.,1.],
                                  [1.,1.,1.,1.],[3.,0.4,1.,1.])
        self.assertGreater(weights[1],weights[0])
        self.assertEqual(engine.curriculum("gold_progress",[1]*4,
                         [1]*4,[2]*4),list(engine.NATURAL))

    def test_error_strategy_distinct_from_progress(self):
        score=engine.curriculum("gold_error",[1.0,1.0,1.0,6.0],None,None)
        self.assertGreater(score[3],score[0])

    def test_generation_pool_complete_unique(self):
        pool=engine.candidate_pool(123,2)
        self.assertEqual(len(pool),24)
        self.assertEqual({row["id"] for row in pool},set(range(24)))
        self.assertEqual([sum(row["band"]==b for row in pool)
                          for b in range(4)],[6,6,6,6])

    def test_all_outputs_finite_and_diversity_bounded(self):
        for row in self.data["runs"]:
            for arm in row["arms"]:
                for entry in arm["history"]:
                    for field in ("id_macro_mse","shift_macro_mse",
                                  "rare_band_mse","trusted_cell_coverage"):
                        self.assertTrue(math.isfinite(entry[field]))
                        self.assertGreaterEqual(entry[field],0)
                    self.assertLessEqual(entry["trusted_cell_coverage"],1.0)

    def test_policy_does_not_see_shifted_test_labels(self):
        baseline=engine.study(619,1,2)
        fn=engine.trusted_pool
        def manipulated(seed,name,n,outer=1.0):
            xs=fn(seed,name,n,outer)
            if name in ("id_test","shift_test"):
                return [[(x,y+13.0) for x,y in group] for group in xs]
            return xs
        with patch.object(engine,"trusted_pool",side_effect=manipulated):
            changed=engine.study(619,1,2)
        for a,b in zip(baseline["runs"][0]["arms"],changed["runs"][0]["arms"]):
            self.assertEqual(a["rounds"],b["rounds"])
            self.assertEqual(a["weights_final"],b["weights_final"])
            self.assertNotEqual(a["history"][-1]["shift_macro_mse"],
                                b["history"][-1]["shift_macro_mse"])

    def test_reproducible_and_seed_sensitive(self):
        self.assertEqual(self.data,engine.study(20261009,2,3))
        self.assertNotEqual(self.data["runs"],engine.study(20261011,2,3)["runs"])

    def test_no_run_without_explicit_pilot(self):
        with self.assertRaises(SystemExit):
            engine.main(["--seeds","1"])

    def test_seed_and_generation_bounds(self):
        for kwargs in ({"n_seeds":25},{"n_generations":13},{"seed_base":-2},
                       {"n_generations":0}):
            with self.assertRaises(ValueError):
                engine.study(**kwargs)

    def test_append_only_file_creation(self):
        with tempfile.TemporaryDirectory() as d:
            a,ha=engine.save_fresh(self.data,Path(d))
            b,hb=engine.save_fresh(self.data,Path(d))
            self.assertNotEqual(a,b)
            self.assertEqual(ha,hb)
            self.assertEqual(hashlib.sha256(a.read_bytes()).hexdigest(),ha)

    def test_evidence_not_promoted_to_confirmation(self):
        self.assertEqual(self.data["evidence_status"],
                         "PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED")
        self.assertTrue(any("no security isolation" in x.lower()
                            for x in self.data["limitations"]))


class VSC002VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=engine.study(444,1,2)

    def roundtrip(self,document):
        raw=json.dumps(document,sort_keys=True,allow_nan=False).encode()
        return verify.check(raw,hashlib.sha256(raw).hexdigest())

    def mutate(self,callback,expected):
        d=copy.deepcopy(self.data)
        callback(d)
        with self.assertRaisesRegex(ValueError,expected):
            self.roundtrip(d)

    def test_independent_replay(self):
        result=self.roundtrip(self.data)
        self.assertEqual(result["policy_seed_replays"],8)
        self.assertEqual(result["generational_checkpoints"],24)

    def test_digest_mismatch_rejected(self):
        raw=json.dumps(self.data).encode()
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            verify.check(raw+b" ",hashlib.sha256(raw).hexdigest())

    def test_forged_oracle_label_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][0]["rounds"][0]
                    ["oracle_events"][0].__setitem__("oracle_label",-999),
                    "replay mismatch")

    def test_forged_pseudolabel_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][6]["rounds"][0]
                    ["replay_events"][0].__setitem__("label",0),
                    "replay mismatch")

    def test_forged_candidate_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][0]["rounds"][0]
                    ["candidate_pool"][0].__setitem__("x",0.88),
                    "replay mismatch")

    def test_forged_heldout_curve_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][0]["history"][1]
                    .__setitem__("shift_macro_mse",0.0),
                    "replay mismatch")

    def test_forged_oracle_cost_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][3]["totals"]
                    .__setitem__("new_oracle_queries",0),
                    "value differs")

    def test_forged_diversity_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][1]["history"][2]
                    .__setitem__("trusted_cell_coverage",0.0),
                    "replay mismatch")

    def test_forged_rejected_event_rehashed(self):
        def forge(d):
            for gen in d["runs"][0]["arms"][4]["rounds"]:
                for e in gen["oracle_events"]:
                    if not e["accepted"]:
                        e["accepted"]=True
                        return
            d["runs"][0]["arms"][4]["rounds"][0]["oracle_events"][0]["accepted"]=False
        self.mutate(forge,"value differs")

    def test_forged_final_score_rehashed(self):
        self.mutate(lambda d:d["summary"]["gold_progress"]["curves"]
                    ["id_macro_mse"].__setitem__(2,-1.0),
                    "numerical replay mismatch")

    def test_reordered_arms_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"].reverse(),"value differs")

    def test_missing_history_rehashed(self):
        self.mutate(lambda d:d["runs"][0]["arms"][0]["history"].pop(),
                    "length differs")

    def test_fake_confirmatory_status(self):
        self.mutate(lambda d:d.__setitem__("evidence_status","VALIDATED"),
                    "false validation")

    def test_missing_privilege_limitation(self):
        self.mutate(lambda d:d["limitations"].pop(1),"length differs")

    def test_fake_seed_count(self):
        self.mutate(lambda d:d.__setitem__("seeds",2),"run count wrong")

    def test_duplicate_json_key(self):
        raw=json.dumps(self.data).encode()
        tampered=raw.replace(b'{"protocol":',b'{"protocol": "VSC-002", "protocol":',1)
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            verify.check(tampered,hashlib.sha256(tampered).hexdigest())

    def test_nonfinite_json(self):
        raw=json.dumps(self.data,sort_keys=True).encode()
        tampered=raw.replace(b'"generations": 2',b'"generations": NaN',1)
        with self.assertRaisesRegex(ValueError,"nonfinite JSON"):
            verify.check(tampered,hashlib.sha256(tampered).hexdigest())

    def test_boolean_budget_rejected(self):
        self.mutate(lambda d:d.__setitem__("generations",True),
                    "generation count invalid")


if __name__=="__main__":
    unittest.main()
