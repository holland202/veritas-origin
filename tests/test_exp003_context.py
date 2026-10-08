"""Check that the exploratory external proposal channel does not directly reveal oracle metadata."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "src/origin/exp003.py"
spec = importlib.util.spec_from_file_location("exp003_context", SOURCE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)


class TestExternalContext(unittest.TestCase):
    def test_no_seed_or_truth_sent_to_proposer(self):
        seen = []

        def probe(_command, request, _timeout):
            seen.append(request)
            self.assertEqual(request["protocol"], "EXP003-P0")
            self.assertNotIn("task_seed", request)
            self.assertNotIn("truth", request)
            self.assertNotIn("oracle", request)
            used = {r["probe"] for r in request["observations"]}
            return next(x for x in request["domain"] if x not in used)

        with patch.object(engine, "external_proposal", side_effect=probe):
            result = engine.evaluate(17, "external", command=["test-only"])
        self.assertEqual(result["status"], "COMPLETE")
        self.assertGreater(len(seen), 0)
        self.assertEqual(len(result["records"]), len(seen))


if __name__ == "__main__":
    unittest.main()
