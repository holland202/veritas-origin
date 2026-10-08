"""VSC-002: longitudinal budget-matched synthetic learning; public toy research.

No LLM, no human-text corpus, no source-code copy from prior repos.
Simulation oracle is NOT hidden from this Python process. A policy may request
at most eight new oracle labels per generation, including checked labels.
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

PROTOCOL = "VSC-002"
ARMS = ("gold_natural", "gold_balanced", "gold_error", "gold_progress",
        "checked_progress", "mixed_pseudo", "gold_replay", "pseudo_only")
NATURAL = (0.50, 0.25, 0.20, 0.05)
N_BANDS = 4
INITIAL = 8
SELECTION = 16
TEST = 48
CANDIDATES_BAND = 6
QUERIES_GEN = 8
GENERATIONS = 12
LEARNING_RATE = 0.08
INITIAL_PASSES = 4
CHECK_TOLERANCE = 0.30
PSEUDO_NOISE = 0.20
NO_OS_ISOLATION = (
    "PUBLIC TOY SIMULATION; NO LANGUAGE MODEL OR HUMAN-TEXT TRAINING",
    "Reference oracle is a same-process function: no security isolation",
    "All policy tuning uses separate fixed selection data, not final tests",
    "Oracle query budgets are equal across oracle-assisted arms, NOT compute updates",
    "24 public seeds are exploratory, not untouched external confirmation",
    "Measured energy and token cost are unavailable; query/update counts are proxies",
    "Deterministic replay means specification agreement, not worldly truth",
)


def seeded(seed: int, purpose: str) -> random.Random:
    if type(seed) is not int or seed < 0 or seed >= 2**62:
        raise ValueError("seed must be a bounded nonnegative integer")
    bits = hashlib.sha256(f"{PROTOCOL}|{seed}|{purpose}".encode("utf-8")).digest()
    return random.Random(int.from_bytes(bits, "big"))


def oracle(seed: int, band: int, x: float) -> float:
    if type(band) is not int or band not in range(N_BANDS):
        raise ValueError("invalid band")
    drift = (seed % 13 - 6) * 0.01
    if band == 0:
        return 0.14 + 0.77*x - 0.21*x*x + drift
    if band == 1:
        return -0.24 + 0.27*x + 0.70*x*x - drift
    if band == 2:
        return 0.10 - 0.38*x + 0.65*x*x*x + drift
    return 0.12*x + 0.73*math.sin(4*math.pi*x+drift)


def trusted_pool(seed: int, purpose: str, n: int, outer=1.0):
    draw = seeded(seed, purpose)
    return [
        [(x, oracle(seed, b, x))
         for x in (outer*(2*draw.random()-1) for _ in range(n))]
        for b in range(N_BANDS)
    ]


def candidate_pool(seed: int, generation: int):
    draw=seeded(seed, f"candidate:{generation}")
    return [
        {"id": b*CANDIDATES_BAND+j, "band": b, "x": 2*draw.random()-1}
        for b in range(N_BANDS) for j in range(CANDIDATES_BAND)
    ]


class Model:
    def __init__(self):
        self.weights = [[0.0,0.0,0.0] for _ in range(N_BANDS)]

    def predict(self, band, x):
        return sum(w*f for w,f in zip(self.weights[band],(1.0,x,x*x)))

    def update(self, band, x, label):
        error = self.predict(band, x)-label
        for j,f in enumerate((1.0,x,x*x)):
            self.weights[band][j] -= LEARNING_RATE*error*f


def fit_initial(model, initial):
    for _ in range(INITIAL_PASSES):
        for band, entries in enumerate(initial):
            for x,y in entries:
                model.update(band,x,y)


def per_band_mse(model, pairs):
    return [
        sum((model.predict(b,x)-y)**2 for x,y in group)/len(group)
        for b, group in enumerate(pairs)
    ]


def normalize_floor(probs, floor=0.03):
    clamped=[max(floor,v) for v in probs]
    z=sum(clamped)
    return [v/z for v in clamped]


def curriculum(mode, previous_errors, before, after):
    if mode == "gold_balanced":
        return [0.25]*4
    if mode == "gold_error":
        z=sum(previous_errors)
        return normalize_floor([v/z if z else 0.25 for v in previous_errors])
    if mode in ("gold_progress","checked_progress"):
        if before is None or after is None:
            return list(NATURAL)
        improvements=[max(0.0, a-b) for a,b in zip(before,after)]
        total=sum(improvements)
        if total<=0:
            return list(NATURAL)
        return normalize_floor([0.4*NATURAL[b]+0.6*improvements[b]/total
                                for b in range(4)])
    return list(NATURAL)


def pick(pool, mode, weights, seed, generation):
    """Only selects unlabeled candidate identities; no oracle reads."""
    if mode=="gold_balanced":
        return [pool[b*CANDIDATES_BAND+i] for i in range(2) for b in range(4)]
    rng_mode=("natural" if mode in ("gold_natural","mixed_pseudo","gold_replay")
              else "progress" if mode in ("gold_progress","checked_progress")
              else mode)
    draw=seeded(seed,f"pick:{rng_mode}:{generation}")
    available={b:[x for x in pool if x["band"]==b] for b in range(4)}
    chosen=[]
    for _ in range(QUERIES_GEN):
        bands=[b for b in range(4) if available[b]]
        total=sum(weights[b] for b in bands)
        threshold=draw.random()*total
        band=bands[-1]
        for b in bands:
            threshold-=weights[b]
            if threshold<0:
                band=b
                break
        j=draw.randrange(len(available[band]))
        chosen.append(available[band].pop(j))
    return chosen


def bucket(x):
    return max(0,min(7,int((x+1.0)*4)))


def entropy_bands(counters):
    total=sum(counters)
    if not total:
        return None
    return -sum((c/total)*math.log(c/total) for c in counters if c)/math.log(4)


def snapshot(model, id_test, shift_test, oracle_cells, accepted_cells,
             gold_cells, generation, selected, accepted_examples,
             oracle_queries, updates, pseudo_updates, replay_updates, rejected):
    id_mse=per_band_mse(model,id_test)
    shifted=per_band_mse(model,shift_test)
    counts=[0]*4
    for record in accepted_examples:
        counts[record["band"]]+=1
    return {
        "generation":generation,
        "id_mse_by_band":id_mse,
        "id_macro_mse":sum(id_mse)/4,
        "shift_mse_by_band":shifted,
        "shift_macro_mse":sum(shifted)/4,
        "rare_band_mse":id_mse[3],
        "oracle_queried_cell_coverage":len(oracle_cells)/32,
        "accepted_cell_coverage":len(accepted_cells)/32,
        "gold_label_cell_coverage":len(gold_cells)/32,
        "new_accepted_band_entropy":entropy_bands(counts),
        "new_oracle_queries":oracle_queries,
        "selected_rare_fraction": (
            sum(r["band"]==3 for r in selected)/len(selected) if selected else None
        ),
        "new_accepted_examples":len(accepted_examples),
        "updates":updates,
        "pseudolabel_updates":pseudo_updates,
        "replay_updates":replay_updates,
        "rejected":rejected,
    }


def evaluate_arm(seed, mode, initial, selection, id_test, shift_test, n_generations):
    model=Model()
    fit_initial(model,initial)
    initial_cells={(b,bucket(x)) for b,items in enumerate(initial) for x,y in items}
    oracle_cells=set(initial_cells)
    accepted_cells=set(initial_cells)
    gold_cells=set(initial_cells)
    current_selection_error=per_band_mse(model,selection)
    last_before=None
    last_after=None
    history=[snapshot(model,id_test,shift_test,oracle_cells,accepted_cells,
                      gold_cells,0,[],[],0,
                      N_BANDS*INITIAL*INITIAL_PASSES,0,0,0)]
    rounds=[]
    for gen in range(1,n_generations+1):
        pool=candidate_pool(seed,gen)
        chosen=[] if mode=="pseudo_only" else pick(
            pool,mode,curriculum(mode,current_selection_error,last_before,last_after),
            seed,gen
        )
        weights=(curriculum(mode,current_selection_error,last_before,last_after)
                 if mode!="pseudo_only" else None)
        oracle_events=[]
        pseudo_events=[]
        replay_events=[]
        accepted_examples=[]
        verified_rejected=0
        updates=0
        noise=seeded(seed, f"noise:{'checked' if mode=='checked_progress' else mode}:{gen}")
        for selected in chosen:
            b,x=selected["band"],selected["x"]
            true=oracle(seed,b,x)
            oracle_cells.add((b,bucket(x)))
            offered=None
            if mode=="checked_progress":
                offered=model.predict(b,x)+noise.gauss(0,PSEUDO_NOISE)
                accept=abs(offered-true)<=CHECK_TOLERANCE
                if accept:
                    model.update(b,x,offered)
                    updates+=1
                    accepted_examples.append(selected)
                    accepted_cells.add((b,bucket(x)))
                else:
                    verified_rejected+=1
            else:
                accept=True
                model.update(b,x,true)
                accepted_examples.append(selected)
                accepted_cells.add((b,bucket(x)))
                gold_cells.add((b,bucket(x)))
                updates+=1
            oracle_events.append({
                "id":selected["id"],"band":b,"x":x,"oracle_label":true,
                "offered_pseudo":offered,"accepted":accept,
            })

        if mode in ("mixed_pseudo","pseudo_only"):
            chosen_ids={e["id"] for e in chosen}
            other=[sample for sample in pool if sample["id"] not in chosen_ids]
            seeded(seed, f"pseudo_candidate_order:{gen}").shuffle(other)
            if mode=="mixed_pseudo":
                other=other[:16]
            for sample in other:
                b,x=sample["band"],sample["x"]
                proposed=model.predict(b,x)+noise.gauss(0,PSEUDO_NOISE)
                model.update(b,x,proposed)
                pseudo_events.append({
                    "id":sample["id"],"band":b,"x":x,"pseudo_label":proposed
                })
                accepted_cells.add((b,bucket(x)))
                updates+=1
        if mode=="gold_replay":
            draw=seeded(seed,f"replay:{gen}")
            for _ in range(16):
                b=draw.randrange(4)
                i=draw.randrange(INITIAL)
                x,y=initial[b][i]
                model.update(b,x,y)
                replay_events.append({"band":b,"initial_index":i,"x":x,"label":y})
                updates+=1

        after_selection=per_band_mse(model,selection)
        rounds.append({
            "generation":gen,
            "allocation_weights":weights,
            "candidate_pool":pool,
            "oracle_events":oracle_events,
            "pseudo_events":pseudo_events,
            "replay_events":replay_events,
            "selection_errors_before":current_selection_error,
            "selection_errors_after":after_selection,
        })
        history.append(snapshot(
            model,id_test,shift_test,oracle_cells,accepted_cells,gold_cells,
            gen,chosen,accepted_examples,len(chosen),updates,
            len(pseudo_events),len(replay_events),verified_rejected,
        ))
        last_before=current_selection_error
        last_after=after_selection
        current_selection_error=after_selection
    totals={
        "new_oracle_queries":sum(x["new_oracle_queries"] for x in history[1:]),
        "updates":sum(x["updates"] for x in history[1:]),
        "pseudolabel_updates":sum(x["pseudolabel_updates"] for x in history[1:]),
        "replay_updates":sum(x["replay_updates"] for x in history[1:]),
        "rejected":sum(x["rejected"] for x in history[1:]),
        "fixed_reference_labels_shared":32+64+192+192,
    }
    return {"mode":mode,"history":history,"rounds":rounds,
            "totals":totals,"weights_final":model.weights}


def evaluate_seed(seed,n_generations):
    initial=trusted_pool(seed,"initial",INITIAL)
    selection=trusted_pool(seed,"selection",SELECTION)
    id_test=trusted_pool(seed,"id_test",TEST)
    shift_test=trusted_pool(seed,"shift_test",TEST,outer=1.45)
    return {"seed":seed,"arms":[
        evaluate_arm(seed,mode,initial,selection,id_test,shift_test,n_generations)
        for mode in ARMS
    ]}


def averages(runs,n_generations):
    out={}
    metrics=("id_macro_mse","shift_macro_mse","rare_band_mse",
             "oracle_queried_cell_coverage","accepted_cell_coverage",
             "gold_label_cell_coverage")
    for mode in ARMS:
        arm_rows=[next(a for a in run["arms"] if a["mode"]==mode) for run in runs]
        means={
            k:[sum(a["history"][g][k] for a in arm_rows)/len(arm_rows)
               for g in range(n_generations+1)]
            for k in metrics
        }
        totals={
            k:sum(a["totals"][k] for a in arm_rows)/len(arm_rows)
            for k in ("new_oracle_queries","updates","pseudolabel_updates",
                      "replay_updates","rejected")
        }
        out[mode]={"curves":means,"mean_totals":totals,
                   "per_seed_final_id_mse":[a["history"][-1]["id_macro_mse"]
                                            for a in arm_rows],
                   "per_seed_final_shift_mse":[a["history"][-1]["shift_macro_mse"]
                                               for a in arm_rows]}
    return out


def study(seed_base=20261009,n_seeds=24,n_generations=GENERATIONS,public=True):
    if type(seed_base) is not int or not 0<=seed_base<2**62-100:
        raise ValueError("seed_base out of bounds")
    if type(n_seeds) is not int or not 1<=n_seeds<=24:
        raise ValueError("n_seeds must be 1..24")
    if type(n_generations) is not int or not 1<=n_generations<=GENERATIONS:
        raise ValueError("generations must be 1..12")
    runs=[evaluate_seed(seed_base+i,n_generations) for i in range(n_seeds)]
    return {
        "protocol":PROTOCOL,
        "evidence_status":"PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED",
        "seed_origin":"PUBLIC_TEST_SEED" if public else "REVEALED_AFTER_PILOT",
        "seed_base":seed_base,"seeds":n_seeds,"generations":n_generations,
        "arms_order":list(ARMS),
        "configuration":{
            "initial_per_band":INITIAL,"selection_per_band":SELECTION,
            "test_per_band":TEST,"candidates_per_band":CANDIDATES_BAND,
            "oracle_queries_per_generation":QUERIES_GEN,
            "learning_rate":LEARNING_RATE,"initial_passes":INITIAL_PASSES,
            "check_tolerance":CHECK_TOLERANCE,"pseudo_noise":PSEUDO_NOISE,
            "natural_band_probabilities":list(NATURAL),
            "shift_test_x_multiplier":1.45,
        },
        "runs":runs,
        "summary":averages(runs,n_generations),
        "limitations":list(NO_OS_ISOLATION),
    }


def save_fresh(obj,directory):
    directory.mkdir(parents=True,exist_ok=True)
    basename=("vsc002-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+
              "-"+uuid.uuid4().hex[:10]+".json")
    target=directory/basename
    raw=(json.dumps(obj,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()
    with target.open("xb") as file:
        file.write(raw)
    return target,hashlib.sha256(raw).hexdigest()


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",action="store_true",help="required explicit opt-in")
    p.add_argument("--seed-base",type=int,default=20261009)
    p.add_argument("--seeds",type=int,default=24)
    p.add_argument("--generations",type=int,default=GENERATIONS)
    p.add_argument("--output-dir",default="evidence/vsc002")
    a=p.parse_args(argv)
    if not a.pilot:
        p.error("HALT: explicit --pilot required")
    try:
        result=study(a.seed_base,a.seeds,a.generations)
        filepath,digest=save_fresh(result,Path(a.output_dir))
    except (ValueError,OSError) as e:
        p.error("HALT: "+str(e))
    print("EVIDENCE:",filepath)
    print("SHA256:",digest)
    for mode,record in result["summary"].items():
        print("POLICY:",mode,
              "FINAL_ID_MSE:",round(record["curves"]["id_macro_mse"][-1],8),
              "FINAL_SHIFT_MSE:",round(record["curves"]["shift_macro_mse"][-1],8),
              "FINAL_RARE_MSE:",round(record["curves"]["rare_band_mse"][-1],8),
              "ORACLE:",record["mean_totals"]["new_oracle_queries"],
              "UPDATES:",record["mean_totals"]["updates"],
              "REJECTED:",record["mean_totals"]["rejected"])
    print("STATUS: PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED")
    return 0


if __name__=="__main__":
    sys.exit(main())
