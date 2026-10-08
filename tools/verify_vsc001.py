"""Independent VSC-001 deterministic evidence replay.

Does not import the VSC experiment runner. This reconstructs its generator,
reference oracle, policy, complete training trajectory and outcome metrics.
Agreement proves internal specification consistency, not external-world truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

POLICIES = ("oracle_natural","oracle_balanced","noisy_natural",
            "verified_natural","verified_progress","recursive_natural")
NATURAL = (0.5, 0.25, 0.15, 0.10)
REFERENCE = {
    "initial_per_band": 8, "selection_per_band": 16,
    "conformal_per_band": 32, "test_per_band": 64,
    "corruption_rate": 0.22, "corruption_size": 1.8,
    "pseudo_noise": 0.18, "learning_rate": 0.10,
    "seed_epochs": 4, "nominal_coverage": 0.90,
    "natural_weights": list(NATURAL),
}
REQUIRED_ROOT = {"protocol","status","seed_origin","seed_base","n_seeds",
                 "rounds","candidates_per_round","mode_order","constants",
                 "runs","summary","limitations"}


def ensure(expr, why):
    if not expr:
        raise ValueError(why)


def no_duplicate(pairs):
    ans = {}
    for k,v in pairs:
        ensure(k not in ans,"duplicate JSON key")
        ans[k]=v
    return ans


def reject_nonfinite(s):
    raise ValueError("nonfinite JSON: "+s)


def seeded(seed, domain):
    raw=hashlib.sha256(f"VSC-001|{seed}|{domain}".encode()).digest()
    return random.Random(int.from_bytes(raw,"big"))


def reference_value(seed, band, x):
    shift=(seed % 11 - 5)*0.012
    if band==0: return 0.18+0.80*x-0.25*x*x+shift
    if band==1: return -0.28+0.32*x+0.73*x*x-shift
    if band==2: return 0.16-0.30*x+0.65*x*x*x+shift
    if band==3: return 0.15*x+0.68*math.sin(4*math.pi*x+shift)
    raise ValueError("band outside domain")


def make_pool(seed, label, count):
    gen=seeded(seed,label)
    blocks=[]
    for b in range(4):
        block=[]
        for _ in range(count):
            x=gen.random()*2.0-1.0
            block.append((x,reference_value(seed,b,x)))
        blocks.append(block)
    return blocks


class Model:
    def __init__(self):
        self.coeffs=[[0.0]*3 for _ in range(4)]

    def output(self,b,x):
        w=self.coeffs[b]
        return sum((w[0]*1.0,w[1]*x,w[2]*x*x))

    def step(self,b,x,y):
        e=self.output(b,x)-y
        f=(1.0,x,x*x)
        for j in range(3):
            self.coeffs[b][j]=self.coeffs[b][j]-0.10*e*f[j]


def mse(model,dataset):
    result=[]
    for b,examples in enumerate(dataset):
        total=0.
        for x,label in examples:
            total+=(model.output(b,x)-label)**2
        result.append(total/len(examples))
    return result


def sample_band(r,weights):
    x=r.random()*sum(weights)
    for i,w in enumerate(weights):
        x-=w
        if x<0.:
            return i
    return 3


def trend_weights(old,new):
    gains=[max(0.,a-b) for a,b in zip(old,new)]
    if sum(gains)<=0.:
        return list(NATURAL)
    return [0.4*NATURAL[i]+0.6*g/sum(gains) for i,g in enumerate(gains)]


def calibrated_result(model,calibration,testing):
    rows=[]
    for b in range(4):
        residuals=sorted(abs(y-model.output(b,x)) for x,y in calibration[b])
        index=min(math.ceil((len(residuals)+1)*0.90),len(residuals))-1
        q=residuals[index]
        covered=sum(abs(y-model.output(b,x))<=q for x,y in testing[b])
        rows.append({"coverage":covered/len(testing[b]),"width":2*q,"q":q})
    return rows


def reconstruct_arm(seed,mode,initial,select,cal,test,rounds,candidates_per_round):
    m=Model()
    for _ in range(4):
        for b in range(4):
            for x,y in initial[b]:
                m.step(b,x,y)
    original=mse(m,test)
    before=mse(m,select)
    picker=seeded(seed,"balanced" if mode=="oracle_balanced" else
                  "adaptive" if mode=="verified_progress" else "natural")
    faults=seeded(seed,"adaptive_corruption" if mode=="verified_progress" else
                  "natural_corruption")
    pseudo=seeded(seed,"recursive_pseudo")
    weights=list((0.25,)*4 if mode=="oracle_balanced" else NATURAL)
    trace=[]
    timeline=[]
    total_good=total_bad=bad_admitted=0
    calls=32
    for rnd in range(rounds):
        weights_this_round=list(weights)
        good=bad=0
        for idx in range(candidates_per_round):
            b=sample_band(picker,weights_this_round)
            x=2.0*picker.random()-1.0
            ground=None
            cost=0
            corrupted=False
            if mode=="recursive_natural":
                offered=m.output(b,x)+pseudo.gauss(0.,0.18)
                accepted=True
            else:
                ground=reference_value(seed,b,x)
                cost+=1
                if mode.startswith(("noisy_","verified_")):
                    corrupted=faults.random()<0.22
                    if corrupted:
                        offered=ground+(1.8 if faults.random()<0.5 else -1.8)
                    else:
                        offered=ground
                else:
                    offered=ground
                if mode.startswith("verified_"):
                    cost+=1
                    accepted=abs(offered-reference_value(seed,b,x))<=1e-9
                else:
                    accepted=True
            calls+=cost
            if accepted:
                m.step(b,x,offered)
                good+=1
                total_good+=1
                if corrupted:
                    bad_admitted+=1
            else:
                bad+=1
                total_bad+=1
            trace.append({"round":rnd,"candidate":idx,"band":b,"x":x,
                          "offered":offered,"reference":ground,
                          "injected":corrupted,"accepted":accepted,
                          "oracle_calls":cost})
        now=mse(m,select)
        timeline.append({"round":rnd,"weights":weights_this_round,
                         "selection_mse_by_band":now,
                         "accepted":good,"rejected":bad})
        if mode=="verified_progress":
            weights=trend_weights(before,now)
        before=now
    final=mse(m,test)
    coverage=calibrated_result(m,cal,test)
    return {
        "mode":mode,
        "initial_test_mse_by_band":original,
        "final_test_mse_by_band":final,
        "initial_test_macro_mse":sum(original)/4,
        "final_test_macro_mse":sum(final)/4,
        "improvement":(sum(original)-sum(final))/4,
        "conformal_by_band":coverage,
        "macro_coverage":sum(z["coverage"] for z in coverage)/4,
        "mean_interval_width":sum(z["width"] for z in coverage)/4,
        "train_oracle_calls":calls,
        "selection_evaluation_calls":16*4*(rounds+1),
        "conformal_and_test_evaluation_calls":4*(32+64),
        "accepted":total_good,"rejected":total_bad,
        "false_labels_admitted":bad_admitted,
        "history":timeline,"events":trace,"weights_final":m.coeffs
    }


def validate_match(expected,found,location="document"):
    ensure(type(expected)==type(found) or (
        type(expected) is float and type(found) is int
    ),f"{location}: mismatched type")
    if type(expected) is dict:
        ensure(set(expected)==set(found),f"{location}: unexpected or missing fields")
        for key in expected:
            validate_match(expected[key],found[key],location+"."+str(key))
    elif type(expected) is list:
        ensure(len(expected)==len(found),f"{location}: wrong list length")
        for i,(a,b) in enumerate(zip(expected,found)):
            validate_match(a,b,location+"["+str(i)+"]")
    elif type(expected) is float:
        ensure(math.isfinite(float(found)) and
               math.isclose(expected,found,abs_tol=1e-12,rel_tol=1e-12),
               f"{location}: replay mismatch")
    else:
        ensure(expected==found,f"{location}: replay mismatch")


def verify(raw,expected_sha256):
    ensure(type(raw) is bytes,"raw evidence must be bytes")
    ensure(type(expected_sha256) is str and len(expected_sha256)==64 and
           all(c in "0123456789abcdef" for c in expected_sha256),
           "invalid expected hash")
    ensure(hashlib.sha256(raw).hexdigest()==expected_sha256,
           "evidence SHA256 mismatch")
    doc=json.loads(raw,object_pairs_hook=no_duplicate,
                   parse_constant=reject_nonfinite)
    ensure(type(doc) is dict and set(doc)==REQUIRED_ROOT,
           "evidence root schema invalid")
    ensure(doc["protocol"]=="VSC-001" and
           doc["status"]=="EXPLORATORY_SIMULATED_NOT_VALIDATED",
           "invalid status/protocol")
    ensure(doc["seed_origin"] in ("PUBLIC_TEST_SEED","REVEALED_AFTER_RUN"),
           "invalid seed origin")
    validate_match(REFERENCE,doc["constants"],"constants")
    ensure(doc["mode_order"]==list(POLICIES),"mode order mismatch")
    base=doc["seed_base"]
    n=doc["n_seeds"]
    rounds=doc["rounds"]
    candidates=doc["candidates_per_round"]
    ensure(type(base) is int and 0<=base<2**63-10,"seed base invalid")
    ensure(type(n) is int and 1<=n<=8,"seed count invalid")
    ensure(type(rounds) is int and 1<=rounds<=20,"round count invalid")
    ensure(type(candidates) is int and 1<=candidates<=50,"candidate budget invalid")
    ensure(type(doc["limitations"]) is list and len(doc["limitations"])>=5 and
           all(type(s) is str and s for s in doc["limitations"]),
           "limitations missing")
    ensure(type(doc["runs"]) is list and len(doc["runs"])==n,"run count invalid")
    expected_summary={}
    for mode in POLICIES:
        expected_summary[mode]={
            "final_test_macro_mse":0.0,
            "improvement":0.0,
            "macro_coverage":0.0,
            "mean_interval_width":0.0,
            "train_oracle_calls":0.0,
            "accepted":0.0,
            "rejected":0.0,
            "false_labels_admitted":0.0,
            "per_seed_mse":[],
        }
    checked=0
    for offset,record in enumerate(doc["runs"]):
        seed=base+offset
        ensure(type(record) is dict and set(record)=={"seed","arms"} and
               type(record["seed"]) is int and record["seed"]==seed,
               "run seed/schema invalid")
        ensure(type(record["arms"]) is list and len(record["arms"])==len(POLICIES),
               "arms missing/duplicated")
        original=make_pool(seed,"initial",8)
        selection=make_pool(seed,"selection",16)
        conformal=make_pool(seed,"conformal",32)
        final_test=make_pool(seed,"test",64)
        for index,mode in enumerate(POLICIES):
            outcome=reconstruct_arm(seed,mode,original,selection,conformal,
                                    final_test,rounds,candidates)
            validate_match(outcome,record["arms"][index],f"run{seed}.{mode}")
            for field in ("final_test_macro_mse","improvement",
                          "macro_coverage","mean_interval_width",
                          "train_oracle_calls","accepted",
                          "rejected","false_labels_admitted"):
                expected_summary[mode][field]+=outcome[field]/n
            expected_summary[mode]["per_seed_mse"].append(outcome["final_test_macro_mse"])
            checked+=1
    validate_match(expected_summary,doc["summary"],"summary")
    return {"seeds":n,"arms_replayed":checked,
            "candidate_events":checked*rounds*candidates,
            "replay":"INTERNALLY_CONSISTENT_ONLY"}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    args=p.parse_args(argv)
    try:
        result=verify(args.evidence.read_bytes(),args.sha256)
    except (ValueError,TypeError,KeyError,IndexError,OSError,OverflowError) as ex:
        print("VERDICT: INCONSISTENT_OR_UNVERIFIABLE:",ex,file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH VSC-001 SPECIFICATION")
    print("REPLAY:",json.dumps(result,sort_keys=True))
    print("LIMITATIONS: synthetic only, oracle independence and data-wall claims NOT VALIDATED")
    return 0


if __name__=="__main__":
    sys.exit(main())
