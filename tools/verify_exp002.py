#!/usr/bin/env python3
"""Offline EXP002 evidence consistency checker.

Does not import, execute, or modify experiments/exp002/run.py.
A passing result shows consistency with this verifier's recorded specification,
not independent evidence of world truth or cross-runtime replication.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence/exp002/exp002-20261008T194950169959Z-fccc3f26.json"
EXPECTED_SHA256 = "a5fe362571ea600485cabd6759542314f0e6562e36ea6330feeb06db187faf6c"
ARMS = ("low", "medium", "high")
PROBABILITIES = {"low": 0.2, "medium": 0.5, "high": 0.8}
POLICIES = ("fixed-medium", "random", "ucb1")
SEEDS = tuple(range(100))
TRIALS = 100


class EvidenceError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"duplicate JSON key: {key}")
        obj[key] = value
    return obj


def reject_constant(value):
    raise EvidenceError(f"nonstandard JSON numeric constant: {value}")


def exact_keys(obj, keys, where):
    require(type(obj) is dict, f"{where}: expected object")
    require(set(obj) == set(keys), f"{where}: unexpected or missing keys")


def verify(path=EVIDENCE):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == EXPECTED_SHA256, "evidence SHA-256 mismatch")

    data = json.loads(
        raw,
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_constant,
    )
    exact_keys(data, (
        "experiment", "status", "seeds", "trials_per_policy_per_seed",
        "arm_probabilities", "means", "criterion_met", "results",
    ), "root")
    require(data["experiment"] == "EXP002", "experiment mismatch")
    require(data["status"] == "CONFIRMATORY_RUN", "status mismatch")
    require(data["seeds"] == [0, 99], "seed range mismatch")
    require(type(data["trials_per_policy_per_seed"]) is int
            and data["trials_per_policy_per_seed"] == TRIALS, "trial count mismatch")
    require(data["arm_probabilities"] == PROBABILITIES, "probabilities mismatch")
    require(type(data["criterion_met"]) is bool, "criterion type mismatch")
    require(type(data["results"]) is list and len(data["results"]) == 300,
            "result count mismatch")

    seen = set()
    totals = {policy: [] for policy in POLICIES}
    verified_records = 0

    for result_index, result in enumerate(data["results"]):
        exact_keys(result, ("seed", "policy", "total_reward", "records"),
                   f"result {result_index}")
        seed = result["seed"]
        policy = result["policy"]
        require(type(seed) is int and seed in SEEDS, "invalid seed")
        require(type(policy) is str and policy in POLICIES, "invalid policy")
        require((seed, policy) not in seen, "duplicate seed-policy pair")
        seen.add((seed, policy))
        require(type(result["records"]) is list
                and len(result["records"]) == TRIALS, "invalid records")

        # Reconstruct potential outcomes without calling the experimental runner.
        outcomes = {
            arm: [
                int(random.Random(f"{seed}:{arm}:{pull}").random()
                    < PROBABILITIES[arm])
                for pull in range(TRIALS)
            ]
            for arm in ARMS
        }
        chooser = random.Random(f"choice:{seed}")
        pulls = {arm: 0 for arm in ARMS}
        earned = {arm: 0 for arm in ARMS}

        for step, record in enumerate(result["records"]):
            exact_keys(record, ("step", "arm", "reward"),
                       f"result {result_index} step {step}")
            if policy == "fixed-medium":
                selected = "medium"
            elif policy == "random":
                selected = chooser.choice(ARMS)
            else:
                unseen = [arm for arm in ARMS if pulls[arm] == 0]
                if unseen:
                    selected = unseen[0]
                else:
                    selected = max(
                        ARMS,
                        key=lambda arm: earned[arm] / pulls[arm]
                        + math.sqrt(2 * math.log(step + 1) / pulls[arm]),
                    )

            expected_reward = outcomes[selected][pulls[selected]]
            require(type(record["step"]) is int and record["step"] == step,
                    f"incorrect step at result {result_index}:{step}")
            require(record["arm"] == selected,
                    f"incorrect arm at result {result_index}:{step}")
            require(type(record["reward"]) is int
                    and record["reward"] == expected_reward,
                    f"incorrect reward at result {result_index}:{step}")
            pulls[selected] += 1
            earned[selected] += expected_reward
            verified_records += 1

        total = sum(earned.values())
        require(type(result["total_reward"]) is int
                and result["total_reward"] == total, "total reward mismatch")
        totals[policy].append(total)

    expected_pairs = {(seed, policy) for seed in SEEDS for policy in POLICIES}
    require(seen == expected_pairs, "missing seed-policy pairs")
    exact_keys(data["means"], POLICIES, "means")
    means = {policy: sum(totals[policy]) / len(SEEDS) for policy in POLICIES}
    for policy in POLICIES:
        recorded = data["means"][policy]
        require(type(recorded) in (int, float) and math.isfinite(recorded)
                and abs(recorded - means[policy]) < 1e-10,
                f"incorrect mean for {policy}")
    differences = {
        baseline: means["ucb1"] - means[baseline]
        for baseline in ("fixed-medium", "random")
    }
    criterion = all(delta >= 5 for delta in differences.values())
    require(data["criterion_met"] is criterion, "criterion mismatch")

    return digest, verified_records, means, differences, criterion


def main():
    if len(sys.argv) > 2:
        print("Usage: python3 tools/verify_exp002.py [evidence-file]", file=sys.stderr)
        return 2
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else EVIDENCE
    try:
        digest, count, means, differences, criterion = verify(path)
    except (EvidenceError, OSError, ValueError, TypeError, KeyError,
            IndexError, OverflowError) as exc:
        print(f"VERDICT: INCONSISTENT OR UNVERIFIABLE: {exc}", file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH EXP002 SPECIFICATION")
    print("Evidence SHA256:", digest)
    print("Verified records:", count)
    print("Policy means:", means)
    print("UCB1 differences:", differences)
    print("Criterion met:", criterion)
    print("LIMITATION: Python RNG-dependent synthetic reconstruction; "
          "no cross-runtime replication or external-world validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
