"""Stand-alone deterministic consistency verifier for EXP003-P0 evidence.

Does not import or run the experiment engine. Requires a pinned SHA-256 from an
independent log. A PASS is internal consistency, not independent-world truth.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

NAMES = ("even", "multiple3", "multiple5", "lowhalf", "bit1", "bit2", "bit3", "mod4eq1")
POLICIES = ("fixed", "random", "greedy", "external")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def nodup(pairs):
    obj = {}
    for k, v in pairs:
        require(k not in obj, "duplicate JSON key")
        obj[k] = v
    return obj


def value(name, x):
    if name == "even": return int(x % 2 == 0)
    if name == "multiple3": return int(x % 3 == 0)
    if name == "multiple5": return int(x % 5 == 0)
    if name == "lowhalf": return int(x < 16)
    if name == "bit1": return int(bool(x & 2))
    if name == "bit2": return int(bool(x & 4))
    if name == "bit3": return int(bool(x & 8))
    if name == "mod4eq1": return int(x % 4 == 1)
    raise ValueError("unknown predicate")


def fixture(seed):
    candidates = tuple(sorted(random.Random(f"EXP003-P0:task:{seed}").sample(NAMES, 4)))
    truth = random.Random(f"EXP003-P0:truth:{seed}").choice(candidates)
    return candidates, truth


def greedy(active, used):
    def gain(x):
        sizes = [sum(value(h, x) == o for h in active) for o in (0, 1)]
        return len(active) - sum(k*k for k in sizes) / len(active)
    return max((x for x in range(32) if x not in used), key=lambda x: (gain(x), -x))


def verify(raw, sha):
    require(hashlib.sha256(raw).hexdigest() == sha, "SHA-256 mismatch")
    data = json.loads(raw, object_pairs_hook=nodup,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError("nonfinite " + s)))
    require(type(data) is dict and set(data) == {
        "protocol", "evidence_status", "seeds", "max_steps", "policies", "summary", "results", "limitations"
    }, "root fields mismatch")
    require(data["protocol"] == "EXP003-P0" and data["evidence_status"] == "EXPLORATORY_SIMULATED", "protocol mismatch")
    require(type(data["max_steps"]) is int and data["max_steps"] == 6, "steps mismatch")
    seeds, policies = data["seeds"], data["policies"]
    require(type(seeds) is list and 1 <= len(seeds) <= 100 and
            all(type(s) is int and 0 <= s < 1000000 for s in seeds) and len(set(seeds)) == len(seeds), "invalid seeds")
    require(type(policies) is list and policies and
            all(type(p) is str and p in POLICIES for p in policies) and len(set(policies)) == len(policies), "invalid policies")
    require(type(data["results"]) is list and len(data["results"]) == len(seeds)*len(policies), "result count mismatch")
    require(type(data["limitations"]) is list and data["limitations"], "limitations missing")
    seen = set()
    aggregation = {p: [] for p in policies}
    count = 0
    for row in data["results"]:
        require(type(row) is dict and set(row) == {
            "seed", "policy", "candidates", "truth", "status", "failure", "records", "remaining", "solved"
        }, "row fields mismatch")
        seed, policy = row["seed"], row["policy"]
        require(type(seed) is int and seed in seeds and policy in policies, "invalid row identity")
        require((seed, policy) not in seen, "duplicate task/policy")
        seen.add((seed, policy))
        candidates, truth = fixture(seed)
        require(row["candidates"] == list(candidates) and row["truth"] == truth, "fixture mismatch")
        require(type(row["records"]) is list and len(row["records"]) <= 6, "record shape mismatch")
        active = candidates
        used = set()
        picker = random.Random(f"EXP003-P0:random:{seed}")
        for i, rec in enumerate(row["records"]):
            require(type(rec) is dict and set(rec) == {"step", "pre", "probe", "outcome", "post"}, "record fields mismatch")
            x = rec["probe"]
            require(type(rec["step"]) is int and rec["step"] == i, "step mismatch")
            require(type(x) is int and 0 <= x < 32 and x not in used, "unauthorized probe")
            require(rec["pre"] == list(active) and len(active) > 1, "pre-state mismatch")
            if policy == "fixed":
                require(x == next(k for k in range(32) if k not in used), "fixed policy mismatch")
            if policy == "random":
                require(x == picker.choice([k for k in range(32) if k not in used]), "random policy mismatch")
            if policy == "greedy":
                require(x == greedy(active, used), "greedy policy mismatch")
            o = value(truth, x)
            require(type(rec["outcome"]) is int and rec["outcome"] == o, "outcome mismatch")
            updated = tuple(h for h in active if value(h, x) == o)
            require(rec["post"] == list(updated), "post-state mismatch")
            require(truth in updated, "truth eliminated")
            active = updated
            used.add(x)
            count += 1
        require(row["remaining"] == list(active), "terminal state mismatch")
        solved = len(active) == 1
        require(type(row["solved"]) is bool and row["solved"] == solved, "solved mismatch")
        require(row["status"] in ("COMPLETE", "DEFERRED"), "invalid status")
        if row["status"] == "COMPLETE":
            require(row["failure"] is None and (solved or len(used) == 6), "invalid completion")
        else:
            require(policy == "external" and type(row["failure"]) is str and row["failure"] and
                    not solved and len(used) < 6, "invalid defer")
        aggregation[policy].append(row)
    require(seen == {(s,p) for s in seeds for p in policies}, "missing pairs")
    require(type(data["summary"]) is dict and set(data["summary"]) == set(policies), "summary shape mismatch")
    for policy in policies:
        rows = aggregation[policy]
        expected = {
            "solved_rate": sum(r["solved"] for r in rows)/len(rows),
            "mean_remaining": sum(len(r["remaining"]) for r in rows)/len(rows),
            "deferred": sum(r["status"] == "DEFERRED" for r in rows),
        }
        recorded = data["summary"][policy]
        require(type(recorded) is dict and set(recorded) == set(expected), "summary fields mismatch")
        for k, v in expected.items():
            require(type(recorded[k]) in (int, float) and recorded[k] == v, "summary fields mismatch")
    return {"records": count, "tasks": len(seen), "summary": data["summary"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--sha256", required=True, help="Expected digest from independent log")
    args = parser.parse_args()
    if len(args.sha256) != 64 or any(c not in '0123456789abcdef' for c in args.sha256):
        parser.error("expected 64-character lowercase hex digest")
    try:
        checked = verify(args.file.read_bytes(), args.sha256)
    except (OSError, ValueError, TypeError, KeyError, StopIteration) as e:
        print("VERDICT: INCONSISTENT OR UNVERIFIABLE:", e, file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH EXP003-P0 SPECIFICATION")
    print(json.dumps(checked, sort_keys=True))
    print("STATUS: EXPLORATORY_SIMULATED — NOT VALIDATED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
