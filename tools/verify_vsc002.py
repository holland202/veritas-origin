"""Independent VSC-002 evidence replay, no imports of experiment runner.

Rebuilds candidate streams, oracle labels, model parameter updates, adaptive
choices, rare-case metrics, and full cost tables. Accepting a record establishes
ONLY consistency under the published toy mathematical specification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

POLICIES=("gold_natural","gold_balanced","gold_error","gold_progress",
          "checked_progress","mixed_pseudo","gold_replay","pseudo_only")
WEIGHTS=(0.5,0.25,0.2,0.05)
REQUIRED={
    "protocol","evidence_status","seed_origin","seed_base","seeds","generations",
    "arms_order","configuration","runs","summary","limitations",
}
CONFIG={
    "initial_per_band":8,"selection_per_band":16,"test_per_band":48,
    "candidates_per_band":6,"oracle_queries_per_generation":8,
    "learning_rate":0.08,"initial_passes":4,"check_tolerance":0.30,
    "pseudo_noise":0.20,"natural_band_probabilities":list(WEIGHTS),
    "shift_test_x_multiplier":1.45,
}
REQUIRED_LIMITS=[
    "PUBLIC TOY SIMULATION; NO LANGUAGE MODEL OR HUMAN-TEXT TRAINING",
    "Reference oracle is a same-process function: no security isolation",
    "All policy tuning uses separate fixed selection data, not final tests",
    "Oracle query budgets are equal across oracle-assisted arms, NOT compute updates",
    "24 public seeds are exploratory, not untouched external confirmation",
    "Measured energy and token cost are unavailable; query/update counts are proxies",
    "Deterministic replay means specification agreement, not worldly truth",
]


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def unique(pairs):
    out={}
    for key,value in pairs:
        require(key not in out,"duplicate JSON key")
        out[key]=value
    return out


def nonfinite(value):
    raise ValueError("nonfinite JSON constant: "+value)


def compare(expected,received,path="root"):
    require(type(expected)==type(received),f"{path}: incompatible type")
    if isinstance(expected,dict):
        require(set(expected)==set(received),f"{path}: fields altered")
        for key in expected:
            compare(expected[key],received[key],path+"."+str(key))
    elif isinstance(expected,list):
        require(len(expected)==len(received),f"{path}: length differs")
        for i,(a,b) in enumerate(zip(expected,received)):
            compare(a,b,f"{path}[{i}]")
    elif type(expected) is float:
        require(math.isfinite(received) and
                math.isclose(expected,received,rel_tol=1e-12,abs_tol=1e-12),
                f"{path}: numerical replay mismatch")
    else:
        require(expected==received,f"{path}: value differs")


def stream(seed,purpose):
    tag=hashlib.sha256(f"VSC-002|{seed}|{purpose}".encode()).digest()
    return random.Random(int.from_bytes(tag,"big"))


def truth(seed,b,x):
    drift=(seed%13-6)*0.01
    if b==0: return 0.14+0.77*x-0.21*x*x+drift
    if b==1: return -0.24+0.27*x+0.70*x*x-drift
    if b==2: return 0.10-0.38*x+0.65*x*x*x+drift
    if b==3: return 0.12*x+0.73*math.sin(4*math.pi*x+drift)
    raise ValueError("bad band")


def data(seed,name,n,scale=1.0):
    draw=stream(seed,name)
    rows=[]
    for b in range(4):
        block=[]
        for _ in range(n):
            x=scale*(2*draw.random()-1)
            block.append((x,truth(seed,b,x)))
        rows.append(block)
    return rows


def available(seed,g):
    draw=stream(seed,f"candidate:{g}")
    rows=[]
    for b in range(4):
        for i in range(6):
            rows.append({"id":6*b+i,"band":b,"x":2*draw.random()-1})
    return rows


class Learner:
    def __init__(self):
        self.w=[[0.0]*3 for _ in range(4)]

    def estimate(self,b,x):
        return sum(c*v for c,v in zip(self.w[b],(1.0,x,x*x)))

    def train(self,b,x,y):
        residual=self.estimate(b,x)-y
        for j,v in enumerate((1.0,x,x*x)):
            self.w[b][j]-=0.08*residual*v


def accuracy(model,pool):
    errors=[]
    for band,items in enumerate(pool):
        error=sum((model.estimate(band,x)-y)**2 for x,y in items)
        errors.append(error/len(items))
    return errors


def floor_weights(source):
    scaled=[max(0.03,v) for v in source]
    tot=sum(scaled)
    return [v/tot for v in scaled]


def priority(mode,previous,old,new):
    if mode=="gold_balanced":
        return [0.25]*4
    if mode=="gold_error":
        total=sum(previous)
        return floor_weights([e/total if total else 0.25 for e in previous])
    if mode in ("gold_progress","checked_progress"):
        if old is None or new is None:
            return list(WEIGHTS)
        progress=[max(0.0,a-b) for a,b in zip(old,new)]
        denom=sum(progress)
        if denom<=0:
            return list(WEIGHTS)
        return floor_weights([0.4*WEIGHTS[b]+0.6*progress[b]/denom
                              for b in range(4)])
    return list(WEIGHTS)


def choose_rows(candidates,mode,weights,seed,gen):
    if mode=="gold_balanced":
        return [candidates[b*6+i] for i in range(2) for b in range(4)]
    name=("natural" if mode in ("gold_natural","mixed_pseudo","gold_replay")
          else "progress" if mode in ("gold_progress","checked_progress")
          else mode)
    picker=stream(seed,f"pick:{name}:{gen}")
    remaining={b:[r for r in candidates if r["band"]==b] for b in range(4)}
    chosen=[]
    for _ in range(8):
        bands=[b for b in range(4) if remaining[b]]
        target=picker.random()*sum(weights[b] for b in bands)
        picked=bands[-1]
        for b in bands:
            target-=weights[b]
            if target<0:
                picked=b
                break
        idx=picker.randrange(len(remaining[picked]))
        chosen.append(remaining[picked].pop(idx))
    return chosen


def xbucket(x):
    return max(0,min(7,int((x+1.0)*4)))


def diversity(records):
    n=len(records)
    if not n:
        return None
    counts=[sum(event["band"]==b for event in records) for b in range(4)]
    return -sum((v/n)*math.log(v/n) for v in counts if v)/math.log(4)


def record_metrics(model,idtest,shift,queried_cells,accepted_cells,
                   gold_cells,g,chosen,admitted,queried,steps,pseudo,replays,denied):
    a=accuracy(model,idtest)
    b=accuracy(model,shift)
    return {
        "generation":g,
        "id_mse_by_band":a,
        "id_macro_mse":sum(a)/4,
        "shift_mse_by_band":b,
        "shift_macro_mse":sum(b)/4,
        "rare_band_mse":a[3],
        "oracle_queried_cell_coverage":len(queried_cells)/32,
        "accepted_cell_coverage":len(accepted_cells)/32,
        "gold_label_cell_coverage":len(gold_cells)/32,
        "new_accepted_band_entropy":diversity(admitted),
        "new_oracle_queries":queried,
        "selected_rare_fraction":(sum(x["band"]==3 for x in chosen)/len(chosen)
                                  if chosen else None),
        "new_accepted_examples":len(admitted),
        "updates":steps,
        "pseudolabel_updates":pseudo,
        "replay_updates":replays,
        "rejected":denied,
    }


def replay_arm(seed,mode,anchors,selection,idtest,shift,ng):
    student=Learner()
    for _ in range(4):
        for b,rows in enumerate(anchors):
            for x,y in rows:
                student.train(b,x,y)
    initial_cells={(b,xbucket(x)) for b,rows in enumerate(anchors) for x,y in rows}
    queried_cells=set(initial_cells)
    accepted_cells=set(initial_cells)
    gold_cells=set(initial_cells)
    prev=accuracy(student,selection)
    prev_old=None
    prev_new=None
    history=[record_metrics(student,idtest,shift,queried_cells,accepted_cells,
                            gold_cells,0,[],[],0,128,0,0,0)]
    rounds=[]
    for gen in range(1,ng+1):
        candidates=available(seed,gen)
        allocation=(None if mode=="pseudo_only" else
                    priority(mode,prev,prev_old,prev_new))
        selected=([] if mode=="pseudo_only" else
                  choose_rows(candidates,mode,allocation,seed,gen))
        chosen_ids={r["id"] for r in selected}
        oracle_records=[]
        pseudo_records=[]
        replay_records=[]
        admitted=[]
        denied=0
        updates=0
        gaussian=stream(seed,f"noise:{'checked' if mode=='checked_progress' else mode}:{gen}")
        for row in selected:
            b,x=row["band"],row["x"]
            label=truth(seed,b,x)
            queried_cells.add((b,xbucket(x)))
            offered=None
            if mode=="checked_progress":
                offered=student.estimate(b,x)+gaussian.gauss(0,0.20)
                allowed=abs(offered-label)<=0.30
                if allowed:
                    student.train(b,x,offered)
                    accepted_cells.add((b,xbucket(x)))
                    admitted.append(row)
                    updates+=1
                else:
                    denied+=1
            else:
                allowed=True
                student.train(b,x,label)
                accepted_cells.add((b,xbucket(x)))
                gold_cells.add((b,xbucket(x)))
                admitted.append(row)
                updates+=1
            oracle_records.append({
                "id":row["id"],"band":b,"x":x,"oracle_label":label,
                "offered_pseudo":offered,"accepted":allowed,
            })

        if mode in ("mixed_pseudo","pseudo_only"):
            unused=[r for r in candidates if r["id"] not in chosen_ids]
            stream(seed,f"pseudo_candidate_order:{gen}").shuffle(unused)
            if mode=="mixed_pseudo":
                unused=unused[:16]
            for row in unused:
                b,x=row["band"],row["x"]
                label=student.estimate(b,x)+gaussian.gauss(0,0.20)
                student.train(b,x,label)
                pseudo_records.append({
                    "id":row["id"],"band":b,"x":x,"pseudo_label":label,
                })
                accepted_cells.add((b,xbucket(x)))
                updates+=1
        if mode=="gold_replay":
            draw=stream(seed,f"replay:{gen}")
            for _ in range(16):
                b=draw.randrange(4)
                j=draw.randrange(8)
                x,y=anchors[b][j]
                student.train(b,x,y)
                replay_records.append({
                    "band":b,"initial_index":j,"x":x,"label":y
                })
                updates+=1

        after=accuracy(student,selection)
        rounds.append({
            "generation":gen,"allocation_weights":allocation,
            "candidate_pool":candidates,
            "oracle_events":oracle_records,
            "pseudo_events":pseudo_records,
            "replay_events":replay_records,
            "selection_errors_before":prev,
            "selection_errors_after":after,
        })
        history.append(record_metrics(student,idtest,shift,queried_cells,
                                      accepted_cells,gold_cells,gen,selected,
                                      admitted,len(selected),updates,
                                      len(pseudo_records),len(replay_records),denied))
        prev_old=prev
        prev_new=after
        prev=after

    total={
        "new_oracle_queries":sum(h["new_oracle_queries"] for h in history[1:]),
        "updates":sum(h["updates"] for h in history[1:]),
        "pseudolabel_updates":sum(h["pseudolabel_updates"] for h in history[1:]),
        "replay_updates":sum(h["replay_updates"] for h in history[1:]),
        "rejected":sum(h["rejected"] for h in history[1:]),
        "fixed_reference_labels_shared":32+64+192+192,
    }
    return {"mode":mode,"history":history,"rounds":rounds,
            "totals":total,"weights_final":student.w}


def check(raw,pinned_sha):
    require(type(raw) is bytes and len(raw)<45_000_000,"evidence size invalid")
    require(type(pinned_sha) is str and len(pinned_sha)==64 and
            all(c in "0123456789abcdef" for c in pinned_sha),
            "expected hash malformed")
    require(hashlib.sha256(raw).hexdigest()==pinned_sha,"evidence SHA256 mismatch")
    doc=json.loads(raw,object_pairs_hook=unique,parse_constant=nonfinite)
    require(type(doc) is dict and set(doc)==REQUIRED,"root field mismatch")
    require(doc["protocol"]=="VSC-002" and
            doc["evidence_status"]=="PUBLIC_EXPLORATORY_SIMULATED_NOT_VALIDATED",
            "false validation or wrong protocol")
    require(doc["seed_origin"] in ("PUBLIC_TEST_SEED","REVEALED_AFTER_PILOT"),
            "seed status invalid")
    compare(CONFIG,doc["configuration"],"configuration")
    compare(list(POLICIES),doc["arms_order"],"arms_order")
    compare(REQUIRED_LIMITS,doc["limitations"],"limitations")
    first,n,ng=doc["seed_base"],doc["seeds"],doc["generations"]
    require(type(first) is int and 0<=first<2**62-100,"seed range invalid")
    require(type(n) is int and 1<=n<=24,"seed count invalid")
    require(type(ng) is int and 1<=ng<=12,"generation count invalid")
    require(type(doc["runs"]) is list and len(doc["runs"])==n,"run count wrong")

    measures=("id_macro_mse","shift_macro_mse","rare_band_mse",
              "oracle_queried_cell_coverage","accepted_cell_coverage",
              "gold_label_cell_coverage")
    cost=("new_oracle_queries","updates","pseudolabel_updates",
          "replay_updates","rejected")
    summary={mode:{
        "curves":{metric:[0.0]*(ng+1) for metric in measures},
        "mean_totals":{metric:0.0 for metric in cost},
        "per_seed_final_id_mse":[],
        "per_seed_final_shift_mse":[],
    } for mode in POLICIES}

    for offset,row in enumerate(doc["runs"]):
        seed=first+offset
        require(type(row) is dict and set(row)=={"seed","arms"},
                "run fields invalid")
        require(type(row["seed"]) is int and row["seed"]==seed,"seed order invalid")
        require(type(row["arms"]) is list and len(row["arms"])==len(POLICIES),
                "arm list wrong")
        anchors=data(seed,"initial",8)
        selection=data(seed,"selection",16)
        idtest=data(seed,"id_test",48)
        shifted=data(seed,"shift_test",48,1.45)

        for i,mode in enumerate(POLICIES):
            expected=replay_arm(seed,mode,anchors,selection,idtest,shifted,ng)
            compare(expected,row["arms"][i],f"seed{seed}.{mode}")
            if mode!="pseudo_only":
                require(expected["totals"]["new_oracle_queries"]==ng*8,
                        "oracle budget broken")
            else:
                require(expected["totals"]["new_oracle_queries"]==0,
                        "pseudo-only oracle leakage")
            for metric in measures:
                for t in range(ng+1):
                    summary[mode]["curves"][metric][t]+=expected["history"][t][metric]/n
            for metric in cost:
                summary[mode]["mean_totals"][metric]+=expected["totals"][metric]/n
            summary[mode]["per_seed_final_id_mse"].append(
                expected["history"][-1]["id_macro_mse"])
            summary[mode]["per_seed_final_shift_mse"].append(
                expected["history"][-1]["shift_macro_mse"])
    compare(summary,doc["summary"],"summary")
    return {
        "policy_seed_replays":len(POLICIES)*n,
        "generational_checkpoints":len(POLICIES)*n*(ng+1),
        "new_oracle_budget_per_gold_arm":ng*8,
        "verdict":"INTERNAL_SPECIFICATION_CONSISTENCY_ONLY",
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    args=p.parse_args(argv)
    try:
        res=check(args.evidence.read_bytes(),args.sha256)
    except (ValueError,TypeError,KeyError,IndexError,OSError,OverflowError) as err:
        print("VERDICT: INCONSISTENT_OR_UNVERIFIABLE:",err,file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH VSC-002 SPECIFICATION")
    print(json.dumps(res,sort_keys=True))
    print("LIMIT: oracle isolation, model collapse and real-world transfer UNVALIDATED")
    return 0


if __name__=="__main__":
    sys.exit(main())
