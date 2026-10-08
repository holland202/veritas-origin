"""VSC-003: toy costed weak-verification and synthetic-learning experiment.

Public exploration only; not a language model, novel active-learning claim,
or a genuinely isolated oracle. Never import prior prototype code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL = "VSC-003"
ARMS = (
    "gold_natural", "gold_balanced", "gold_error", "gold_progress",
    "checked_natural", "checked_balanced", "checked_progress",
    "hybrid_progress", "gold_plus_pseudo", "gold_replay", "pseudo_only",
)
NATURAL = (0.50, 0.25, 0.20, 0.05)
INITIAL_PER_BAND = 8
SELECT_PER_BAND = 16
TEST_PER_BAND = 48
CANDIDATES_PER_BAND = 6
GEN_CREDITS = 12
STRONG_COST = 6
WEAK_COST = 1
GENERATIONS = 10
STUDENT_RATE = 0.08
INITIAL_EPOCHS = 4
TOLERANCE = 0.30
FLIP_RATE = 0.08
PROPOSAL_NOISE = 0.25
OUTLIER_RATE = 0.15
OUTLIER_SIZE = 1.0
LIMITATIONS = (
    "PUBLIC SYNTHETIC NUMERICAL STUDY, NOT LANGUAGE-MODEL TRAINING",
    "Reference and cheap checker are co-resident Python functions; oracle isolation NOT TESTED",
    "Binary cheap-check feedback leaks a bit but never supplies a true numerical label to the student",
    "Ground-truth labels are recorded in evidence for post-run audit, not fed to weak-only policies",
    "Shared initial, selection, and test oracle labels are counted separately from acquisition credits",
    "No energy, actual money, pretrained language model, real human-data, or external-domain evaluation",
    "Novelty and production reliability NOT ESTABLISHED",
)


def stream(seed: int, key: str) -> random.Random:
    if type(seed) is not int or not 0 <= seed < 2**62:
        raise ValueError("seed invalid")
    data = hashlib.sha256(f"{PROTOCOL}:{seed}:{key}".encode()).digest()
    return random.Random(int.from_bytes(data, "big"))


def truth(seed: int, band: int, x: float) -> float:
    if type(band) is not int or not 0 <= band <= 3:
        raise ValueError("band invalid")
    shift = (seed % 17 - 8) * 0.008
    if band == 0:
        return 0.2 + 0.70*x - 0.18*x*x + shift
    if band == 1:
        return -0.14 + 0.31*x + 0.67*x*x - shift
    if band == 2:
        return 0.08 - 0.36*x + 0.55*x*x*x + shift
    return 0.1*x + 0.72*math.sin(4*math.pi*x + shift)


def fixed_pool(seed: int, key: str, count: int, scale: float = 1.0):
    r = stream(seed, key)
    return [[(x, truth(seed, b, x))
             for x in (scale*(2*r.random()-1) for _ in range(count))]
            for b in range(4)]


def proposed_pool(seed: int, generation: int):
    r = stream(seed, f"candidates:{generation}")
    return [{"id": b*6+j, "band": b, "x": 2*r.random()-1}
            for b in range(4) for j in range(6)]


def bin_id(x: float):
    return max(0, min(7, int((x+1)*4)))


class Student:
    def __init__(self):
        self.w = [[0., 0., 0.] for _ in range(4)]

    def predict(self, band, x):
        return sum(a*b for a, b in zip(self.w[band], (1.,x,x*x)))

    def train(self, band, x, y):
        err = self.predict(band,x)-y
        for j,z in enumerate((1.,x,x*x)):
            self.w[band][j] -= STUDENT_RATE*err*z


def mses(student, dataset):
    return [sum((student.predict(b,x)-y)**2 for x,y in group)/len(group)
            for b, group in enumerate(dataset)]


def weights(policy, selection_error, old, new):
    if policy in ("gold_balanced", "checked_balanced"):
        return [0.25]*4
    if policy == "gold_error":
        total = sum(selection_error)
        raw = [z/total if total>0 else 0.25 for z in selection_error]
    elif policy in ("gold_progress","checked_progress","hybrid_progress"):
        gains = ([max(0.,a-b) for a,b in zip(old,new)]
                 if old is not None and new is not None else [0.]*4)
        total = sum(gains)
        raw = ([0.4*NATURAL[b]+0.6*gains[b]/total for b in range(4)]
               if total>0 else list(NATURAL))
    else:
        raw = list(NATURAL)
    adjusted = [max(0.03,v) for v in raw]
    return [z/sum(adjusted) for z in adjusted]


def choose(pool, policy, weight, seed, gen, n):
    """Exactly n distinct unlabeled candidate IDs selected without ground truth."""
    if policy=="gold_balanced":
        # Rotation offers all bands equal opportunities across generations.
        bands = [((gen-1)%4), ((gen+1)%4)]
        return [pool[b*6+(gen-1)%6] for b in bands]
    if policy=="checked_balanced":
        return [pool[b*6+j] for j in range(3) for b in range(4)]
    sampler = ("natural" if policy in
               ("gold_natural","checked_natural","gold_plus_pseudo","gold_replay","pseudo_only")
               else "progress" if policy in ("gold_progress","checked_progress","hybrid_progress")
               else policy)
    r=stream(seed,f"selection:{sampler}:{gen}")
    bins={b:[c for c in pool if c["band"]==b] for b in range(4)}
    chosen=[]
    for _ in range(n):
        active=[b for b in range(4) if bins[b]]
        total=sum(weight[b] for b in active)
        v=r.random()*total
        b=active[-1]
        for candidate_band in active:
            v-=weight[candidate_band]
            if v<0:
                b=candidate_band
                break
        ix=r.randrange(len(bins[b]))
        chosen.append(bins[b].pop(ix))
    return chosen


def synth_label(model, row, seed, gen):
    b,x,j=row["band"],row["x"],row["id"]
    r=stream(seed,f"proposal:{gen}:{j}")
    candidate=model.predict(b,x)+r.gauss(0.,PROPOSAL_NOISE)
    outlier=r.random()<OUTLIER_RATE
    if outlier:
        candidate += OUTLIER_SIZE*(1 if r.random()<0.5 else -1)
    return candidate, outlier


def cheap_check(seed, gen, row, proposed):
    """Returns a Boolean only. Any true y below is evaluator-only state."""
    correct=abs(proposed-truth(seed,row["band"],row["x"]))<=TOLERANCE
    noisy=stream(seed,f"weak_flip:{gen}:{row['id']}").random()<FLIP_RATE
    return (not correct if noisy else correct),correct,noisy


def new_snapshot(student,id_test,shift_test,cells_queried,cells_accepted,
                 cells_gold,gen,counts,credit,updates,strong,weak,accepted,rejected,
                 false_accept,false_reject,pseudo,replays,queried_bands):
    id_mse=mses(student,id_test)
    shift_mse=mses(student,shift_test)
    return {
        "generation":gen,
        "in_domain_mse_by_band":id_mse,
        "in_domain_macro_mse":sum(id_mse)/4,
        "shift_mse_by_band":shift_mse,
        "shift_macro_mse":sum(shift_mse)/4,
        "rare_band_mse":id_mse[3],
        "queried_cell_coverage":len(cells_queried)/32,
        "accepted_cell_coverage":len(cells_accepted)/32,
        "gold_cell_coverage":len(cells_gold)/32,
        "credits_spent":credit,
        "credits_unused":GEN_CREDITS-credit if gen else 0,
        "strong_queries":strong,
        "weak_queries":weak,
        "student_updates":updates,
        "weak_accepted":accepted,
        "weak_rejected":rejected,
        "false_accept":false_accept,
        "false_reject":false_reject,
        "pseudolabel_updates":pseudo,
        "anchor_replays":replays,
        "queried_rare_count":sum(b==3 for b in queried_bands),
        "queried_band_counts":[sum(b==k for b in queried_bands) for k in range(4)],
    }


def train_arm(seed,policy,initial,selection,id_test,shift_test,generations):
    model=Student()
    for _ in range(INITIAL_EPOCHS):
        for b,group in enumerate(initial):
            for x,y in group:
                model.train(b,x,y)
    start_cells={(b,bin_id(x)) for b,group in enumerate(initial) for x,y in group}
    queried=set(start_cells)
    accepted=set(start_cells)
    gold=set(start_cells)
    recent=mses(model,selection)
    previous=None
    current=None
    history=[new_snapshot(model,id_test,shift_test,queried,accepted,gold,0,
                          None,0,INITIAL_EPOCHS*4*INITIAL_PER_BAND,
                          0,0,0,0,0,0,0,0,[])]
    rounds=[]
    for gen in range(1,generations+1):
        pool=proposed_pool(seed,gen)
        allocation=weights(policy,recent,previous,current)
        if policy.startswith("gold_") or policy=="gold_plus_pseudo":
            selected=choose(pool,policy,allocation,seed,gen,2)
            strong_ids={item["id"] for item in selected}
            weak_ids=set()
        elif policy=="hybrid_progress":
            selected=choose(pool,policy,allocation,seed,gen,7)
            strong_ids={selected[0]["id"]}
            weak_ids={item["id"] for item in selected[1:]}
        elif policy=="pseudo_only":
            selected=choose(pool,policy,allocation,seed,gen,12)
            strong_ids=set()
            weak_ids=set()
        else:
            selected=choose(pool,policy,allocation,seed,gen,12)
            strong_ids=set()
            weak_ids={item["id"] for item in selected}
        events=[]
        replay_events=[]
        strong_count=weak_count=weak_accepted=weak_rejected=0
        false_accept=false_reject=0
        pseudo_updates=0
        updates=0
        bands=[]
        for item in selected:
            b,x=item["band"],item["x"]
            idx=(b,bin_id(x))
            offered,outlier=synth_label(model,item,seed,gen)
            if item["id"] in strong_ids:
                # In a real isolated service a numeric label is returned.
                y=truth(seed,b,x)
                model.train(b,x,y)
                gold.add(idx)
                accepted.add(idx)
                queried.add(idx)
                bands.append(b)
                kind="STRONG_GOLD"
                weak_result=None
                truth_acceptable=None
                flipped=None
                training_label=y
                strong_count+=1
                updates+=1
            elif item["id"] in weak_ids:
                # The learner receives ONLY feedback bool, not the y below.
                weak_result,truth_acceptable,flipped=cheap_check(
                    seed,gen,item,offered)
                actual=truth(seed,b,x)  # evaluator-only audit receipt
                kind="WEAK_ACCEPTED_PSEUDO" if weak_result else "WEAK_REFUSED"
                training_label=offered if weak_result else None
                queried.add(idx)
                bands.append(b)
                weak_count+=1
                if weak_result:
                    model.train(b,x,offered)
                    accepted.add(idx)
                    weak_accepted+=1
                    pseudo_updates+=1
                    updates+=1
                else:
                    weak_rejected+=1
                if weak_result and not truth_acceptable:
                    false_accept+=1
                elif not weak_result and truth_acceptable:
                    false_reject+=1
                y=actual
            else:
                kind="UNVERIFIED_PSEUDO"
                y=None
                weak_result=None
                truth_acceptable=None
                flipped=None
                model.train(b,x,offered)
                training_label=offered
                accepted.add(idx)
                pseudo_updates+=1
                updates+=1
            events.append({
                "id":item["id"],"band":b,"x":x,
                "kind":kind,"proposed_label":offered,
                "outlier_injected":outlier,
                "evaluator_true_label":y,
                "truth_acceptable":truth_acceptable,
                "feedback_flipped":flipped,
                "weak_boolean":weak_result,
                "training_label":training_label,
            })
        if policy in ("gold_plus_pseudo","gold_replay"):
            if policy=="gold_plus_pseudo":
                selected_ids={row["id"] for row in selected}
                remain=[item for item in pool if item["id"] not in selected_ids]
                stream(seed,f"extra_sample:{gen}").shuffle(remain)
                for row in remain[:10]:
                    proposal,outlier=synth_label(model,row,seed,gen)
                    model.train(row["band"],row["x"],proposal)
                    accepted.add((row["band"],bin_id(row["x"])))
                    updates+=1
                    pseudo_updates+=1
                    replay_events.append({
                        "kind":"UNVERIFIED_EXTRA","id":row["id"],
                        "band":row["band"],"x":row["x"],
                        "proposed_label":proposal,"outlier_injected":outlier,
                    })
            else:
                replay=stream(seed,f"anchor_replay:{gen}")
                for _ in range(10):
                    band=replay.randrange(4)
                    i=replay.randrange(INITIAL_PER_BAND)
                    x,y=initial[band][i]
                    model.train(band,x,y)
                    updates+=1
                    replay_events.append({"kind":"TRUSTED_ANCHOR_REPLAY",
                                          "band":band,"initial_index":i,
                                          "x":x,"true_label":y})
        spent=STRONG_COST*strong_count+WEAK_COST*weak_count
        if spent>GEN_CREDITS:
            raise AssertionError("credit budget exceeded")
        new_error=mses(model,selection)
        rounds.append({
            "generation":gen,"weights":allocation,
            "candidate_pool":pool,"events":events,"extra_events":replay_events,
            "selection_before":recent,"selection_after":new_error
        })
        history.append(new_snapshot(
            model,id_test,shift_test,queried,accepted,gold,gen,None,
            spent,updates,strong_count,weak_count,weak_accepted,weak_rejected,
            false_accept,false_reject,pseudo_updates,len(replay_events)
            if policy=="gold_replay" else 0,bands
        ))
        previous=recent
        current=new_error
        recent=new_error
    fields=("credits_spent","credits_unused","strong_queries","weak_queries",
            "student_updates","weak_accepted","weak_rejected","false_accept",
            "false_reject","pseudolabel_updates","anchor_replays",
            "queried_rare_count")
    totals={key:sum(state[key] for state in history[1:]) for key in fields}
    totals["shared_reference_labels"]=32+64+48*4*2
    return {"policy":policy,"history":history,"rounds":rounds,
            "totals":totals,"final_weights":model.w}


def study_seed(seed,generations):
    initial=fixed_pool(seed,"initial",INITIAL_PER_BAND)
    selection=fixed_pool(seed,"selection",SELECT_PER_BAND)
    final=fixed_pool(seed,"test",TEST_PER_BAND)
    shift=fixed_pool(seed,"shift",TEST_PER_BAND,scale=1.40)
    return {"seed":seed,"policies":[train_arm(seed,mode,initial,selection,final,shift,
                                              generations) for mode in ARMS]}


def summarize(runs,generations):
    metrics=("in_domain_macro_mse","shift_macro_mse","rare_band_mse",
             "queried_cell_coverage","accepted_cell_coverage",
             "gold_cell_coverage")
    totals=("credits_spent","credits_unused","strong_queries","weak_queries",
            "student_updates","weak_accepted","weak_rejected","false_accept",
            "false_reject","pseudolabel_updates","anchor_replays",
            "queried_rare_count")
    result={}
    for policy in ARMS:
        rows=[next(x for x in run["policies"] if x["policy"]==policy) for run in runs]
        result[policy]={
            "curves":{key:[sum(a["history"][t][key] for a in rows)/len(rows)
                          for t in range(generations+1)] for key in metrics},
            "mean_totals":{key:sum(a["totals"][key] for a in rows)/len(rows)
                           for key in totals},
            "per_seed_final_id_mse":[a["history"][-1]["in_domain_macro_mse"]
                                      for a in rows],
            "per_seed_final_rare_mse":[a["history"][-1]["rare_band_mse"]
                                        for a in rows],
            "per_seed_final_shift_mse":[a["history"][-1]["shift_macro_mse"]
                                         for a in rows],
        }
    return result


def study(first=20261033,seeds=24,generations=GENERATIONS):
    if type(first) is not int or not 0<=first<2**62-100:
        raise ValueError("seed base invalid")
    if type(seeds) is not int or not 1<=seeds<=24:
        raise ValueError("seeds outside 1..24")
    if type(generations) is not int or not 1<=generations<=GENERATIONS:
        raise ValueError("generations outside 1..10")
    runs=[study_seed(first+i,generations) for i in range(seeds)]
    return {
        "protocol":PROTOCOL,"status":"PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED",
        "seed_base":first,"n_seeds":seeds,"generations":generations,
        "arms":list(ARMS),
        "constants":{
            "natural":list(NATURAL),"initial_per_band":INITIAL_PER_BAND,
            "selection_per_band":SELECT_PER_BAND,"test_per_band":TEST_PER_BAND,
            "candidates_per_band":CANDIDATES_PER_BAND,"gen_credits":GEN_CREDITS,
            "strong_cost":STRONG_COST,"weak_cost":WEAK_COST,
            "student_rate":STUDENT_RATE,"initial_epochs":INITIAL_EPOCHS,
            "tolerance":TOLERANCE,"flip_rate":FLIP_RATE,
            "proposal_noise":PROPOSAL_NOISE,"outlier_rate":OUTLIER_RATE,
            "outlier_size":OUTLIER_SIZE,"shift_multiplier":1.4,
        },
        "runs":runs,"summary":summarize(runs,generations),
        "limitations":list(LIMITATIONS),
    }


def save_new(value, directory):
    directory.mkdir(parents=True,exist_ok=True)
    name="vsc003-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+uuid.uuid4().hex[:10]+".json"
    destination=directory/name
    content=(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    with destination.open("xb") as handle:
        handle.write(content)
    return destination,hashlib.sha256(content).hexdigest()


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--seed-base",type=int,default=20261033)
    p.add_argument("--seeds",type=int,default=24)
    p.add_argument("--generations",type=int,default=GENERATIONS)
    p.add_argument("--output-dir",default="evidence/vsc003")
    args=p.parse_args(argv)
    if not args.pilot:
        p.error("HALT: --pilot explicit opt-in required")
    try:
        obj=study(args.seed_base,args.seeds,args.generations)
        path,sha=save_new(obj,Path(args.output_dir))
    except (ValueError,OSError) as err:
        p.error("HALT: "+str(err))
    print("EVIDENCE:",path)
    print("SHA256:",sha)
    for key,record in obj["summary"].items():
        print("POLICY:",key,
              "FINAL_ID_MSE:",round(record["curves"]["in_domain_macro_mse"][-1],8),
              "FINAL_RARE_MSE:",round(record["curves"]["rare_band_mse"][-1],8),
              "FINAL_SHIFT_MSE:",round(record["curves"]["shift_macro_mse"][-1],8),
              "CREDITS:",record["mean_totals"]["credits_spent"],
              "WEAK_FALSE_ACCEPT:",record["mean_totals"]["false_accept"],
              "WEAK_FALSE_REJECT:",record["mean_totals"]["false_reject"],
              "STEPS:",record["mean_totals"]["student_updates"])
    print("STATUS: PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED")
    return 0


if __name__=="__main__":
    sys.exit(main())
