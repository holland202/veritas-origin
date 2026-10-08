"""C1-001 positive, adversarial, and replay-mutation tests.

OS-boundary enforcement is a separate required LIVE Linux test in GitHub CI:
these pure unit tests cannot establish DAC or peer credential enforcement.
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

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

evaluator=load("c1001_evaluator","experiments/c1001/evaluator.py")
proposer=load("c1001_proposer","experiments/c1001/proposer.py")
replayer=load("c1001_independent","tools/verify_c1001.py")

def synthetic_receipt():
    session=evaluator.Session()
    session.peer_denials=1 # UNIT fixture only, NOT OS-measured.
    welcome=session.react(b'{"op":"HELLO"}')
    assert welcome["status"]=="PUBLIC_CONTEXT"
    for bad in (
        {"op":"GET_SECRET"},{"op":"READ_FILE"},
        {"op":"PROBE","probe":True},
        {"op":"PROBE","probe":-1},
        {"op":"PROBE","probe":0,"approval":True},
        {"op":"HELLO","truth":"forged"},
    ):
        assert session.react(evaluator.canonical(bad))=={"error":"SCHEMA_DENIED"}
    view=welcome["context"]
    while not view["solved"] and view["remaining_budget"]>0:
        selected=proposer.greedy(view["candidate_names"],view["observations"])
        response=session.react(evaluator.canonical({"op":"PROBE","probe":selected}))
        assert response["status"]=="PROBE_OK"
        view=response["context"]
        if len(view["observations"])==1:
            assert session.react(evaluator.canonical({"op":"PROBE","probe":selected}))=={
                "error":"DUPLICATE_PROBE"}
    assert view["solved"]
    assert session.protocol_denials>=7
    return session,session.receipt(32001,32002)

class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session,cls.receipt=synthetic_receipt()

    def test_positive_task_reachable_not_all_deny(self):
        self.assertTrue(self.receipt["solved"])
        self.assertGreater(len(self.receipt["events"]),0)
        self.assertLessEqual(len(self.receipt["events"]),6)

    def test_proposer_view_excludes_hidden_fields(self):
        view=self.session.public_view()
        for key in ("truth","salt","secret","task_seed","private_path"):
            self.assertNotIn(key,view)
        self.assertEqual(view["commitment_sha256"],self.session.commitment)

    def test_salted_nonce_not_public_seed(self):
        self.assertEqual(len(bytes.fromhex(self.receipt["trial"]["salt"])),32)
        self.assertEqual(len(bytes.fromhex(self.receipt["trial"]["trial_id"])),16)
        self.assertNotEqual(self.session.commitment,evaluator.Session().commitment)

    def test_unauthorized_action_refused(self):
        self.assertEqual(self.session.react(b'{"op":"GET_SECRET"}'),
                         {"error":"SCHEMA_DENIED"})

    def test_forbidden_extra_fields_refused(self):
        self.assertEqual(self.session.react(
            b'{"op":"PROBE","probe":2,"approval":true}'),{"error":"SCHEMA_DENIED"})

    def test_boolean_noninteger_out_of_bounds_refused(self):
        for raw in (b'{"op":"PROBE","probe":true}',b'{"op":"PROBE","probe":-5}',
                    b'{"op":"PROBE","probe":32}',b'{"op":"PROBE","probe":2.0}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.session.react(raw),{"error":"SCHEMA_DENIED"})

    def test_duplicate_json_keys_refused(self):
        self.assertEqual(self.session.react(
            b'{"op":"HELLO","op":"HELLO"}'),{"error":"SCHEMA_DENIED"})

    def test_nan_refused(self):
        self.assertEqual(self.session.react(
            b'{"op":"PROBE","probe":NaN}'),{"error":"SCHEMA_DENIED"})

    def test_message_size_bounded(self):
        with self.assertRaisesRegex(ValueError,"too large"):
            evaluator.parse_request(b"x"*2050)

    def test_proposer_algorithm_not_given_hidden_truth(self):
        names=self.session.public_view()["candidate_names"]
        self.assertIs(type(proposer.greedy(names,[])),int)

    def test_peer_denial_distinct_from_protocol_denial(self):
        self.assertGreater(self.receipt["peer_denials"],0)
        self.assertGreater(self.receipt["protocol_denials"],0)
        self.assertFalse(self.receipt["os_controls"]["full_process_isolation"])

    def test_fs_enforcement_fails_on_bad_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            pri=Path(folder)/"private"
            pub=Path(folder)/"public"
            pri.mkdir(mode=0o700)
            pub.mkdir(mode=0o770)
            with self.assertRaisesRegex(RuntimeError,"UID/GID"):
                evaluator.enforce_fs(pri,pub,100000,200000)

    def test_independent_replayer_no_evaluator_import(self):
        s=(ROOT/"tools/verify_c1001.py").read_text()
        self.assertNotIn("import evaluator",s)
        self.assertNotIn("from experiments.c1001",s)

    def test_absence_of_external_model_or_power_claims(self):
        self.assertIn("NOT_SANDBOXED",self.receipt["scope"])
        self.assertFalse(self.receipt["os_controls"]["network_egress_blocked"])

class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=synthetic_receipt()[1]

    def validate(self,record):
        b=json.dumps(record,sort_keys=True,allow_nan=False).encode()
        return replayer.verify(b,hashlib.sha256(b).hexdigest())

    def changed(self,modifier,reason):
        doc=copy.deepcopy(self.original)
        modifier(doc)
        with self.assertRaisesRegex(ValueError,reason):
            self.validate(doc)

    def test_positive_replay_and_narrow_scope(self):
        d=self.validate(self.original)
        self.assertTrue(d["solved"])
        self.assertEqual(d["secure_sandbox"],"NOT_ESTABLISHED")

    def test_byte_change_rejected(self):
        b=json.dumps(self.original).encode()
        with self.assertRaisesRegex(ValueError,"SHA256 mismatch"):
            replayer.verify(b+b" ",hashlib.sha256(b).hexdigest())

    def test_changed_math_outcome_rejected(self):
        self.changed(lambda d:d["events"][0].__setitem__("outcome",3),
                     "oracle outcome mismatch")

    def test_changed_truth_rejected(self):
        missing=next(n for n in evaluator.NAMES if n not in self.original["trial"]["candidates"])
        self.changed(lambda d:d["trial"].__setitem__("truth",missing),
                     "hidden truth invalid")

    def test_forged_salted_commitment_rejected(self):
        self.changed(lambda d:d["trial"].__setitem__("commitment_sha256","0"*64),
                     "salted commitment mismatch")

    def test_wrong_salt_rejected(self):
        self.changed(lambda d:d["trial"].__setitem__("salt","0"*64),
                     "salted commitment mismatch")

    def test_wrong_evaluator_uid_rejected(self):
        self.changed(lambda d:d.__setitem__("evaluator_euid",32002),
                     "unexpected identities")

    def test_forged_full_sandbox_rejected(self):
        self.changed(lambda d:d["os_controls"].__setitem__(
            "full_process_isolation",True),"unsupported sandbox")

    def test_missing_denial_evidence_rejected(self):
        self.changed(lambda d:d.__setitem__("peer_denials",0),
                     "no unauthorized peer")

    def test_false_self_attestation_rejected(self):
        self.changed(lambda d:d.__setitem__("untrusted_proposer_access_log","CLEAN"),
                     "attempted promotion")

    def test_missing_history_rejected(self):
        self.changed(lambda d:d.__setitem__("events",[]),"nonvacuous")

    def test_duplicate_probe_rejected(self):
        def repeat(d):
            d["events"].insert(1,copy.deepcopy(d["events"][0]))
            d["events"][1]["step"]=1
        self.changed(repeat,"probe domain/duplicate violation|invalid prior-state")

    def test_no_upgrade_to_validated(self):
        self.changed(lambda d:d.__setitem__("scope","FULLY_VALIDATED"),"invalid scope")

    def test_duplicate_json_key_rejected(self):
        b=b'{"scope":1,"scope":2}'
        with self.assertRaisesRegex(ValueError,"duplicate JSON key"):
            replayer.verify(b,hashlib.sha256(b).hexdigest())

    def test_nonfinite_json_rejected(self):
        b=b'{"x":Infinity}'
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            replayer.verify(b,hashlib.sha256(b).hexdigest())

if __name__=="__main__":
    unittest.main()
