"""VSC-003: behavior, cost accounting, oracle separation, falsification tests."""
from __future__ import annotations

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


def load(name,relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


runner=load("vsc003_runner","src/origin/vsc003.py")
checker=load("vsc003_checker","tools/verify_vsc003.py")


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=runner.study(20261033,2,3)

    def test_eleven_policy_arms_registered(self):
        self.assertEqual(len(runner.ARMS),11)
        self.assertEqual(len(set(runner.ARMS)),11)
        for p in ("gold_natural","gold_balanced","gold_error","gold_progress",
                  "checked_natural","checked_balanced","checked_progress",
                  "hybrid_progress","gold_plus_pseudo","gold_replay","pseudo_only"):
            self.assertIn(p,runner.ARMS)

    def test_initialization_and_test_splits_shared(self):
        for record in self.fixture["runs"]:
            starts=[a["history"][0] for a in record["policies"]]
            self.assertTrue(all(starts[0]==item for item in starts))
            self.assertEqual([x["generation"] for x in record["policies"][0]["history"]],
                             [0,1,2,3])

    def test_candidate_pool_complete_and_shared(self):
        for row in self.fixture["runs"]:
            for idx in range(3):
                pools=[a["rounds"][idx]["candidate_pool"] for a in row["policies"]]
                self.assertTrue(all(x==pools[0] for x in pools))
                self.assertEqual([sum(item["band"]==b for item in pools[0])
                                  for b in range(4)],[6]*4)
                self.assertEqual(len({x["id"] for x in pools[0]}),24)

    def test_budget_exact_for_every_generation(self):
        for row in self.fixture["runs"]:
            for arm in row["policies"]:
                for state in arm["history"][1:]:
                    if arm["policy"]=="pseudo_only":
                        self.assertEqual(state["credits_spent"],0)
                        self.assertEqual(state["strong_queries"],0)
                        self.assertEqual(state["weak_queries"],0)
                    else:
                        self.assertEqual(state["credits_spent"],12)
                        self.assertEqual(state["strong_queries"]*6+
                                         state["weak_queries"],12)
                        self.assertEqual(state["credits_unused"],0)
                self.assertEqual(arm["totals"]["shared_reference_labels"],480)

    def test_gold_weak_and_hybrid_query_counts(self):
        for row in self.fixture["runs"]:
            arms={a["policy"]:a for a in row["policies"]}
            for name in ("gold_natural","gold_balanced","gold_error",
                         "gold_progress","gold_plus_pseudo","gold_replay"):
                self.assertEqual(arms[name]["totals"]["strong_queries"],6)
                self.assertEqual(arms[name]["totals"]["weak_queries"],0)
            for name in ("checked_natural","checked_balanced","checked_progress"):
                self.assertEqual(arms[name]["totals"]["weak_queries"],36)
                self.assertEqual(arms[name]["totals"]["strong_queries"],0)
            self.assertEqual(arms["hybrid_progress"]["totals"]["weak_queries"],18)
            self.assertEqual(arms["hybrid_progress"]["totals"]["strong_queries"],3)
            self.assertEqual(arms["pseudo_only"]["totals"]["strong_queries"],0)

    def test_gold_balanced_rotates_band_coverage(self):
        row=self.fixture["runs"][0]
        arm=next(a for a in row["policies"] if a["policy"]=="gold_balanced")
        self.assertEqual([{e["band"] for e in rnd["events"]} for rnd in arm["rounds"]],
                         [{0,2},{1,3},{0,2}])

    def test_checked_balanced_selects_three_per_band(self):
        arm=next(a for a in self.fixture["runs"][0]["policies"]
                 if a["policy"]=="checked_balanced")
        for round_ in arm["rounds"]:
            self.assertEqual([sum(e["band"]==b for e in round_["events"])
                              for b in range(4)],[3,3,3,3])

    def test_signed_progress_discounts_worsening(self):
        weights=runner.weights("checked_progress",[1.,1.,1.,1.],
                               [1.,1.,1.,1.],[2.0,0.4,1.,1.])
        self.assertGreater(weights[1],weights[0])
        self.assertEqual(runner.weights("checked_progress",[1.]*4,
                                        [1.]*4,[2.]*4),
                         runner.weights("gold_natural",[1.]*4,None,None))

    def test_weak_label_never_trained_as_oracle_gold(self):
        for record in self.fixture["runs"]:
            by={a["policy"]:a for a in record["policies"]}
            initial=by["pseudo_only"]["history"][0]["gold_cell_coverage"]
            for name in ("checked_natural","checked_balanced",
                         "checked_progress","pseudo_only"):
                arm=by[name]
                self.assertTrue(all(s["gold_cell_coverage"]==initial
                                    for s in arm["history"]))
                for rnd in arm["rounds"]:
                    for e in rnd["events"]:
                        if e["kind"].startswith("WEAK_"):
                            self.assertEqual(e["training_label"],
                                             e["proposed_label"] if e["weak_boolean"]
                                             else None)
                            self.assertEqual(type(e["evaluator_true_label"]),float)
            self.assertTrue(all(s["accepted_cell_coverage"]>=
                                s["gold_cell_coverage"]
                                for a in record["policies"] for s in a["history"]))

    def test_weak_service_feedback_noise_is_a_real_falsifier(self):
        truly_positive=truly_negative=flips=0
        for record in self.fixture["runs"]:
            for arm in record["policies"]:
                for rnd in arm["rounds"]:
                    for e in rnd["events"]:
                        if e["kind"].startswith("WEAK_"):
                            truly_positive+=bool(e["truth_acceptable"])
                            truly_negative+=not e["truth_acceptable"]
                            flips+=bool(e["feedback_flipped"])
                            self.assertEqual(e["weak_boolean"]!=e["truth_acceptable"],
                                             e["feedback_flipped"])
        self.assertGreater(truly_positive,0)
        self.assertGreater(truly_negative,0)
        self.assertGreater(flips,0)

    def test_weak_positive_and_negative_decisions_are_distinct(self):
        for row in self.fixture["runs"]:
            for arm in row["policies"]:
                for rnd in arm["rounds"]:
                    for e in rnd["events"]:
                        if e["kind"]=="WEAK_ACCEPTED_PSEUDO":
                            self.assertTrue(e["weak_boolean"])
                        if e["kind"]=="WEAK_REFUSED":
                            self.assertFalse(e["weak_boolean"])

    def test_training_compute_ablation_is_counted(self):
        for row in self.fixture["runs"]:
            by={a["policy"]:a for a in row["policies"]}
            self.assertEqual(by["gold_plus_pseudo"]["totals"]["student_updates"],36)
            self.assertEqual(by["gold_replay"]["totals"]["student_updates"],36)
            self.assertEqual(by["gold_replay"]["totals"]["anchor_replays"],30)
            self.assertEqual(by["gold_plus_pseudo"]["totals"]["pseudolabel_updates"],30)
            self.assertEqual(by["pseudo_only"]["totals"]["student_updates"],36)
            self.assertEqual(by["gold_natural"]["totals"]["student_updates"],6)

    def test_rare_and_shifted_outcomes_remain_visible(self):
        for row in self.fixture["runs"]:
            for arm in row["policies"]:
                for point in arm["history"]:
                    for key in ("in_domain_macro_mse","shift_macro_mse",
                                "rare_band_mse","accepted_cell_coverage",
                                "queried_cell_coverage","gold_cell_coverage"):
                        self.assertTrue(math.isfinite(point[key]))
                        self.assertGreaterEqual(point[key],0)
                    self.assertLessEqual(point["accepted_cell_coverage"],1)

    def test_test_set_is_not_used_to_choose_training(self):
        original=runner.study(240,1,2)
        real=runner.fixed_pool
        def altered(seed,key,count,scale=1.0):
            samples=real(seed,key,count,scale)
            if key in ("test","shift"):
                return [[(x,y+13.) for x,y in group] for group in samples]
            return samples
        with patch.object(runner,"fixed_pool",side_effect=altered):
            corrupted=runner.study(240,1,2)
        for a,b in zip(original["runs"][0]["policies"],
                       corrupted["runs"][0]["policies"]):
            self.assertEqual(a["rounds"],b["rounds"])
            self.assertEqual(a["final_weights"],b["final_weights"])
            self.assertNotEqual(a["history"][-1]["shift_macro_mse"],
                                b["history"][-1]["shift_macro_mse"])

    def test_seed_determinism_and_seed_sensitivity(self):
        self.assertEqual(self.fixture,runner.study(20261033,2,3))
        self.assertNotEqual(self.fixture["runs"],runner.study(20261035,2,3)["runs"])

    def test_requires_explicit_pilot(self):
        with self.assertRaises(SystemExit):
            runner.main(["--seeds","2"])

    def test_rejects_invalid_bounds(self):
        for args in ({"first":-1},{"first":True},{"seeds":25},
                     {"seeds":0},{"generations":11},{"generations":0}):
            with self.assertRaises(ValueError):
                runner.study(**args)

    def test_evidence_is_exclusive_write(self):
        with tempfile.TemporaryDirectory() as d:
            a,ha=runner.save_new(self.fixture,Path(d))
            b,hb=runner.save_new(self.fixture,Path(d))
            self.assertNotEqual(a,b)
            self.assertEqual(ha,hb)
            self.assertEqual(hashlib.sha256(a.read_bytes()).hexdigest(),ha)

    def test_status_and_limitations_are_not_claims_of_validation(self):
        self.assertEqual(self.fixture["status"],
                         "PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED")
        self.assertTrue(any("not tested" in x.lower()
                            for x in self.fixture["limitations"]))


class IndependentReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=runner.study(20261033,1,2)

    def do_verify(self,obj):
        raw=json.dumps(obj,sort_keys=True,allow_nan=False).encode()
        return checker.verify(raw,hashlib.sha256(raw).hexdigest())

    def altered(self,fn,description):
        x=copy.deepcopy(self.d)
        fn(x)
        with self.assertRaisesRegex(ValueError,description):
            self.do_verify(x)

    def test_positive_full_independent_reconstruction(self):
        result=self.do_verify(self.d)
        self.assertEqual(result["policy_replays"],11)
        self.assertGreater(result["weak_truth_acceptable"],0)
        self.assertGreater(result["weak_truth_unacceptable"],0)

    def test_digest_mismatch(self):
        raw=json.dumps(self.d).encode()
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            checker.verify(raw+b" ",hashlib.sha256(raw).hexdigest())

    def test_rehashed_forged_boolean_decision(self):
        self.altered(lambda d:d["runs"][0]["policies"][4]["rounds"][0]
                     ["events"][0].__setitem__("weak_boolean",True
                                             if d["runs"][0]["policies"][4]
                                             ["rounds"][0]["events"][0]
                                             ["weak_boolean"] is False else False),
                     "replay mismatch")

    def test_rehashed_gold_answer(self):
        self.altered(lambda d:d["runs"][0]["policies"][0]["rounds"][0]
                     ["events"][0].__setitem__("evaluator_true_label",333.0),
                     "numerical replay mismatch")

    def test_rehashed_forged_expensive_query_cost(self):
        self.altered(lambda d:d["runs"][0]["policies"][0]["history"][1]
                     .__setitem__("credits_spent",7),"replay mismatch")

    def test_rehashed_training_value(self):
        self.altered(lambda d:d["runs"][0]["policies"][4]["rounds"][0]
                     ["events"][0].__setitem__("proposed_label",999.0),
                     "numerical replay mismatch")

    def test_rehashed_false_admission_receipt(self):
        self.altered(lambda d:d["runs"][0]["policies"][4]["totals"]
                     .__setitem__("false_accept",100),"replay mismatch")

    def test_rehashed_selection_weights(self):
        self.altered(lambda d:d["runs"][0]["policies"][6]["rounds"][0]
                     ["weights"].__setitem__(0,0.0),"numerical replay mismatch")

    def test_rehashed_final_rare_band_score(self):
        self.altered(lambda d:d["runs"][0]["policies"][6]["history"][-1]
                     .__setitem__("rare_band_mse",0.0),"numerical replay mismatch")

    def test_rehashed_false_evidence_promotion(self):
        self.altered(lambda d:d["runs"][0]["policies"][4]["history"][-1]
                     .__setitem__("gold_cell_coverage",1.0),
                     "numerical replay mismatch")

    def test_rehashed_aggregate_score(self):
        self.altered(lambda d:d["summary"]["gold_natural"]["curves"]
                     ["in_domain_macro_mse"].__setitem__(-1,0.0),
                     "numerical replay mismatch")

    def test_missing_arm(self):
        self.altered(lambda d:d["runs"][0]["policies"].pop(),
                     "policies missing")

    def test_wrong_status_cannot_claim_validation(self):
        self.altered(lambda d:d.__setitem__("status","VALIDATED"),
                     "false validated")

    def test_missing_safety_limitation(self):
        self.altered(lambda d:d["limitations"].pop(),
                     "length differs")

    def test_forged_constants(self):
        self.altered(lambda d:d["constants"].__setitem__("weak_cost",0),
                     "type differs|replay mismatch")

    def test_duplicate_json_key_rejected(self):
        raw=json.dumps(self.d,sort_keys=True).encode()
        orig=b'{"arms": '
        bad=raw.replace(orig,b'{"protocol": "VSC-003", "arms": ',1)
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            checker.verify(bad,hashlib.sha256(bad).hexdigest())

    def test_nan_json_is_unverifiable(self):
        raw=json.dumps(self.d,sort_keys=True).encode()
        raw=raw.replace(b'"generations": 2',b'"generations": NaN',1)
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            checker.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_boolean_seed_rejected(self):
        self.altered(lambda d:d.__setitem__("seed_base",True),
                     "seed invalid")


if __name__=="__main__":
    unittest.main()
