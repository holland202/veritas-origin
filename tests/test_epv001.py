"""EPV-001 adversarial synthetic truth-report, anchor, and false clean controls."""
from __future__ import annotations
import copy,hashlib,importlib.util,json,random,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def module(name,path):
    obj=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(obj)
    obj.loader.exec_module(mod)
    return mod

lab=module("epv001_runner","src/origin/epv001.py")
checker=module("epv001_replay","tools/verify_epv001.py")

class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.record=lab.run()

    def test_all_registered_cases_and_trials(self):
        self.assertEqual(len(self.record["trial_records"]),3072)
        self.assertEqual(self.record["seeds"],list(range(260801,260809)))
        self.assertEqual(len(self.record["summary"]),6)

    def test_four_reports_for_all_cases(self):
        self.assertTrue(all(len(row["reports"])==4
                            for row in self.record["trial_records"]))

    def test_world_truth_not_policy_argument(self):
        import ast
        code=ast.parse((ROOT/"src/origin/epv001.py").read_text())
        f=next(x for x in code.body if isinstance(x,ast.FunctionDef) and
               x.name=="decide")
        self.assertEqual([x.arg for x in f.args.args],["trial","policy"])
        source=ast.unparse(f)
        self.assertNotIn('trial["world_truth"]',source)

    def test_unique_report_id_and_valid_claim(self):
        for row in self.record["trial_records"]:
            self.assertEqual(len({x["id"] for x in row["reports"]}),4)
            self.assertTrue(all(type(x["claim"]) is int and x["claim"] in (0,1)
                                for x in row["reports"]))

    def test_all_situations_have_both_truth_labels(self):
        for case in lab.CASES:
            candidates={r["world_truth"] for r in self.record["trial_records"]
                        if r["case"]==case}
            self.assertEqual(candidates,{0,1})

    def test_control_nonvacuous_majority(self):
        p=self.record["summary"]["INDEPENDENT_LIAR"]
        self.assertEqual(p["majority"]["correct"],512)
        self.assertEqual(p["evidence_first"]["correct"],512)

    def test_naive_majority_launders_correlated_duplicates(self):
        p=self.record["summary"]["CORRELATED_FALSE_MAJORI"]
        self.assertEqual(p["majority"]["incorrect"],512)
        self.assertEqual(p["lineage"]["abstained"],512)
        self.assertEqual(p["evidence_first"]["correct"],512)

    def test_unverified_dissent_stays_unknown(self):
        p=self.record["summary"]["CORRELATED_UNPROVEN_DISSENT"]
        self.assertEqual(p["evidence_first"]["abstained"],512)
        self.assertIsNone(p["evidence_first"]["error_per_accepted"])

    def test_forged_attestation_does_not_override_anchor(self):
        p=self.record["summary"]["FORGED_DISSENT_PROOF"]
        self.assertEqual(p["claimed_certificate"]["incorrect"],512)
        self.assertEqual(p["evidence_first"]["correct"],512)

    def test_broken_reference_produces_known_false_positive(self):
        p=self.record["summary"]["POISONED_AUTHORITY"]
        self.assertEqual(p["evidence_first"]["incorrect"],512)
        self.assertTrue(self.record["registered_controls"][
            "poisoned_authority_false_positive_preserved"])

    def test_mutually_certified_conflict_abstained(self):
        p=self.record["summary"]["CONFLICTING_AUTHORITIES"]
        self.assertEqual(p["evidence_first"]["abstained"],512)

    def test_same_seed_rerun_is_identical(self):
        self.assertEqual(self.record,lab.run())

    def test_never_auto_runs_without_optin(self):
        with self.assertRaises(SystemExit):lab.main([])

    def test_new_files_exclusive_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            a,h1=lab.write_once(self.record,Path(folder))
            b,h2=lab.write_once(self.record,Path(folder))
            self.assertNotEqual(a,b)
            self.assertEqual(h1,h2)

    def test_all_outputs_are_legitimate_decisions(self):
        for row in self.record["trial_records"]:
            self.assertEqual(set(row["decisions"]),set(lab.POLICIES))
            self.assertTrue(all(val in (0,1,lab.ABSTAIN)
                                for val in row["decisions"].values()))

class IndependentReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.source=lab.run()

    def validate(self,record):
        raw=json.dumps(record,sort_keys=True,allow_nan=False).encode()
        return checker.verify(raw,hashlib.sha256(raw).hexdigest())

    def mutation(self,change,expect):
        edited=copy.deepcopy(self.source)
        change(edited)
        with self.assertRaisesRegex(ValueError,expect):
            self.validate(edited)

    def test_positive_full_semantic_replay(self):
        result=self.validate(self.source)
        self.assertEqual(result["trials"],3072)
        self.assertEqual(result["critical_known_false_positive"],512)

    def test_original_sha_mismatch(self):
        raw=json.dumps(self.source).encode()
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            checker.verify(raw,"0"*64)

    def test_rehashed_wrong_binary_world(self):
        self.mutation(lambda x:x["trial_records"][0].__setitem__("world_truth",2),
                      "mismatch")

    def test_rehashed_forged_report_claim(self):
        self.mutation(lambda x:x["trial_records"][0]["reports"][0].__setitem__(
            "claim",2),"mismatch")

    def test_rehashed_changed_trust_anchor(self):
        self.mutation(lambda x:x["trial_records"][64]["trusted_anchors"].__setitem__(
            "s3","0"*64),"mismatch")

    def test_rehashed_false_positive_hidden(self):
        self.mutation(lambda x:x["summary"]["POISONED_AUTHORITY"][
            "evidence_first"].__setitem__("incorrect",0),"mismatch")

    def test_rehashed_abstention_promoted(self):
        self.mutation(lambda x:x["trial_records"][0]["decisions"].__setitem__(
            "evidence_first",lab.ABSTAIN),"mismatch")

    def test_rehashed_missing_trial(self):
        self.mutation(lambda x:x["trial_records"].pop(),"missing trial inventory")

    def test_rehashed_fake_validation(self):
        self.mutation(lambda x:x.__setitem__("status","VALIDATED"),"mismatch")

    def test_duplicate_json_key_detected(self):
        raw=b'{"x":0,"x":1}'
        with self.assertRaisesRegex(ValueError,"duplicate JSON keys"):
            checker.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_nonfinite_json_numeric_detected(self):
        raw=b'{"x":NaN}'
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            checker.verify(raw,hashlib.sha256(raw).hexdigest())

    def test_independent_replayer_never_imports_runner(self):
        import ast
        tree=ast.parse((ROOT/"tools/verify_epv001.py").read_text())
        names=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names.extend(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom):names.append(node.module or "")
        self.assertNotIn("epv001",names)
        self.assertNotIn("src.origin.epv001",names)

if __name__=="__main__":unittest.main()
