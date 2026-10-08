import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


engine = load("exp003_engine", "src/origin/exp003.py")
verifier = load("exp003_verifier", "tools/verify_exp003_p0.py")


class TestExp003Verifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = engine.study([0, 1, 2, 3])

    def check(self, obj, message):
        raw = json.dumps(obj, sort_keys=True).encode()
        with self.assertRaisesRegex(ValueError, message):
            verifier.verify(raw, hashlib.sha256(raw).hexdigest())

    def test_accepted_replay(self):
        raw = json.dumps(self.data).encode()
        r = verifier.verify(raw, hashlib.sha256(raw).hexdigest())
        self.assertEqual(r["tasks"], 12)

    def test_modified_hash_rejected(self):
        raw = json.dumps(self.data).encode()
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            verifier.verify(raw + b" ", hashlib.sha256(raw).hexdigest())

    def test_truth_rewrite_even_if_rehashed(self):
        data = copy.deepcopy(self.data)
        r = data["results"][0]
        r["truth"] = next(x for x in r["candidates"] if x != r["truth"])
        self.check(data, "fixture mismatch")

    def test_wrong_probe_even_if_rehashed(self):
        data = copy.deepcopy(self.data)
        row = next(r for r in data["results"] if r["policy"] == "fixed")
        row["records"][0]["probe"] = 31
        self.check(data, "fixed policy mismatch")

    def test_fake_score_even_if_rehashed(self):
        data = copy.deepcopy(self.data)
        data["summary"]["greedy"]["solved_rate"] = -1
        self.check(data, "summary fields mismatch")

    def test_duplicate_keys_even_if_rehashed(self):
        raw = json.dumps(self.data).encode().replace(b"{", b'{"protocol":"EXP003-P0",', 1)
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            verifier.verify(raw, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
