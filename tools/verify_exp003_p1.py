"""Independent EXP003-P1 evidence consistency verifier. Does NOT import engine.

Digest agreement and specification replay do NOT prove evaluator/proposer isolation.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

DOMAIN = tuple(range(24))
NAMES = tuple(f"H{i:02d}" for i in range(16))
ALLOWED_POLICIES = ("fixed", "random", "greedy", "external")
ALLOWED_FAILURES = (
    "PROPOSER_TIMEOUT", "PROPOSER_START_FAILED", "PROPOSER_NONZERO_EXIT",
    "PROPOSER_OUTPUT_TOO_LARGE", "PROPOSER_INVALID_JSON",
    "PROPOSER_INVALID_SCHEMA", "INVALID_PROBE", "EXTERNAL_COMMAND_MISSING",
)


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def nodup(pairs):
    obj = {}
    for key, val in pairs:
        require(key not in obj, "duplicate JSON key")
        obj[key] = val
    return obj


def digest(key, label):
    return hashlib.sha256(key + b"\0EXP003-P1\0" + label.encode("ascii")).digest()


def regen(secret_hex, task_index):
    key = bytes.fromhex(secret_hex)
    seen = set()
    words = []
    for index in range(16):
        for retry in range(512):
            v = int.from_bytes(
                digest(key, f"task:{task_index}:row:{index}:retry:{retry}")[:3], "big"
            )
            if v not in seen:
                seen.add(v)
                words.append(v)
                break
        else:
            raise ValueError("row generation exhausted")
    truth = NAMES[digest(key, f"truth:{task_index}")[0] % 16]
    matrix = [[(v >> probe) & 1 for probe in DOMAIN] for v in words]
    return matrix, truth


def bit(matrix, h, probe):
    return matrix[NAMES.index(h)][probe]


def control_probe(policy, secret_hex, task_index, step, matrix, remaining, used):
    available = [p for p in DOMAIN if p not in used]
    if policy == "fixed":
        return available[0]
    if policy == "random":
        key = bytes.fromhex(secret_hex)
        pick = int.from_bytes(digest(key, f"random:{task_index}:step:{step}"), "big")
        return available[pick % len(available)]
    if policy == "greedy":
        n = len(remaining)
        def score(probe):
            groups = [sum(bit(matrix, name, probe) == v for name in remaining) for v in (0, 1)]
            return n*n - sum(z*z for z in groups)
        return max(available, key=lambda p: (score(p), -p))
    raise ValueError("external selection cannot be independently inferred")


def expected_summary(results, policies):
    output = {}
    for p in policies:
        group = [r for r in results if r["policy"] == p]
        solved = [r for r in group if r["solved"]]
        output[p] = {
            "solved_rate": len(solved)/len(group),
            "mean_probes_all": sum(len(r["records"]) for r in group)/len(group),
            "mean_probes_solved": sum(len(r["records"]) for r in solved)/len(solved) if solved else None,
            "mean_remaining": sum(len(r["remaining"]) for r in group)/len(group),
            "deferred": sum(r["status"] == "DEFERRED" for r in group),
        }
    return output


def verify(raw, expected_sha256):
    require(type(raw) is bytes and hashlib.sha256(raw).hexdigest() == expected_sha256,
            "evidence SHA-256 mismatch")
    doc = json.loads(raw, object_pairs_hook=nodup,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    require(type(doc) is dict and set(doc) == {
        "protocol", "evidence_status", "task_origin", "evaluator_secret_hex",
        "task_count", "max_steps", "policies", "model_metadata",
        "results", "summary", "limitations",
    }, "root fields mismatch")
    require(doc["protocol"] == "EXP003-P1" and
            doc["evidence_status"] == "EXPLORATORY_SIMULATED", "unexpected protocol/status")
    require(doc["task_origin"] in ("PUBLIC_TEST_SECRET", "SECRET_REVEALED_AFTER_PILOT"),
            "task origin invalid")
    secret_hex = doc["evaluator_secret_hex"]
    require(type(secret_hex) is str and len(secret_hex) == 64 and
            all(c in "0123456789abcdef" for c in secret_hex), "invalid evaluator secret")
    task_count = doc["task_count"]
    require(type(task_count) is int and 1 <= task_count <= 20, "invalid task count")
    require(type(doc["max_steps"]) is int and doc["max_steps"] == 5,
            "step count mismatch")
    policies = doc["policies"]
    require(type(policies) is list and policies and len(policies) == len(set(policies))
            and all(type(p) is str and p in ALLOWED_POLICIES for p in policies), "invalid policies")
    meta = doc["model_metadata"]
    if "external" not in policies:
        require(meta is None, "unexpected model metadata")
    else:
        require(type(meta) is dict and set(meta) == {"id", "sha256_operator_reported"},
                "model metadata missing")
        h = meta["sha256_operator_reported"]
        require(type(meta["id"]) is str and bool(meta["id"].strip()) and
                type(h) is str and len(h) == 64 and all(c in "0123456789abcdef" for c in h),
                "model metadata invalid")
    require(type(doc["limitations"]) is list and bool(doc["limitations"]) and
            all(type(x) is str and x for x in doc["limitations"]), "limitations missing")
    results = doc["results"]
    require(type(results) is list and len(results) == task_count * len(policies),
            "row count mismatch")
    seen = set()
    probes = 0
    for row in results:
        require(type(row) is dict and set(row) == {
            "task_index", "policy", "matrix", "truth", "records",
            "remaining", "solved", "status", "error"
        }, "row schema mismatch")
        i, p = row["task_index"], row["policy"]
        require(type(i) is int and 0 <= i < task_count and type(p) is str and p in policies,
                "result identity invalid")
        require((i, p) not in seen, "duplicate result")
        seen.add((i, p))
        matrix, truth = regen(secret_hex, i)
        require(row["matrix"] == matrix and row["truth"] == truth, "task fixture mismatch")
        remaining, used = list(NAMES), set()
        records = row["records"]
        require(type(records) is list and len(records) <= 5, "record count invalid")
        for step, event in enumerate(records):
            require(type(event) is dict and set(event) ==
                    {"step", "pre", "probe", "outcome", "post"}, "event schema mismatch")
            x = event["probe"]
            require(type(event["step"]) is int and event["step"] == step, "event step mismatch")
            require(type(x) is int and x in DOMAIN and x not in used, "invalid selected probe")
            require(len(remaining) > 1 and event["pre"] == remaining, "event pre-state mismatch")
            if p != "external":
                expected = control_probe(p, secret_hex, i, step, matrix, remaining, used)
                require(x == expected, "baseline choice mismatch")
            observed = bit(matrix, truth, x)
            require(type(event["outcome"]) is int and event["outcome"] == observed,
                    "oracle outcome mismatch")
            updated = [name for name in remaining if bit(matrix, name, x) == observed]
            require(truth in updated and event["post"] == updated,
                    "candidate elimination mismatch")
            remaining = updated
            used.add(x)
            probes += 1
        require(row["remaining"] == remaining, "terminal candidate mismatch")
        solved = len(remaining) == 1
        require(type(row["solved"]) is bool and row["solved"] == solved, "solved flag mismatch")
        require(row["status"] in ("COMPLETE", "DEFERRED"), "status invalid")
        if row["status"] == "COMPLETE":
            require(row["error"] is None and (solved or len(records) == 5),
                    "completion inconsistent")
        else:
            require(p == "external" and not solved and len(records) < 5 and
                    type(row["error"]) is str and row["error"] in ALLOWED_FAILURES,
                    "deferred status inconsistent")
    require(seen == {(i, p) for i in range(task_count) for p in policies}, "missing result pair")
    expected = expected_summary(results, policies)
    actual = doc["summary"]
    require(type(actual) is dict and set(actual) == set(expected), "summary keys mismatch")
    for p in policies:
        require(type(actual[p]) is dict and set(actual[p]) == set(expected[p]),
                "policy summary shape mismatch")
        for key, value in expected[p].items():
            a = actual[p][key]
            if value is None:
                require(a is None, "mean solved probes invalid")
            else:
                require(type(a) in (int, float) and a == value,
                        f"aggregate {p}.{key} mismatch")
    return {"policy_task_pairs": len(seen), "observations": probes, "summary": expected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--sha256", required=True, help="Expected original SHA-256 from independent log")
    args = parser.parse_args(argv)
    if len(args.sha256) != 64 or any(c not in "0123456789abcdef" for c in args.sha256):
        parser.error("requires 64-character lowercase SHA-256")
    try:
        result = verify(args.path.read_bytes(), args.sha256)
    except (ValueError, OSError, TypeError, KeyError, IndexError, ZeroDivisionError) as exc:
        print("VERDICT: INCONSISTENT OR UNVERIFIABLE:", exc, file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH EXP003-P1 SPECIFICATION")
    print(json.dumps(result, sort_keys=True))
    print("LIMITATION: consistency only; proposer oracle isolation NOT VALIDATED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
