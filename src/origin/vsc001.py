"""VSC-001: exploratory, simulator-grounded synthetic curriculum study.

Stdlib only. Synthetic scalar domain, polynomial student, no LLM, no claims
of general intelligence or resistance to real-world model collapse.
This file is independent of QUASAR and Coverage-Preserving Synthesis source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import secrets
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL = "VSC-001"
MODES = (
    "oracle_natural", "oracle_balanced", "noisy_natural",
    "verified_natural", "verified_progress", "recursive_natural",
)
NATURAL = (0.50, 0.25, 0.15, 0.10)
N_BANDS = 4
INITIAL_PER_BAND = 8
SELECT_PER_BAND = 16
CONFORMAL_PER_BAND = 32
TEST_PER_BAND = 64
CORRUPTION_RATE = 0.22
CORRUPTION_SIZE = 1.8
PSEUDO_NOISE = 0.18
LEARNING_RATE = 0.10
SEED_EPOCHS = 4
CONFIDENCE = 0.90
LIMITS = [
    "EXPLORATORY_SIMULATED; not a human text data study",
    "Simulated oracle computed in the same process; OS isolation untested",
    "Verifier invokes privileged oracle; its call cost is explicitly counted",
    "No large language model, no real-world sensor, no production action",
    "Synthetic task family and code are public; do not reuse as blind benchmark",
    "Predictive coverage is descriptive, not guaranteed under distribution shift",
    "No equal oracle budget between policies; report counts and direct-oracle controls",
]


def rng(seed: int, domain: str) -> random.Random:
    if type(seed) is not int or seed < 0 or seed > 2**63:
        raise ValueError("seed out of bounds")
    digest = hashlib.sha256(f"{PROTOCOL}|{seed}|{domain}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def teacher(seed: int, band: int, x: float) -> float:
    """Mathematical reference; not accessible to a deployed real-model agent."""
    if type(band) is not int or band not in range(N_BANDS):
        raise ValueError("invalid band")
    shift = (seed % 11 - 5) * 0.012
    if band == 0:
        return 0.18 + 0.80*x - 0.25*x*x + shift
    if band == 1:
        return -0.28 + 0.32*x + 0.73*x*x - shift
    if band == 2:
        return 0.16 - 0.30*x + 0.65*x*x*x + shift
    return 0.15*x + 0.68*math.sin(4*math.pi*x + shift)


def features(x: float) -> tuple[float, float, float]:
    return (1.0, x, x*x)


class Student:
    def __init__(self):
        self.w = [[0.0, 0.0, 0.0] for _ in range(N_BANDS)]

    def predict(self, band: int, x: float) -> float:
        return sum(a*b for a, b in zip(self.w[band], features(x)))

    def learn(self, band: int, x: float, label: float) -> None:
        error = self.predict(band, x) - label
        for j, feat in enumerate(features(x)):
            self.w[band][j] -= LEARNING_RATE * error * feat


def pool(seed: int, domain: str, per_band: int) -> list[list[tuple[float, float]]]:
    randomizer = rng(seed, domain)
    return [
        [(x, teacher(seed, b, x))
         for x in (2.0*randomizer.random()-1.0 for _ in range(per_band))]
        for b in range(N_BANDS)
    ]


def errors(student: Student, dataset: list[list[tuple[float, float]]]) -> list[float]:
    return [
        sum((student.predict(b, x)-y)**2 for x, y in group)/len(group)
        for b, group in enumerate(dataset)
    ]


def choose(randomizer: random.Random, weights: list[float] | tuple[float, ...]) -> int:
    q = randomizer.random()*sum(weights)
    for b, w in enumerate(weights):
        q -= w
        if q < 0.0:
            return b
    return N_BANDS-1


def progress_weights(before: list[float], after: list[float]) -> list[float]:
    """POSITIVE observed reduction only. Worsening cannot count as progress."""
    delta = [max(0.0, a-b) for a, b in zip(before, after)]
    total = sum(delta)
    if total <= 0.0:
        return list(NATURAL)
    return [0.4*prior + 0.6*d/total for prior, d in zip(NATURAL, delta)]


def conformal(student: Student, calibration, testing):
    results = []
    for band in range(N_BANDS):
        residuals = sorted(abs(y-student.predict(band,x))
                           for x,y in calibration[band])
        k = min(math.ceil((len(residuals)+1)*CONFIDENCE), len(residuals))-1
        q = residuals[k]
        included = sum(abs(y-student.predict(band,x)) <= q for x,y in testing[band])
        results.append({"coverage": included/len(testing[band]),
                        "width": 2*q, "q": q})
    return results


def run_arm(seed, mode, initial, selection, calibration, testing,
            rounds: int, candidates_per_round: int):
    if mode not in MODES:
        raise ValueError("unknown mode")
    student = Student()
    for _ in range(SEED_EPOCHS):
        for band, group in enumerate(initial):
            for x,y in group:
                student.learn(band,x,y)
    initial_test = errors(student, testing)
    before = errors(student, selection)
    randomizer = rng(seed, "balanced" if mode=="oracle_balanced"
                     else "adaptive" if mode=="verified_progress" else "natural")
    defects = rng(seed, "adaptive_corruption" if mode=="verified_progress"
                  else "natural_corruption")
    pseudo = rng(seed, "recursive_pseudo")
    weights = list((0.25,)*4 if mode == "oracle_balanced" else NATURAL)
    history, events = [], []
    accepted = rejected = false_admitted = 0
    # Initial and three separately frozen evaluation partitions are shared
    # across all policies; count the initial oracle labels only in this cost
    # metric. Report non-training evaluation oracle calls separately.
    train_oracle_calls = INITIAL_PER_BAND*N_BANDS
    for round_index in range(rounds):
        used_weights = list(weights)
        n_good = n_bad = 0
        for candidate_index in range(candidates_per_round):
            band = choose(randomizer, used_weights)
            x = 2.0*randomizer.random()-1.0
            reference = None
            oracle_cost = 0
            injected = False
            if mode == "recursive_natural":
                offered = student.predict(band,x) + pseudo.gauss(0.0,PSEUDO_NOISE)
                admitted = True
            else:
                reference = teacher(seed,band,x)
                oracle_cost = 1  # generator / direct-oracle ground-truth access
                if mode.startswith(("noisy_", "verified_")):
                    injected = defects.random() < CORRUPTION_RATE
                    if injected:
                        offered = reference + (CORRUPTION_SIZE if defects.random()<0.5
                                               else -CORRUPTION_SIZE)
                    else:
                        offered = reference
                else:
                    offered = reference
                if mode.startswith("verified_"):
                    independently_measured = teacher(seed,band,x)
                    oracle_cost += 1  # independently measured comparison
                    admitted = abs(offered-independently_measured) <= 1e-9
                else:
                    admitted = True
            train_oracle_calls += oracle_cost
            if admitted:
                student.learn(band,x,offered)
                accepted += 1
                n_good += 1
                if injected:
                    false_admitted += 1
            else:
                rejected += 1
                n_bad += 1
            events.append({
                "round": round_index, "candidate": candidate_index,
                "band": band, "x": x, "offered": offered,
                "reference": reference, "injected": injected,
                "accepted": admitted, "oracle_calls": oracle_cost,
            })
        after = errors(student, selection)
        history.append({
            "round": round_index, "weights": used_weights,
            "selection_mse_by_band": after,
            "accepted": n_good, "rejected": n_bad,
        })
        if mode=="verified_progress":
            weights = progress_weights(before,after)
        before = after

    last_test = errors(student,testing)  # test set used only for final reporting
    conf = conformal(student,calibration,testing)  # separate conformal calibration
    return {
        "mode": mode,
        "initial_test_mse_by_band": initial_test,
        "final_test_mse_by_band": last_test,
        "initial_test_macro_mse": sum(initial_test)/N_BANDS,
        "final_test_macro_mse": sum(last_test)/N_BANDS,
        "improvement": (sum(initial_test)-sum(last_test))/N_BANDS,
        "conformal_by_band": conf,
        "macro_coverage": sum(v["coverage"] for v in conf)/N_BANDS,
        "mean_interval_width": sum(v["width"] for v in conf)/N_BANDS,
        "train_oracle_calls": train_oracle_calls,
        "selection_reference_labels": SELECT_PER_BAND*N_BANDS,
        "selection_score_comparisons": SELECT_PER_BAND*N_BANDS*(rounds+1),
        "conformal_and_test_reference_labels": N_BANDS*(CONFORMAL_PER_BAND+TEST_PER_BAND),
        "total_allocated_oracle_calls": (train_oracle_calls + SELECT_PER_BAND*N_BANDS
                                         + N_BANDS*(CONFORMAL_PER_BAND+TEST_PER_BAND)),
        "accepted": accepted, "rejected": rejected,
        "false_labels_admitted": false_admitted,
        "history": history, "events": events,
        "weights_final": student.w,
    }


def run_seed(seed, rounds, candidates_per_round):
    initial = pool(seed, "initial", INITIAL_PER_BAND)
    selection = pool(seed, "selection", SELECT_PER_BAND)
    calibration = pool(seed, "conformal", CONFORMAL_PER_BAND)
    testing = pool(seed, "test", TEST_PER_BAND)
    return {
        "seed": seed,
        "arms": [
            run_arm(seed, mode, initial, selection, calibration, testing,
                    rounds, candidates_per_round)
            for mode in MODES
        ],
    }


def summarize(runs):
    result = {}
    n = len(runs)
    for mode in MODES:
        arms = [next(a for a in row["arms"] if a["mode"] == mode) for row in runs]
        fields = ("final_test_macro_mse", "improvement", "macro_coverage",
                  "mean_interval_width", "train_oracle_calls",
                  "total_allocated_oracle_calls", "accepted",
                  "rejected", "false_labels_admitted")
        result[mode] = {name:sum(a[name] for a in arms)/n for name in fields}
        result[mode]["per_seed_mse"] = [a["final_test_macro_mse"] for a in arms]
    return result


def study(seed_base, n_seeds=3, rounds=10, candidates_per_round=24,
          public_test_seed=False):
    if type(seed_base) is not int or not (0 <= seed_base < 2**63 - 10):
        raise ValueError("seed base invalid")
    if type(n_seeds) is not int or not (1 <= n_seeds <= 8):
        raise ValueError("seed count must be 1..8")
    if type(rounds) is not int or not (1 <= rounds <= 20):
        raise ValueError("rounds must be 1..20")
    if type(candidates_per_round) is not int or not (1 <= candidates_per_round <= 50):
        raise ValueError("candidates per round must be 1..50")
    runs = [run_seed(seed_base+i,rounds,candidates_per_round)
            for i in range(n_seeds)]
    return {
        "protocol": PROTOCOL,
        "status": "EXPLORATORY_SIMULATED_NOT_VALIDATED",
        "seed_origin": "PUBLIC_TEST_SEED" if public_test_seed else "REVEALED_AFTER_RUN",
        "seed_base": seed_base, "n_seeds": n_seeds,
        "rounds": rounds, "candidates_per_round": candidates_per_round,
        "mode_order": list(MODES),
        "constants": {
            "initial_per_band": INITIAL_PER_BAND,
            "selection_per_band": SELECT_PER_BAND,
            "conformal_per_band": CONFORMAL_PER_BAND,
            "test_per_band": TEST_PER_BAND,
            "corruption_rate": CORRUPTION_RATE,
            "corruption_size": CORRUPTION_SIZE,
            "pseudo_noise": PSEUDO_NOISE, "learning_rate": LEARNING_RATE,
            "seed_epochs": SEED_EPOCHS, "nominal_coverage": CONFIDENCE,
            "natural_weights": list(NATURAL),
        },
        "runs": runs, "summary": summarize(runs), "limitations": list(LIMITS),
    }


def save_new(data, output_dir):
    output_dir.mkdir(parents=True,exist_ok=True)
    path = output_dir/("vsc001-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                       +"-"+uuid.uuid4().hex[:10]+".json")
    raw = (json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    with path.open("xb") as f:
        f.write(raw)
    return path,hashlib.sha256(raw).hexdigest()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot", action="store_true")
    p.add_argument("--seeds",type=int,default=3)
    p.add_argument("--rounds",type=int,default=10)
    p.add_argument("--candidates-per-round",type=int,default=24)
    p.add_argument("--test-seed-base",type=int)
    p.add_argument("--allow-public-test-seed",action="store_true")
    p.add_argument("--output-dir",default="evidence/vsc001")
    a = p.parse_args(argv)
    if not a.pilot:
        p.error("HALT: --pilot required")
    if (a.test_seed_base is None) != (not a.allow_public_test_seed):
        p.error("HALT: --test-seed-base requires --allow-public-test-seed (and vice versa)")
    try:
        base = a.test_seed_base if a.test_seed_base is not None else secrets.randbits(62)
        data = study(base,a.seeds,a.rounds,a.candidates_per_round,
                     public_test_seed=a.allow_public_test_seed)
        path,digest = save_new(data,Path(a.output_dir))
    except (ValueError,OSError) as e:
        p.error("HALT: "+str(e))
    print("EVIDENCE:",path)
    print("SHA256:",digest)
    print("SUMMARY:",json.dumps(data["summary"],sort_keys=True))
    print("STATUS: EXPLORATORY_SIMULATED — NOT VALIDATED")
    print("LIMITATION: privileged simulation oracle, not a language-model experiment")
    return 0


if __name__=="__main__":
    sys.exit(main())
