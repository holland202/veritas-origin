"""VSC-003 independent replay. No imports from the experiment runner.

Reports only internal consistency of a disclosed mathematical specification.
Weak-check true labels are reconstructed here for audit; they are NEVER
available as training labels in weak-only arms.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

POLICIES=(
    "gold_natural","gold_balanced","gold_error","gold_progress",
    "checked_natural","checked_balanced","checked_progress",
    "hybrid_progress","gold_plus_pseudo","gold_replay","pseudo_only",
)
NATURAL=(0.50,0.25,0.20,0.05)
EXPECTED_CONSTANTS={
    "natural":list(NATURAL),"initial_per_band":8,
    "selection_per_band":16,"test_per_band":48,
    "candidates_per_band":6,"gen_credits":12,
    "strong_cost":6,"weak_cost":1,"student_rate":0.08,
    "initial_epochs":4,"tolerance":0.30,"flip_rate":0.08,
    "proposal_noise":0.25,"outlier_rate":0.15,
    "outlier_size":1.0,"shift_multiplier":1.4,
}
LIMITATIONS=[
    "PUBLIC SYNTHETIC NUMERICAL STUDY, NOT LANGUAGE-MODEL TRAINING",
    "Reference and cheap checker are co-resident Python functions; oracle isolation NOT TESTED",
    "Binary cheap-check feedback leaks a bit but never supplies a true numerical label to the student",
    "Ground-truth labels are recorded in evidence for post-run audit, not fed to weak-only policies",
    "Shared initial, selection, and test oracle labels are counted separately from acquisition credits",
    "No energy, actual money, pretrained language model, real human-data, or external-domain evaluation",
    "Novelty and production reliability NOT ESTABLISHED",
]
ROOT_KEYS={
    "protocol","status","seed_base","n_seeds","generations","arms",
    "constants","runs","summary","limitations",
}


def demand(expr,label):
    if not expr:
        raise ValueError(label)


def unique_keys(pairs):
    doc={}
    for k,v in pairs:
        demand(k not in doc,"duplicate JSON key")
        doc[k]=v
    return doc


def nonfinite(x):
    raise ValueError("nonfinite numeric constant "+x)


def same(expected,actual,path="evidence"):
    demand(type(expected) is type(actual),f"{path}: type differs")
    if isinstance(expected,dict):
        demand(set(expected)==set(actual),f"{path}: fields differ")
        for k in expected:
            same(expected[k],actual[k],f"{path}.{k}")
    elif isinstance(expected,list):
        demand(len(expected)==len(actual),f"{path}: length differs")
        for i,(a,b) in enumerate(zip(expected,actual)):
            same(a,b,f"{path}[{i}]")
    elif type(expected) is float:
        demand(math.isfinite(actual) and
               math.isclose(expected,actual,rel_tol=1e-12,abs_tol=1e-12),
               f"{path}: numerical replay mismatch")
    else:
        demand(expected==actual,f"{path}: replay mismatch")


def seeded(seed,namespace):
    raw=hashlib.sha256(f"VSC-003:{seed}:{namespace}".encode()).digest()
    return random.Random(int.from_bytes(raw,"big"))


def math_reference(seed,band,x):
    shift=(seed%17-8)*0.008
    if band==0: return 0.2+0.70*x-0.18*x*x+shift
    if band==1: return -0.14+0.31*x+0.67*x*x-shift
    if band==2: return 0.08-0.36*x+0.55*x*x*x+shift
    if band==3: return 0.1*x+0.72*math.sin(4*math.pi*x+shift)
    raise ValueError("band must be 0..3")


def reference_pool(seed,name,count,multiplier=1.):
    gen=seeded(seed,name)
    items=[]
    for b in range(4):
        series=[]
        for _ in range(count):
            x=multiplier*(2*gen.random()-1)
            series.append((x,math_reference(seed,b,x)))
        items.append(series)
    return items


def unlabeled_pool(seed,generation):
    gen=seeded(seed,f"candidates:{generation}")
    pool=[]
    for band in range(4):
        for j in range(6):
            pool.append({"id":band*6+j,"band":band,
                         "x":2*gen.random()-1})
    return pool


class Predictor:
    def __init__(self):
        self.parameters=[[0.0,0.0,0.0] for _ in range(4)]

    def eval(self,b,x):
        return sum(a*z for a,z in zip(self.parameters[b],(1.,x,x*x)))

    def update(self,b,x,y):
        e=self.eval(b,x)-y
        for i,f in enumerate((1.,x,x*x)):
            self.parameters[b][i]-=0.08*e*f


def loss(model,rows):
    vals=[]
    for b,group in enumerate(rows):
        val=sum((model.eval(b,x)-y)**2 for x,y in group)/len(group)
        vals.append(val)
    return vals


def allocation(policy,score,previous,current):
    if policy in ("gold_balanced","checked_balanced"):
        return [0.25]*4
    if policy=="gold_error":
        total=sum(score)
        p=[v/total if total>0 else .25 for v in score]
    elif policy in ("gold_progress","checked_progress","hybrid_progress"):
        deltas=([max(0.,a-b) for a,b in zip(previous,current)]
                if previous is not None and current is not None else [0.]*4)
        total=sum(deltas)
        p=([.4*NATURAL[b]+.6*deltas[b]/total for b in range(4)]
           if total>0 else list(NATURAL))
    else:
        p=list(NATURAL)
    floored=[max(.03,v) for v in p]
    total=sum(floored)
    return [v/total for v in floored]


def select(pool,policy,weights,seed,generation,limit):
    if policy=="gold_balanced":
        b1=(generation-1)%4
        b2=(generation+1)%4
        return [pool[b*6+(generation-1)%6] for b in (b1,b2)]
    if policy=="checked_balanced":
        return [pool[b*6+j] for j in range(3) for b in range(4)]
    klass=("natural" if policy in (
        "gold_natural","checked_natural","gold_plus_pseudo",
        "gold_replay","pseudo_only"
    ) else "progress" if policy in (
        "gold_progress","checked_progress","hybrid_progress"
    ) else policy)
    rng=seeded(seed,f"selection:{klass}:{generation}")
    by_band={b:[item for item in pool if item["band"]==b] for b in range(4)}
    result=[]
    for _ in range(limit):
        available=[b for b in range(4) if by_band[b]]
        threshold=rng.random()*sum(weights[b] for b in available)
        chosen=available[-1]
        for b in available:
            threshold-=weights[b]
            if threshold<0:
                chosen=b
                break
        j=rng.randrange(len(by_band[chosen]))
        result.append(by_band[chosen].pop(j))
    return result


def proposal(model,item,seed,generation):
    b,x=item["band"],item["x"]
    r=seeded(seed,f"proposal:{generation}:{item['id']}")
    p=model.eval(b,x)+r.gauss(0.,.25)
    is_bad=r.random()<.15
    if is_bad:
        p+=1.0*(1 if r.random()<.5 else -1)
    return p,is_bad


def feedback(seed,generation,item,pseudo):
    correct=abs(pseudo-math_reference(seed,item["band"],item["x"]))<=.30
    wrong=seeded(seed,f"weak_flip:{generation}:{item['id']}").random()<.08
    return (not correct if wrong else correct),correct,wrong


def cell(x):
    return max(0,min(7,int((x+1)*4)))


def metrics(model,ordinary,shifted,asked,accepted,gold,
            generation,spent,steps,strong,weak,weak_yes,weak_no,
            false_yes,false_no,pseudo,replay,band_ids):
    a=loss(model,ordinary)
    s=loss(model,shifted)
    return {
        "generation":generation,
        "in_domain_mse_by_band":a,
        "in_domain_macro_mse":sum(a)/4,
        "shift_mse_by_band":s,
        "shift_macro_mse":sum(s)/4,
        "rare_band_mse":a[3],
        "queried_cell_coverage":len(asked)/32,
        "accepted_cell_coverage":len(accepted)/32,
        "gold_cell_coverage":len(gold)/32,
        "credits_spent":spent,
        "credits_unused":12-spent if generation else 0,
        "strong_queries":strong,
        "weak_queries":weak,
        "student_updates":steps,
        "weak_accepted":weak_yes,
        "weak_rejected":weak_no,
        "false_accept":false_yes,
        "false_reject":false_no,
        "pseudolabel_updates":pseudo,
        "anchor_replays":replay,
        "queried_rare_count":sum(b==3 for b in band_ids),
        "queried_band_counts":[sum(b==k for b in band_ids) for k in range(4)],
    }


def replay_policy(seed,name,initial,selector,idtest,shifted,n_gen):
    model=Predictor()
    for _ in range(4):
        for b,group in enumerate(initial):
            for x,y in group:
                model.update(b,x,y)
    initial_cells={(b,cell(x)) for b,group in enumerate(initial) for x,y in group}
    asked=set(initial_cells)
    admitted=set(initial_cells)
    gold=set(initial_cells)
    score=loss(model,selector)
    prior=None
    recent=None
    checkpoints=[metrics(model,idtest,shifted,asked,admitted,gold,
                         0,0,128,0,0,0,0,0,0,0,0,[])]
    rounds=[]
    for g in range(1,n_gen+1):
        candidates=unlabeled_pool(seed,g)
        prob=allocation(name,score,prior,recent)
        if name.startswith("gold_") or name=="gold_plus_pseudo":
            chosen=select(candidates,name,prob,seed,g,2)
            strong_ids={r["id"] for r in chosen}
            weak_ids=set()
        elif name=="hybrid_progress":
            chosen=select(candidates,name,prob,seed,g,7)
            strong_ids={chosen[0]["id"]}
            weak_ids={r["id"] for r in chosen[1:]}
        elif name=="pseudo_only":
            chosen=select(candidates,name,prob,seed,g,12)
            strong_ids=set()
            weak_ids=set()
        else:
            chosen=select(candidates,name,prob,seed,g,12)
            strong_ids=set()
            weak_ids={r["id"] for r in chosen}
        decisions=[]
        extras=[]
        got_gold=got_weak=weak_yes=weak_no=0
        wrong_yes=wrong_no=0
        pseudo_steps=steps=0
        bands=[]
        for item in chosen:
            b,x=item["band"],item["x"]
            slot=(b,cell(x))
            guess,is_outlier=proposal(model,item,seed,g)
            if item["id"] in strong_ids:
                true=math_reference(seed,b,x)
                model.update(b,x,true)
                asked.add(slot)
                admitted.add(slot)
                gold.add(slot)
                bands.append(b)
                role="STRONG_GOLD"
                accepted_truth=None
                inverted=None
                decision=None
                update_label=true
                got_gold+=1
                steps+=1
            elif item["id"] in weak_ids:
                decision,accepted_truth,inverted=feedback(seed,g,item,guess)
                true=math_reference(seed,b,x)  # audit-only, never train
                role="WEAK_ACCEPTED_PSEUDO" if decision else "WEAK_REFUSED"
                update_label=guess if decision else None
                asked.add(slot)
                bands.append(b)
                got_weak+=1
                if decision:
                    model.update(b,x,guess)
                    admitted.add(slot)
                    weak_yes+=1
                    pseudo_steps+=1
                    steps+=1
                else:
                    weak_no+=1
                if decision and not accepted_truth:
                    wrong_yes+=1
                elif not decision and accepted_truth:
                    wrong_no+=1
            else:
                role="UNVERIFIED_PSEUDO"
                true=None
                accepted_truth=None
                inverted=None
                decision=None
                model.update(b,x,guess)
                update_label=guess
                admitted.add(slot)
                pseudo_steps+=1
                steps+=1
            decisions.append({
                "id":item["id"],"band":b,"x":x,
                "kind":role,"proposed_label":guess,
                "outlier_injected":is_outlier,
                "evaluator_true_label":true,
                "truth_acceptable":accepted_truth,
                "feedback_flipped":inverted,
                "weak_boolean":decision,
                "training_label":update_label,
            })
        if name in ("gold_plus_pseudo","gold_replay"):
            if name=="gold_plus_pseudo":
                used={r["id"] for r in chosen}
                other=[row for row in candidates if row["id"] not in used]
                seeded(seed,f"extra_sample:{g}").shuffle(other)
                for row in other[:10]:
                    guess,outlier=proposal(model,row,seed,g)
                    model.update(row["band"],row["x"],guess)
                    admitted.add((row["band"],cell(row["x"])))
                    steps+=1
                    pseudo_steps+=1
                    extras.append({
                        "kind":"UNVERIFIED_EXTRA","id":row["id"],
                        "band":row["band"],"x":row["x"],
                        "proposed_label":guess,"outlier_injected":outlier
                    })
            else:
                r=seeded(seed,f"anchor_replay:{g}")
                for _ in range(10):
                    b=r.randrange(4)
                    idx=r.randrange(8)
                    x,y=initial[b][idx]
                    model.update(b,x,y)
                    steps+=1
                    extras.append({
                        "kind":"TRUSTED_ANCHOR_REPLAY","band":b,
                        "initial_index":idx,"x":x,"true_label":y
                    })
        cost=got_gold*6+got_weak
        demand(cost<=12,"budget not respected by independent replay")
        new_score=loss(model,selector)
        rounds.append({
            "generation":g,"weights":prob,
            "candidate_pool":candidates,"events":decisions,
            "extra_events":extras,"selection_before":score,
            "selection_after":new_score
        })
        checkpoints.append(metrics(
            model,idtest,shifted,asked,admitted,gold,
            g,cost,steps,got_gold,got_weak,weak_yes,weak_no,
            wrong_yes,wrong_no,pseudo_steps,
            len(extras) if name=="gold_replay" else 0,bands
        ))
        prior=score
        recent=new_score
        score=new_score
    counters=(
        "credits_spent","credits_unused","strong_queries","weak_queries",
        "student_updates","weak_accepted","weak_rejected","false_accept",
        "false_reject","pseudolabel_updates","anchor_replays","queried_rare_count",
    )
    totals={f:sum(v[f] for v in checkpoints[1:]) for f in counters}
    totals["shared_reference_labels"]=32+64+48*4*2
    return {
        "policy":name,"history":checkpoints,"rounds":rounds,
        "totals":totals,"final_weights":model.parameters
    }


def expected_summary(rows,generations):
    series=(
        "in_domain_macro_mse","shift_macro_mse","rare_band_mse",
        "queried_cell_coverage","accepted_cell_coverage","gold_cell_coverage",
    )
    sums=(
        "credits_spent","credits_unused","strong_queries","weak_queries",
        "student_updates","weak_accepted","weak_rejected","false_accept",
        "false_reject","pseudolabel_updates","anchor_replays","queried_rare_count"
    )
    result={}
    for mode in POLICIES:
        arms=[next(a for a in run["policies"] if a["policy"]==mode) for run in rows]
        result[mode]={
            "curves":{key:[sum(a["history"][t][key] for a in arms)/len(arms)
                            for t in range(generations+1)] for key in series},
            "mean_totals":{key:sum(a["totals"][key] for a in arms)/len(arms)
                           for key in sums},
            "per_seed_final_id_mse":[a["history"][-1]["in_domain_macro_mse"]
                                     for a in arms],
            "per_seed_final_rare_mse":[a["history"][-1]["rare_band_mse"]
                                       for a in arms],
            "per_seed_final_shift_mse":[a["history"][-1]["shift_macro_mse"]
                                        for a in arms],
        }
    return result


def verify(raw,sha):
    demand(type(raw) is bytes and len(raw)<50_000_000,"invalid evidence size")
    demand(type(sha) is str and len(sha)==64 and
           all(c in "0123456789abcdef" for c in sha),"invalid pinned SHA")
    demand(hashlib.sha256(raw).hexdigest()==sha,"evidence SHA256 mismatch")
    doc=json.loads(raw,object_pairs_hook=unique_keys,parse_constant=nonfinite)
    demand(type(doc) is dict and set(doc)==ROOT_KEYS,"root schema mismatch")
    demand(doc["protocol"]=="VSC-003" and
           doc["status"]=="PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED",
           "invalid protocol or false validated status")
    same(EXPECTED_CONSTANTS,doc["constants"],"constants")
    same(list(POLICIES),doc["arms"],"arms")
    same(LIMITATIONS,doc["limitations"],"limitations")
    base,n,g=doc["seed_base"],doc["n_seeds"],doc["generations"]
    demand(type(base) is int and 0<=base<2**62-100,"seed invalid")
    demand(type(n) is int and 1<=n<=24,"seed count invalid")
    demand(type(g) is int and 1<=g<=10,"generations invalid")
    demand(type(doc["runs"]) is list and len(doc["runs"])==n,"run count invalid")
    reconstructed=[]
    weak_good=weak_bad=wrong_yes=wrong_no=0
    for k,run in enumerate(doc["runs"]):
        seed=base+k
        demand(type(run) is dict and set(run)=={"seed","policies"},
               "run schema invalid")
        demand(type(run["seed"]) is int and run["seed"]==seed,
               "seeds not consecutive")
        demand(type(run["policies"]) is list and
               len(run["policies"])==len(POLICIES),"policies missing")
        initial=reference_pool(seed,"initial",8)
        selection=reference_pool(seed,"selection",16)
        standard=reference_pool(seed,"test",48)
        shifted=reference_pool(seed,"shift",48,1.4)
        replayed=[]
        for i,mode in enumerate(POLICIES):
            outcome=replay_policy(seed,mode,initial,selection,standard,shifted,g)
            same(outcome,run["policies"][i],f"seed{seed}.{mode}")
            if mode=="pseudo_only":
                demand(outcome["totals"]["credits_spent"]==0,
                       "pseudo-only spent budget")
            else:
                demand(outcome["totals"]["credits_spent"]==g*12,
                       "cost parity broken")
            if mode.startswith("checked_") or mode=="hybrid_progress":
                for period in outcome["rounds"]:
                    for event in period["events"]:
                        if event["kind"].startswith("WEAK_"):
                            weak_good+=int(bool(event["truth_acceptable"]))
                            weak_bad+=int(not event["truth_acceptable"])
                wrong_yes+=outcome["totals"]["false_accept"]
                wrong_no+=outcome["totals"]["false_reject"]
            replayed.append(outcome)
        reconstructed.append({"seed":seed,"policies":replayed})
    same(expected_summary(reconstructed,g),doc["summary"],"summary")
    return {
        "seed_count":n,"policy_replays":n*len(POLICIES),
        "training_generations":g,
        "weak_truth_acceptable":weak_good,
        "weak_truth_unacceptable":weak_bad,
        "weak_false_accepts":wrong_yes,
        "weak_false_rejects":wrong_no,
        "anti_vacuity":("INFORMATIVE" if weak_good and weak_bad and
                        wrong_yes and wrong_no else "UNINFORMATIVE"),
        "verdict":"INTERNAL_SPECIFICATION_CONSISTENCY_ONLY",
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    a=p.parse_args(argv)
    try:
        outcome=verify(a.evidence.read_bytes(),a.sha256)
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,OSError) as err:
        print("VERDICT: INCONSISTENT_OR_UNVERIFIABLE",err,file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH VSC-003 SPECIFICATION")
    print("DETAILS:",json.dumps(outcome,sort_keys=True))
    print("SCOPE: PUBLIC_SIMULATED_NOT_VALIDATED; no oracle isolation or LLM")
    return 0


if __name__=="__main__":
    sys.exit(main())
