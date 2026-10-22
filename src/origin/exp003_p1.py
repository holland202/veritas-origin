"""EXP003-P1: bounded binary hypothesis discrimination — exploratory only.

Evaluator secret is withheld from proposal messages, not isolated from processes
on the same OS account. External command mode is NOT A SANDBOX.
"""
import argparse
import hashlib
import json
import secrets
import shlex
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL = "EXP003-P1"
HYPOTHESES = tuple(f"H{i:02d}" for i in range(16))
PROBES = tuple(range(24))
MAX_STEPS = 5
POLICIES = ("fixed", "random", "greedy", "external")
LIMITATIONS = [
    "EXPLORATORY_SIMULATED: 16 synthetic hypotheses with binary response matrices",
    "No autonomous hypothesis invention or external-world experiment",
    "External proposer is an unsandboxed subprocess when enabled",
    "Proposer and evaluator do not have independently verified process isolation",
    "Evaluator secret is released in the evidence after the run; never reuse tasks as held out",
    "External model identifier and artifact digest, if supplied, are operator-reported",
    "No network/cost/global CPU enforcement for the external proposer",
]


def _valid_secret(secret_hex):
    return (type(secret_hex) is str and len(secret_hex) == 64 and
            all(ch in "0123456789abcdef" for ch in secret_hex))


def _digest(key, domain):
    return hashlib.sha256(key + b"\0EXP003-P1\0" + domain.encode("ascii")).digest()


def make_task(secret_hex, index):
    if not _valid_secret(secret_hex) or type(index) is not int or not 0 <= index < 1000000:
        raise ValueError("invalid evaluator secret or bounded index")
    key = bytes.fromhex(secret_hex)
    values, seen = [], set()
    for row in range(len(HYPOTHESES)):
        for retry in range(512):
            v = int.from_bytes(_digest(key, f"task:{index}:row:{row}:retry:{retry}")[:3], "big")
            if v not in seen:
                values.append(v)
                seen.add(v)
                break
        else:
            raise ValueError("unable to generate distinct hypotheses")
    matrix = [[(word >> probe) & 1 for probe in PROBES] for word in values]
    truth_idx = _digest(key, f"truth:{index}")[0] % len(HYPOTHESES)
    return {"index": index, "hypotheses": list(HYPOTHESES),
            "matrix": matrix, "truth": HYPOTHESES[truth_idx]}


def outcome(task, hypothesis, probe):
    return task["matrix"][HYPOTHESES.index(hypothesis)][probe]


def information_score(task, remaining, probe):
    n = len(remaining)
    bins = [sum(outcome(task, name, probe) == bit for name in remaining)
            for bit in (0, 1)]
    return n * n - sum(size * size for size in bins)


def greedy_probe(task, remaining, used):
    return max((p for p in PROBES if p not in used),
               key=lambda p: (information_score(task, remaining, p), -p))


def random_probe(secret_hex, task_index, step, used):
    choices = [p for p in PROBES if p not in used]
    key = bytes.fromhex(secret_hex)
    val = int.from_bytes(_digest(key, f"random:{task_index}:step:{step}"), "big")
    return choices[val % len(choices)]


def _strict_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def external_proposal(command, context, timeout):
    """A trust boundary for syntax ONLY, not a security sandbox."""
    if not command:
        raise ValueError("EXTERNAL_COMMAND_MISSING")
    try:
        cp = subprocess.run(command, input=json.dumps(context, sort_keys=True),
                            capture_output=True, text=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ValueError("PROPOSER_TIMEOUT") from None
    except OSError:
        raise ValueError("PROPOSER_START_FAILED") from None
    if cp.returncode != 0:
        raise ValueError("PROPOSER_NONZERO_EXIT")
    if len(cp.stdout) > 4096:
        raise ValueError("PROPOSER_OUTPUT_TOO_LARGE")
    try:
        result = json.loads(
            cp.stdout, object_pairs_hook=_strict_object,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
        )
    except (ValueError, TypeError) as exc:
        raise ValueError("PROPOSER_INVALID_JSON") from exc
    if type(result) is not dict or set(result) != {"probe"}:
        raise ValueError("PROPOSER_INVALID_SCHEMA")
    return result["probe"]


def evaluate(secret_hex, index, policy, command=None, timeout=5):
    if policy not in POLICIES:
        raise ValueError("invalid policy")
    task = make_task(secret_hex, index)
    remaining, used, records = list(HYPOTHESES), set(), []
    status, error = "COMPLETE", None
    for step in range(MAX_STEPS):
        if len(remaining) <= 1:
            break
        context = {"protocol": PROTOCOL,
                   "hypotheses": list(HYPOTHESES),
                   "candidate_names": list(remaining),
                   "matrix": task["matrix"],
                   "available_probes": [x for x in PROBES if x not in used],
                   "observations": [{"probe": r["probe"], "outcome": r["outcome"]}
                                    for r in records],
                   "remaining_budget": MAX_STEPS - step}
        try:
            if policy == "fixed":
                proposal = next(x for x in PROBES if x not in used)
            elif policy == "random":
                proposal = random_probe(secret_hex, index, step, used)
            elif policy == "greedy":
                proposal = greedy_probe(task, remaining, used)
            else:
                proposal = external_proposal(command, context, timeout)
            if type(proposal) is not int or proposal not in PROBES or proposal in used:
                raise ValueError("INVALID_PROBE")
        except (ValueError, StopIteration) as exc:
            status, error = "DEFERRED", str(exc)[:80]
            break
        observed = outcome(task, task["truth"], proposal)
        updated = [name for name in remaining if outcome(task, name, proposal) == observed]
        if task["truth"] not in updated:
            raise AssertionError("evaluator state contradiction")
        records.append({"step": step, "pre": list(remaining), "probe": proposal,
                        "outcome": observed, "post": list(updated)})
        used.add(proposal)
        remaining = updated
    return {"task_index": index, "policy": policy,
            "matrix": task["matrix"], "truth": task["truth"],
            "records": records, "remaining": remaining,
            "solved": len(remaining) == 1, "status": status, "error": error}


def summarize(rows, policies):
    summary = {}
    for policy in policies:
        group = [r for r in rows if r["policy"] == policy]
        solved = [r for r in group if r["solved"]]
        summary[policy] = {
            "solved_rate": len(solved) / len(group),
            "mean_probes_all": sum(len(r["records"]) for r in group) / len(group),
            "mean_probes_solved": (
                sum(len(r["records"]) for r in solved) / len(solved) if solved else None),
            "mean_remaining": sum(len(r["remaining"]) for r in group) / len(group),
            "deferred": sum(r["status"] == "DEFERRED" for r in group),
        }
    return summary


def study(secret_hex, task_count=8, policies=("fixed", "random", "greedy"),
          command=None, timeout=5, acknowledge_unisolated=False,
          model_id=None, model_sha256=None, public_test_secret=False):
    if not _valid_secret(secret_hex):
        raise ValueError("secret must be exactly 64 lowercase hexadecimal characters")
    if type(task_count) is not int or not 1 <= task_count <= 20:
        raise ValueError("task count must be 1..20")
    if type(policies) not in (tuple, list) or not policies or len(set(policies)) != len(policies) or any(p not in POLICIES for p in policies):
        raise ValueError("invalid policy set")
    if not 0 < timeout <= 10:
        raise ValueError("timeout must be within 0..10 seconds")
    if "external" in policies:
        if not acknowledge_unisolated or not command:
            raise ValueError("unsandboxed external proposer must be explicitly acknowledged")
        if type(model_id) is not str or not model_id.strip():
            raise ValueError("model id is required for external proposer")
        if not _valid_secret(model_sha256):
            raise ValueError("operator-reported model artifact SHA-256 is required")
    elif command is not None or model_id is not None or model_sha256 is not None:
        raise ValueError("model metadata/command requires external policy")
    rows = [evaluate(secret_hex, task_index, policy, command=command, timeout=timeout)
            for task_index in range(task_count) for policy in policies]
    return {"protocol": PROTOCOL,
            "evidence_status": "EXPLORATORY_SIMULATED",
            "task_origin": "PUBLIC_TEST_SECRET" if public_test_secret else "SECRET_REVEALED_AFTER_PILOT",
            "evaluator_secret_hex": secret_hex, "task_count": task_count,
            "max_steps": MAX_STEPS, "policies": list(policies),
            "model_metadata": ({"id": model_id, "sha256_operator_reported": model_sha256}
                               if "external" in policies else None),
            "results": rows, "summary": summarize(rows, policies),
            "limitations": list(LIMITATIONS)}


def save_fresh(data, destination):
    destination.mkdir(parents=True, exist_ok=True)
    name = ("exp003-p1-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            + "-" + uuid.uuid4().hex[:10] + ".json")
    path = destination / name
    raw = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as f:
        f.write(raw)
    return path, hashlib.sha256(raw).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true", help="authorize exploratory pilot")
    parser.add_argument("--task-count", type=int, default=8)
    parser.add_argument("--output-dir", default="evidence/exp003")
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--test-secret-hex")
    parser.add_argument("--allow-public-test-secret", action="store_true")
    parser.add_argument("--external-command")
    parser.add_argument("--acknowledge-unisolated-proposer", action="store_true")
    parser.add_argument("--model-id")
    parser.add_argument("--model-sha256")
    args = parser.parse_args(argv)
    if not args.pilot:
        parser.error("HALT: explicit --pilot required")
    if args.test_secret_hex is not None and not args.allow_public_test_secret:
        parser.error("HALT: --test-secret-hex requires --allow-public-test-secret")
    if args.allow_public_test_secret and args.test_secret_hex is None:
        parser.error("HALT: --allow-public-test-secret requires --test-secret-hex")
    if args.external_command and not args.acknowledge_unisolated_proposer:
        parser.error("HALT: external process is NOT sandboxed: acknowledge explicitly")
    if args.acknowledge_unisolated_proposer and not args.external_command:
        parser.error("HALT: external process not configured")
    try:
        secret_hex = args.test_secret_hex if args.test_secret_hex is not None else secrets.token_hex(32)
        command = shlex.split(args.external_command) if args.external_command else None
        policies = ("fixed", "random", "greedy") + (("external",) if command else ())
        result = study(secret_hex, task_count=args.task_count, policies=policies,
                       command=command, timeout=args.timeout,
                       acknowledge_unisolated=args.acknowledge_unisolated_proposer,
                       model_id=args.model_id, model_sha256=args.model_sha256,
                       public_test_secret=args.allow_public_test_secret)
        path, digest = save_fresh(result, Path(args.output_dir))
    except (ValueError, OSError) as exc:
        parser.error("HALT: " + str(exc))
    print("EVIDENCE:", path)
    print("SHA256:", digest)
    print("SUMMARY:", json.dumps(result["summary"], sort_keys=True))
    print("STATUS: EXPLORATORY_SIMULATED — NOT VALIDATED; C1 oracle isolation UNMET")
    return 0


if __name__ == "__main__":
    sys.exit(main())
