"""ASP-001 positive, negative and rehashed-forgery tests. NumPy only."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
import numpy as np
BASE=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,BASE/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

study=load("asp001_producer","src/origin/asp001.py")
replayer=load("asp001_verifier","tools/verify_asp001.py")

class NetworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture=study.run([20330101],8)

    def test_actual_network_and_trainable_parameters(self):
        weights,batches,grid=study.make_seed(20330101,8)
        self.assertEqual(weights.shape,(49,))
        self.assertEqual(study.predict(weights,grid).shape,(129,1))
        altered=weights.copy();altered[:16]+=.1
        self.assertFalse(np.array_equal(study.predict(weights,grid),
                                        study.predict(altered,grid)))

    def test_gradient_is_real_chain_rule(self):
        parameters,data,_=study.make_seed(20330101,8)
        x,y=data[0][0][0],data[0][1][0]
        loss,gradient=study.backprop(parameters,x,y)
        self.assertGreater(loss,0)
        for i in (0,12,16,31,32,47,48):
            plus=parameters.copy();plus[i]+=1e-5
            minus=parameters.copy();minus[i]-=1e-5
            approx=(study.backprop(plus,x,y)[0]-
                    study.backprop(minus,x,y)[0])/(2e-5)
            self.assertAlmostEqual(approx,gradient[i],delta=1e-8)

    def test_six_arm_roster_is_frozen(self):
        self.assertEqual(study.ARMS,(
            "sgd_001","sgd_003","sgd_009","scheduled_sgd","adam_001","regulated_sgd"
        ))

    def test_equivalent_label_and_update_budget(self):
        for a in self.fixture["runs"][0]["arms"]:
            self.assertEqual(a["update_count"],24)
            self.assertEqual(a["label_exposures"],384)
            self.assertEqual(len(a["steps"]),24)

    def test_every_arm_starts_same_but_changes_weights(self):
        rows=self.fixture["runs"][0]["arms"]
        self.assertTrue(all(a["checkpoints"][0]==rows[0]["checkpoints"][0]
                            for a in rows))
        self.assertTrue(all(a["checkpoints"][0]["parameters"]!=a["final_parameters"]
                            for a in rows))

    def test_b_labels_are_corrupted_and_A_is_clean(self):
        _,dataset,_=study.make_seed(20330101,8)
        self.assertFalse(np.any(dataset[0][2]))
        self.assertTrue(np.any(dataset[1][2]))
        self.assertFalse(np.any(dataset[2][2]))

    def test_validation_grid_fixed_and_never_train_on_grid(self):
        _,batches,grid=study.make_seed(20330101,8)
        self.assertEqual(len(grid),129)
        self.assertEqual(grid[0,0],-1)
        self.assertEqual(grid[-1,0],1)
        self.assertEqual(batches[0][0].shape,(8,16,1))

    def test_real_regulator_changes_learning_rate(self):
        arm=self.fixture["runs"][0]["arms"][-1]
        self.assertGreater(arm["modulator_nonunit_steps"],0)
        self.assertGreaterEqual(arm["modulator_min"],.35)
        self.assertLessEqual(arm["modulator_max"],1.4)
        self.assertEqual(arm["steps"][0]["modulator"],1.)

    def test_const_modulation_SGD_ablation(self):
        arm=self.fixture["runs"][0]["arms"][1]
        self.assertTrue(all(p["modulator"]==1 and p["learning_rate"]==.03
                            for p in arm["steps"]))

    def test_adam_strong_control_included(self):
        arm=self.fixture["runs"][0]["arms"][4]
        self.assertTrue(all(p["learning_rate"]==.01 for p in arm["steps"]))

    def test_regulator_cannot_lookup_task_id_or_heldout_scores(self):
        import ast
        t=ast.parse((BASE/"src/origin/asp001.py").read_text())
        impl=next(n for n in t.body if isinstance(n,ast.FunctionDef)
                  and n.name=="train_arm")
        text=ast.unparse(impl)
        self.assertNotIn("a_function(",text)
        self.assertNotIn("b_function(",text)
        self.assertNotIn("eval_grid[",text)

    def test_deterministic_across_runs(self):
        self.assertEqual(self.fixture,study.run([20330101],8))
        other=study.run([20330102],8)
        self.assertNotEqual(self.fixture["runs"][0]["training_inputs_sha256"],
                            other["runs"][0]["training_inputs_sha256"])

    def test_all_outcomes_retained_if_negative(self):
        self.assertIn(self.fixture["summary"]["H1"],(
            "H1_NOT_SUPPORTED_IN_THIS_FIXTURE",
            "H1_EXPLORATORY_CRITERION_MET_NOT_VALIDATED"
        ))
        self.assertEqual(len(self.fixture["summary"]["paired_comparisons"]),5)

    def test_no_implicit_run(self):
        with self.assertRaises(SystemExit):study.main([])

    def test_invalid_counts_fail_closed(self):
        for steps in (0,65,False,1.2):
            with self.assertRaises(ValueError):study.run([20330101],steps)

    def test_exclusive_evidence_files(self):
        with tempfile.TemporaryDirectory() as location:
            first,a=study.save_new(self.fixture,Path(location))
            second,b=study.save_new(self.fixture,Path(location))
            self.assertNotEqual(first,second)
            self.assertEqual(a,b)
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(),a)

class IndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture=study.run([20330101],8)
    def check(self,doc):
        raw=json.dumps(doc,sort_keys=True,allow_nan=False).encode()
        return replayer.verify(raw,hashlib.sha256(raw).hexdigest())
    def corrupt(self,callback,why):
        doc=copy.deepcopy(self.fixture)
        callback(doc)
        with self.assertRaisesRegex(ValueError,why):self.check(doc)

    def test_positive_replay(self):
        result=self.check(self.fixture)
        self.assertEqual(result["verdict"],
                         "INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY")

    def test_changed_raw_sha(self):
        raw=json.dumps(self.fixture).encode()
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            replayer.verify(raw+b" ",hashlib.sha256(raw).hexdigest())

    def test_rehashed_forged_loss(self):
        self.corrupt(lambda d:d["runs"][0]["arms"][0]["steps"][0].__setitem__(
            "loss",-1.),"numeric replay mismatch")

    def test_rehashed_heldout_error(self):
        self.corrupt(lambda d:d["runs"][0]["arms"][4]["checkpoints"][2].__setitem__(
            "B_mse",0.),"numeric replay mismatch")

    def test_rehashed_forged_gain(self):
        self.corrupt(lambda d:d["runs"][0]["arms"][5]["steps"][1].__setitem__(
            "modulator",10.),"numeric replay mismatch")

    def test_rehashed_wrong_exposure(self):
        self.corrupt(lambda d:d["runs"][0]["arms"][5].__setitem__(
            "label_exposures",4),"replay mismatch")

    def test_rehashed_changed_model_weights(self):
        self.corrupt(lambda d:d["runs"][0]["arms"][2]["final_parameters"].__setitem__(
            0,999.),"numeric replay mismatch")

    def test_changed_checkpoint_digest(self):
        self.corrupt(lambda d:d["runs"][0]["arms"][3]["checkpoints"][2][
            "parameters"].__setitem__(0,100.),"checkpoint parameter digest mismatch")

    def test_rehashed_data_stream(self):
        self.corrupt(lambda d:d["runs"][0].__setitem__(
            "training_inputs_sha256","0"*64),"replay mismatch")

    def test_rehashed_false_H1(self):
        self.corrupt(lambda d:d["summary"].__setitem__("H1","VALIDATED"),
                     "replay mismatch")

    def test_extra_arm_refused(self):
        self.corrupt(lambda d:d["arms"].append("oracle_control"),"length mismatch")

    def test_missing_seed(self):
        self.corrupt(lambda d:d["runs"].pop(),"missing runs")

    def test_false_validated_status(self):
        self.corrupt(lambda d:d.__setitem__("status","VALIDATED"),
                     "false validation status")

    def test_duplicate_json_keys(self):
        raw=b'{"a":1,"a":2}'
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            replayer.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_nonfinite_json(self):
        raw=b'{"x":Infinity}'
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            replayer.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_wrong_public_seed_not_permitted(self):
        self.corrupt(lambda d:d.__setitem__("seeds",[20330102]),
                     "outside preregistration")

if __name__=="__main__":unittest.main()
