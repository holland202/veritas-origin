import importlib.util
import math
import unittest
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "experiments/exp002/run.py"
spec = importlib.util.spec_from_file_location("exp002_frozen", RUNNER)
exp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)


class TestEXP002(unittest.TestCase):
    def test_frozen_parameters(self):
        self.assertEqual(exp.ARMS, {
            "low": 0.2, "medium": 0.5, "high": 0.8
        })
        self.assertEqual(exp.POLICIES, (
            "fixed-medium", "random", "ucb1"
        ))
        self.assertEqual(exp.TRIALS, 100)
        self.assertEqual(list(exp.SEEDS), list(range(100)))

    def test_deterministic_outcomes(self):
        self.assertEqual(
            exp.potential_outcomes(17),
            exp.potential_outcomes(17)
        )

    def test_outcome_dimensions(self):
        for seed in (0, 17, 99):
            outcomes = exp.potential_outcomes(seed)
            self.assertEqual(set(outcomes), set(exp.ARMS))
            for arm in exp.ARMS:
                self.assertEqual(len(outcomes[arm]), 100)
                self.assertTrue(
                    all(x in (0, 1) for x in outcomes[arm])
                )

    def test_deterministic_policy_replay(self):
        outcomes = exp.potential_outcomes(17)
        for policy in exp.POLICIES:
            self.assertEqual(
                exp.evaluate(17, policy, outcomes),
                exp.evaluate(17, policy, outcomes)
            )

    def test_trial_counts_and_totals(self):
        outcomes = exp.potential_outcomes(17)
        for policy in exp.POLICIES:
            result = exp.evaluate(17, policy, outcomes)
            records = result["records"]
            self.assertEqual(len(records), 100)
            self.assertEqual(
                [r["step"] for r in records],
                list(range(100))
            )
            self.assertEqual(
                result["total_reward"],
                sum(r["reward"] for r in records)
            )

    def test_shared_potential_outcome_consumption(self):
        outcomes = exp.potential_outcomes(17)
        for policy in exp.POLICIES:
            result = exp.evaluate(17, policy, outcomes)
            counts = {arm: 0 for arm in exp.ARMS}
            for record in result["records"]:
                arm = record["arm"]
                self.assertIn(arm, exp.ARMS)
                self.assertEqual(
                    record["reward"],
                    outcomes[arm][counts[arm]]
                )
                counts[arm] += 1

    def test_fixed_policy(self):
        outcomes = exp.potential_outcomes(17)
        result = exp.evaluate(
            17, "fixed-medium", outcomes
        )
        self.assertTrue(all(
            r["arm"] == "medium"
            for r in result["records"]
        ))
        self.assertEqual(
            result["total_reward"],
            sum(outcomes["medium"])
        )

    def test_ucb_initial_exploration(self):
        outcomes = {
            arm: [0] * 100 for arm in exp.ARMS
        }
        result = exp.evaluate(0, "ucb1", outcomes)
        self.assertEqual(
            [r["arm"] for r in result["records"][:3]],
            ["low", "medium", "high"]
        )

    def test_ucb_reference_oracle(self):
        outcomes = {
            "low": [0] * 100,
            "medium": [1] * 100,
            "high": [1, 0] * 50
        }
        actual = exp.evaluate(0, "ucb1", outcomes)

        counts = {a: 0 for a in exp.ARMS}
        rewards = {a: 0 for a in exp.ARMS}
        expected = []

        for step in range(100):
            unpulled = [
                a for a in exp.ARMS if counts[a] == 0
            ]
            if unpulled:
                arm = unpulled[0]
            else:
                scores = {
                    a: rewards[a] / counts[a]
                    + math.sqrt(
                        2 * math.log(step + 1) / counts[a]
                    )
                    for a in exp.ARMS
                }
                arm = max(exp.ARMS, key=scores.get)

            reward = outcomes[arm][counts[arm]]
            expected.append((arm, reward))
            counts[arm] += 1
            rewards[arm] += reward

        observed = [
            (r["arm"], r["reward"])
            for r in actual["records"]
        ]
        self.assertEqual(observed, expected)

    def test_run_aggregation_and_criterion(self):
        data = exp.run()
        self.assertEqual(data["experiment"], "EXP002")
        self.assertEqual(len(data["results"]), 300)

        for policy in exp.POLICIES:
            rows = [
                r for r in data["results"]
                if r["policy"] == policy
            ]
            self.assertEqual(len(rows), 100)
            self.assertEqual(
                data["means"][policy],
                sum(r["total_reward"] for r in rows) / 100
            )

        expected = all(
            data["means"]["ucb1"] - data["means"][b] >= 5
            for b in ("fixed-medium", "random")
        )
        self.assertEqual(data["criterion_met"], expected)


if __name__ == "__main__":
    unittest.main()
