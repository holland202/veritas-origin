"""Positive and adversarial controls for P1's offline exchange contract.

No model is executed, no network or subprocess is used and no secret is
exposed to a tool. These do not demonstrate OS sandboxing.
"""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


p1 = load("engine_offline_fixture", "src/origin/exp003_p1.py")
ex = load("offline_exchange", "src/origin/p1_offline_exchange.py")
SECRET = "0123456789abcdef" * 4
RID = "a" * 32


class TestOfflineExchange(unittest.TestCase):
    def setUp(self):
        self.task = p1.make_task(SECRET, 3)
        self.request = ex.issue_request(self.task, [], 3_000_000_000, request_id=RID)
        self.probe = self.request["available_probes"][0]

    def reply(self, probe=None, **kw):
        data = {"request_id": RID,
                "request_sha256": ex.request_digest(self.request),
                "probe": self.probe if probe is None else probe}
        data.update(kw)
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def admission(self, raw=None, request=None, spent=None, now=10_000):
        return ex.admit_proposal(self.request if request is None else request,
                                 self.reply() if raw is None else raw,
                                 now_unix=now,
                                 spent_request_ids=set() if spent is None else spent)

    def test_good_proposal_admitted_only(self):
        outcome = self.admission()
        self.assertEqual(outcome["verdict"], "ADMISSIBLE_PROPOSAL_ONLY")
        self.assertEqual(outcome["probe"], self.probe)
        self.assertEqual(outcome["request_sha256"], ex.request_digest(self.request))

    def test_oracle_seed_and_truth_not_sent_in_wire_message(self):
        raw = ex.canonical_bytes(self.request)
        for field in (b'"truth"', b'"task_index"', b'"secret"',
                      b'"evaluator_secret_hex"', b'"seed"', b'"capabilities"'):
            self.assertNotIn(field, raw)
        self.assertNotIn(SECRET.encode("ascii"), raw)
        self.assertEqual(len(self.request["matrix"]), 16)
        self.assertEqual(len(self.request["matrix"][0]), 24)

    def test_evaluator_state_kept_separate(self):
        p = 4
        observed = self.task["matrix"][p1.HYPOTHESES.index(self.task["truth"])][p]
        req = ex.issue_request(self.task, [{"probe": p, "outcome": observed}],
                               3_000_000_000, request_id="b" * 32)
        self.assertEqual(req["observations"], [{"probe": p, "outcome": observed}])
        self.assertNotIn(p, req["available_probes"])
        self.assertNotIn("truth", req)
        self.assertEqual(req["remaining_budget"], 4)

    def test_repeat_probe_rejected(self):
        req = copy.deepcopy(self.request)
        req["available_probes"].remove(self.probe)
        with self.assertRaisesRegex(ex.ProposalRejected, "AVAILABLE_PROBES_MISMATCH"):
            ex.admit_proposal(req, self.reply(), 1000, set())

    def test_expired_request_rejected(self):
        with self.assertRaisesRegex(ex.ProposalRejected, "EXPIRED_REQUEST"):
            self.admission(now=3_000_000_000)

    def test_replay_set_rejected(self):
        with self.assertRaisesRegex(ex.ProposalRejected, "REQUEST_ALREADY_SPENT"):
            self.admission(spent={RID})

    def test_missing_spent_state_rejected(self):
        with self.assertRaisesRegex(ex.ProposalRejected, "SPENT_STATE_MISSING"):
            ex.admit_proposal(self.request, self.reply(), 1000, None)

    def test_cross_request_rejected(self):
        with self.assertRaisesRegex(ex.ProposalRejected, "CROSS_REQUEST_RESPONSE"):
            self.admission(raw=self.reply(request_id="f" * 32))

    def test_wrong_request_digest_rejected(self):
        with self.assertRaisesRegex(ex.ProposalRejected, "REQUEST_DIGEST_MISMATCH"):
            self.admission(raw=self.reply(request_sha256="f" * 64))

    def test_boolean_probe_rejected(self):
        with self.assertRaisesRegex(ex.ProposalRejected, "INVALID_PROBE"):
            self.admission(raw=self.reply(probe=True))

    def test_duplicate_json_key_rejected(self):
        raw = self.reply().replace(b'{"probe":', b'{"probe": 1, "probe":', 1)
        with self.assertRaisesRegex(ex.ProposalRejected, "DUPLICATE_JSON_KEY"):
            self.admission(raw=raw)

    def test_nonfinite_json_rejected(self):
        raw = self.reply().replace(b'"probe": 0', b'"probe": NaN')
        with self.assertRaisesRegex(ex.ProposalRejected, "NONFINITE_JSON"):
            self.admission(raw=raw)

    def test_arbitrary_command_field_rejected(self):
        raw = self.reply(shell="rm -rf /", permission="ALLOW")
        with self.assertRaisesRegex(ex.ProposalRejected, "RESPONSE_SCHEMA"):
            self.admission(raw=raw)

    def test_response_too_large_rejected(self):
        raw = self.reply() + b"x" * 1024
        with self.assertRaisesRegex(ex.ProposalRejected, "RESPONSE_SIZE"):
            self.admission(raw=raw)

    def test_contradictory_observations_rejected(self):
        # A single probe cannot both be 0 and 1; separate probes can contradict all
        # hypotheses. Exercise input validation using an impossible used-probe state.
        with self.assertRaisesRegex(ex.ProposalRejected, "OBSERVATION_PROBE_INVALID"):
            ex.issue_request(self.task, [{"probe": 0, "outcome": 0},
                                         {"probe": 0, "outcome": 1}],
                             3_000_000_000, request_id=RID)

    def test_request_unknown_field_rejected(self):
        forged = copy.deepcopy(self.request)
        forged["truth"] = self.task["truth"]
        with self.assertRaisesRegex(ex.ProposalRejected, "INVALID_REQUEST_SCHEMA"):
            self.admission(request=forged)

    def test_candidate_state_forgery_rejected(self):
        forged = copy.deepcopy(self.request)
        forged["candidate_names"] = ["H00"]
        with self.assertRaisesRegex(ex.ProposalRejected, "CANDIDATE_STATE_MISMATCH"):
            self.admission(request=forged)

    def test_implicit_execution_never_happens(self):
        self.assertFalse(hasattr(ex, "execute"))
        self.assertFalse(hasattr(ex, "run_model"))
        result = self.admission()
        self.assertNotIn("executed", result)
        self.assertNotIn("allow", result)

    def test_insufficient_budget_rejected(self):
        forged = copy.deepcopy(self.request)
        forged["remaining_budget"] = 0
        with self.assertRaisesRegex(ex.ProposalRejected, "BUDGET_OR_ALREADY_SOLVED"):
            self.admission(request=forged)


if __name__ == "__main__":
    unittest.main()
