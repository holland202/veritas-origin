"""EXP003-P0 controlled hypothesis discrimination, standard-library-only.

EXPLORATORY substrate. No claims of model learning or autonomous science.
The external proposer is untrusted and not sandboxed: run only trusted local commands.
"""
import argparse
import hashlib
import json
import math
import random
import shlex
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

DOMAIN = tuple(range(32))
REGISTRY = {
    "even": lambda x: int(x % 2 == 0),
    "multiple3": lambda x: int(x % 3 == 0),
    "multiple5": lambda x: int(x % 5 == 0),
    "lowhalf": lambda x: int(x < 16),
    "bit1": lambda x: int(bool(x & 2)),
    "bit2": lambda x: int(bool(x & 4)),
    "bit3": lambda x: int(bool(x & 8)),
    "mod4eq1": lambda x: int(x % 4 == 1),
}
LABELS = tuple(REGISTRY)
POLICIES = ("fixed", "random", "greedy", "external")
MAX_STEPS = 6


def strict_object(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"duplicate JSON key: {k}")
        out[k] = v
    return out


def task(seed):
    if type(seed) is not int or not 0 <= seed < 1000000:
        raise ValueError("seed outside bounded nonnegative range")
    chooser = random.Random(f"EXP003-P0:task:{seed}")
    candidates = tuple(sorted(chooser.sample(LABELS, 4)))
    truth = random.Random(f"EXP003-P0:truth:{seed}").choice(candidates)
    return candidates, truth


def reduction(candidates, probe):
    """Expected eliminated candidates under a uniform distribution (pre-outcome)."""
    groups = [0, 0]
    for name in candidates:
        groups[REGISTRY[name](probe)] += 1
    n = len(candidates)
    return n - sum(size * size for size in groups) / n


def choose_greedy(candidates, used):
    choices = [x for x in DOMAIN if x not in used]
    if not choices:
        raise ValueError("no probe remaining")
    return max(choices, key=lambda x: (reduction(candidates, x), -x))


def external_proposal(command, payload, timeout):
    """User-supplied proposer process. No shell; NOT a security sandbox."""
    if not command:
        raise ValueError("external command not configured")
    result = subprocess.run(
        command,
        input=json.dumps(payload, sort_keys=True),
        text=True, capture_output=True,
        timeout=timeout, check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"external proposer exited nonzero ({result.returncode})")
    if len(result.stdout) > 4096:
        raise ValueError("external proposer exceeded output bound")
    response = json.loads(result.stdout, object_pairs_hook=strict_object,
                          parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))
    if type(response) is not dict or set(response) != {"probe"}:
        raise ValueError("proposal must be a JSON object with only 'probe'")
    return response["probe"]


def evaluate(seed, policy, command=None, timeout=15):
    candidates, truth = task(seed)
    active = candidates
    history = []
    used = set()
    rng = random.Random(f"EXP003-P0:random:{seed}")
    status = "COMPLETE"
    failure = None
    for step in range(MAX_STEPS):
        if len(active) == 1:
            break
        context = {
            "protocol": "EXP003-P0", "task_seed": seed, "step": step,
            "domain": list(DOMAIN), "candidate_names": list(active),
            "observations": [{"probe": row["probe"], "outcome": row["outcome"]}
                             for row in history],
            "remaining_budget": MAX_STEPS-step,
            "predicate_definitions": {
                "even": "x % 2 == 0", "multiple3": "x % 3 == 0",
                "multiple5": "x % 5 == 0", "lowhalf": "x < 16",
                "bit1": "(x & 2) != 0", "bit2": "(x & 4) != 0",
                "bit3": "(x & 8) != 0", "mod4eq1": "x % 4 == 1",
            },
        }
        try:
            if policy == "fixed":
                proposal = next(x for x in DOMAIN if x not in used)
            elif policy == "random":
                proposal = rng.choice([x for x in DOMAIN if x not in used])
            elif policy == "greedy":
                proposal = choose_greedy(active, used)
            elif policy == "external":
                proposal = external_proposal(command, context, timeout)
            else:
                raise ValueError("unknown policy")
            if type(proposal) is not int or proposal not in DOMAIN or proposal in used:
                raise ValueError("inadmissible probe: must be unique integer 0..31")
        except (ValueError, StopIteration, subprocess.TimeoutExpired, OSError) as exc:
            status = "DEFERRED"
            failure = type(exc).__name__ + ": " + str(exc)[:180]
            break
        observation = REGISTRY[truth](proposal)
        updated = tuple(name for name in active if REGISTRY[name](proposal) == observation)
        if not updated or truth not in updated:
            raise AssertionError("internal consistency failure")
        history.append({"step": step, "pre": list(active), "probe": proposal,
                        "outcome": observation, "post": list(updated)})
        used.add(proposal)
        active = updated
    return {"seed": seed, "policy": policy, "candidates": list(candidates),
            "truth": truth, "status": status, "failure": failure,
            "records": history, "remaining": list(active), "solved": len(active) == 1}


def study(seeds, policies=("fixed", "random", "greedy"), command=None, timeout=15):
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("nonempty unique seeds required")
    if any(type(s) is not int or not 0 <= s < 1000000 for s in seeds):
        raise ValueError("invalid seed")
    if not policies or any(p not in POLICIES for p in policies) or len(set(policies)) != len(policies):
        raise ValueError("invalid policies")
    results = [evaluate(seed, policy, command=command, timeout=timeout)
               for seed in seeds for policy in policies]
    summary = {}
    for policy in policies:
        rows = [r for r in results if r["policy"] == policy]
        summary[policy] = {
            "solved_rate": sum(r["solved"] for r in rows) / len(rows),
            "mean_remaining": sum(len(r["remaining"]) for r in rows) / len(rows),
            "deferred": sum(r["status"] == "DEFERRED" for r in rows),
        }
    return {"protocol": "EXP003-P0", "evidence_status": "EXPLORATORY_SIMULATED",
            "seeds": seeds, "max_steps": MAX_STEPS, "policies": list(policies),
            "summary": summary, "results": results,
            "limitations": ["synthetic binary predicates", "oracle labels recorded in evidence",
                            "external proposer not sandboxed", "no model benchmark unless external policy configured"]}


def save_fresh(data, destination):
    destination.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = destination / f"exp003-p0-{stamp}-{uuid.uuid4().hex[:8]}.json"
    content = (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with output.open("xb") as handle:
        handle.write(content)
    return output, hashlib.sha256(content).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true", help="authorize exploratory execution")
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--seed-count", type=int, default=12)
    parser.add_argument("--external-command", help="trusted local proposer argv, no shell")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--output-dir", default="evidence/exp003")
    args = parser.parse_args(argv)
    if not args.pilot:
        parser.error("EXPERIMENT DEFERRED: explicit --pilot required")
    if not 1 <= args.seed_count <= 100 or not 0 <= args.seed_start < 1000000 or args.seed_start + args.seed_count > 1000000:
        parser.error("invalid bounded pilot seeds")
    if not 0 < args.timeout <= 60:
        parser.error("invalid timeout")
    policies = ("fixed", "random", "greedy")
    command = None
    if args.external_command:
        command = shlex.split(args.external_command)
        if not command:
            parser.error("empty external command")
        policies += ("external",)
    data = study(list(range(args.seed_start, args.seed_start + args.seed_count)),
                 policies=policies, command=command, timeout=args.timeout)
    path, digest = save_fresh(data, Path(args.output_dir))
    print("EVIDENCE:", path)
    print("SHA256:", digest)
    print("SUMMARY:", json.dumps(data["summary"], sort_keys=True))
    print("STATUS: EXPLORATORY_SIMULATED — NOT VALIDATED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
