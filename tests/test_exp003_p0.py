import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "src/origin/exp003.py"
spec = importlib.util.spec_from_file_location("origin_exp003_p0", MODULE)
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


class TestEXP003P0(unittest.TestCase):
    def test_replay_deterministic(self):
        self.assertEqual(exp.study([0, 1]), exp.study([0, 1]))

    def test_shared_tasks_and_truth(self):
        data = exp.study([0, 1, 2])
        for seed in [0, 1, 2]:
            rows = [r for r in data["results"] if r["seed"] == seed]
            self.assertEqual(len(rows), 3)
            self.assertEqual(len({tuple(r["candidates"]) for r in rows}), 1)
            self.assertEqual(len({r["truth"] for r in rows}), 1)

    def test_observation_and_elimination(self):
        for record in exp.study(list(range(12)))["results"]:
            active = tuple(record["candidates"])
            used = set()
            self.assertIn(record["truth"], active)
            for i, row in enumerate(record["records"]):
                self.assertEqual(row["step"], i)
                self.assertEqual(row["pre"], list(active))
                self.assertNotIn(row["probe"], used)
                self.assertIn(row["probe"], exp.DOMAIN)
                self.assertEqual(row["outcome"], exp.REGISTRY[record["truth"]](row["probe"]))
                active = tuple(h for h in active if exp.REGISTRY[h](row["probe"]) == row["outcome"])
                self.assertEqual(row["post"], list(active))
                used.add(row["probe"])
            self.assertEqual(list(active), record["remaining"])
            self.assertEqual(record["solved"], len(active) == 1)
            self.assertLessEqual(len(record["records"]), 6)

    def test_greedy_partition_value(self):
        candidates = ("even", "lowhalf", "bit1", "multiple3")
        possible = [exp.reduction(candidates, x) for x in exp.DOMAIN]
        best = exp.choose_greedy(candidates, set())
        self.assertEqual(exp.reduction(candidates, best), max(possible))
        self.assertEqual(best, next(i for i, s in enumerate(possible) if s == max(possible)))

    def test_invalid_policy_refused(self):
        with self.assertRaises(ValueError):
            exp.study([1], ("invented",))

    def test_duplicate_seed_refused(self):
        with self.assertRaises(ValueError):
            exp.study([1, 1])

    def test_external_invalid_proposal_deferred(self):
        with tempfile.TemporaryDirectory() as d:
            proposer = Path(d) / "bad.py"
            proposer.write_text('print("{\\"probe\\":true}")\n')
            result = exp.evaluate(1, "external", [__import__("sys").executable, str(proposer)])
            self.assertEqual(result["status"], "DEFERRED")
            self.assertEqual(result["records"], [])

    def test_external_valid_proposals(self):
        with tempfile.TemporaryDirectory() as d:
            proposer = Path(d) / "good.py"
            proposer.write_text("import json,sys\nd=json.load(sys.stdin)\nprint(json.dumps({'probe':next(x for x in d['domain'] if x not in [r['probe'] for r in d['observations']])}))\n")
            result = exp.evaluate(2, "external", [__import__("sys").executable, str(proposer)])
            self.assertEqual(result["status"], "COMPLETE")
            self.assertGreaterEqual(len(result["records"]), 1)

    def test_external_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            proposer = Path(d) / "dup.py"
            proposer.write_text('print(\'{"probe":0,"probe":1}\')\n')
            result = exp.evaluate(3, "external", [__import__("sys").executable, str(proposer)])
            self.assertEqual(result["status"], "DEFERRED")

    def test_fresh_write_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            data = exp.study([0])
            a, ha = exp.save_fresh(data, Path(d))
            b, hb = exp.save_fresh(data, Path(d))
            self.assertNotEqual(a, b)
            self.assertEqual(ha, hb)
            self.assertEqual(json.loads(a.read_text()), data)


if __name__ == "__main__":
    unittest.main()
