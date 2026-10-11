"""HYP-001: isolated property-testing instrument; no production checker import.

Run: python -m unittest discover -s research/hypothesis_pilot -p 'test_*.py' -v
Optional: python -m pip install hypothesis  # only after dependency approval
Tests are designed to fail if the instrument cannot distinguish its mutant.
"""
import copy
import json
import unittest

def reference(record):
    """Minimal toy evidence boundary, NOT DPC-001."""
    if not isinstance(record, dict) or set(record) != {"id", "evidence", "authorized"}:
        return "REFUSE"
    if not isinstance(record["id"], str) or not record["id"].strip():
        return "REFUSE"
    if not isinstance(record["authorized"], bool):
        return "REFUSE"
    if not isinstance(record["evidence"], list) or not record["evidence"]:
        return "REFUSE"
    if any(not isinstance(x, str) or not x.strip() for x in record["evidence"]):
        return "REFUSE"
    return "ALLOW" if record["authorized"] else "REFUSE"

def mutant(record):
    """Known-bad control: truthiness accepts 'false' and 1 as authorization."""
    if isinstance(record, dict) and record.get("authorized"):
        return "ALLOW"
    return "REFUSE"

class InstrumentControls(unittest.TestCase):
    def test_valid_control(self):
        self.assertEqual(reference({"id": "case-1", "evidence": ["a"], "authorized": True}), "ALLOW")

    def test_negative_control(self):
        self.assertEqual(reference({"id": "case-1", "evidence": ["a"], "authorized": False}), "REFUSE")

    def test_known_bad_mutant_detected(self):
        cases = [
            {"id": "case-1", "evidence": ["a"], "authorized": "false"},
            {"id": "case-1", "evidence": [], "authorized": True},
            {"id": "", "evidence": ["a"], "authorized": True},
        ]
        self.assertTrue(any(reference(c) != mutant(c) for c in cases))

    def test_determinism_and_nonmutation(self):
        c = {"id": "case-1", "evidence": ["a"], "authorized": True}
        before = copy.deepcopy(c)
        self.assertEqual(reference(c), reference(c))
        self.assertEqual(c, before)

try:
    from hypothesis import given, settings, strategies as st
except ImportError:
    HYPOTHESIS_AVAILABLE = False
else:
    HYPOTHESIS_AVAILABLE = True

if HYPOTHESIS_AVAILABLE:
    class HypothesisProperties(unittest.TestCase):
        @settings(max_examples=150, deadline=None, derandomize=True)
        @given(st.dictionaries(st.text(max_size=12), st.one_of(st.none(), st.booleans(), st.integers(), st.text(max_size=12), st.lists(st.text(max_size=12), max_size=4)), max_size=8))
        def test_totality_and_determinism(self, record):
            before = copy.deepcopy(record)
            a = reference(record)
            self.assertIn(a, ("ALLOW", "REFUSE"))
            self.assertEqual(a, reference(record))
            self.assertEqual(record, before)

        @settings(max_examples=100, deadline=None, derandomize=True)
        @given(st.one_of(st.none(), st.integers(), st.text(), st.lists(st.integers(), max_size=3)))
        def test_nonboolean_authorization_refused(self, value):
            if isinstance(value, bool):
                return
            self.assertEqual(reference({"id":"case-1","evidence":["a"],"authorized":value}), "REFUSE")

if __name__ == "__main__":
    unittest.main()
