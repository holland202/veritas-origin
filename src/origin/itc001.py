"""ITC-001: learned recurrent latent-state computation (no human thoughts claim).

Prospective protocol: experiments/itc001/PROTOCOL.md; no outcome tuning.
NumPy is the only non-stdlib dependency. Writes fresh, immutable evidence files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
import numpy as np

TASKS=("copy1","and2","xor2","parity4","majority5","parity8")
SEEDS=tuple(range(20261161,20261167))
DEPTH=5
DIM=24
N_BITS=16
UPDATES=640
BATCH=96
TEST_PER_TASK=512
WEIGHTS=np.array([.10,.10,.15,.25,.40],dtype=np.float64)
STATUS="PUBLIC_EXPLORATORY_INTERNAL_COMPUTATION_NOT_VALIDATED"
POLICIES=("fixed1","fixed2","fixed3","fixed5","adaptive","shuffle_task","shuffle_global")
LIMITATIONS=(
    "Hidden recurrent numerical iterations are not human thoughts or conscious experiences",
    "Small fixed public binary task families do not establish general intelligence",
    "Train/test split excludes shared exact bit patterns but does not hide task definitions",
    "Adaptive halting uses uncalibrated confidence and prediction stability, not correctness",
    "Task-preserving depth shuffling is a matched allocation control, not an independent agent",
    "Matched recurrent passes are not measured joules, processor instructions or runtime",
    "Internal numerical replay shares NumPy and algorithm assumptions, not world-truth authority",
    "No external model, no autonomous tool action, no publication authorization",
)

@lru_cache(maxsize=1)
def test_split():
    table=np.zeros(1<<N_BITS,dtype=np.bool_)
    prefix=b"ITC001_SPLIT_V1:"
    for k in range(1<<N_BITS):
        table[k]=hashlib.sha256(prefix+k.to_bytes(2,"big")).digest()[0]<32
    return table

POWERS=np.array([1<<k for k in range(N_BITS)],dtype=np.int64)

def bits_code(bits):
    return (bits.astype(np.int64)@POWERS).astype(np.int64)

def task_labels(bits,task):
    if task==0: return bits[:,0].copy()
    if task==1: return (bits[:,0]&bits[:,1]).astype(np.int64)
    if task==2: return (bits[:,0]^bits[:,1]).astype(np.int64)
    if task==3: return (np.sum(bits[:,:4],axis=1)%2).astype(np.int64)
    if task==4: return (np.sum(bits[:,:5],axis=1)>=3).astype(np.int64)
    if task==5: return (np.sum(bits[:,:8],axis=1)%2).astype(np.int64)
    raise ValueError("unregistered task")

def draw_group(rng,task,count,heldout):
    bits=rng.integers(0,2,size=(count,N_BITS),dtype=np.int64)
    allowed=test_split()
    for _ in range(150):
        failed=allowed[bits_code(bits)]!=heldout
        if not np.any(failed):break
        bits[failed]=rng.integers(0,2,size=(int(np.sum(failed)),N_BITS),dtype=np.int64)
    else:raise RuntimeError("split sample selection exhausted")
    labels=task_labels(bits,task).astype(np.float64)
    tasks=np.full(count,task,dtype=np.int64)
    return bits,tasks,labels

def encode(bits,tasks):
    v=np.concatenate((2*bits.astype(np.float64)-1,
                       np.eye(len(TASKS),dtype=np.float64)[tasks]),axis=1)
    if v.shape[1]!=22:raise AssertionError("feature shape")
    return v

def draw_train_batch(rng):
    blocks=[draw_group(rng,t,16,False) for t in range(6)]
    bs=np.concatenate([r[0] for r in blocks],axis=0)
    ts=np.concatenate([r[1] for r in blocks])
    ys=np.concatenate([r[2] for r in blocks])
    assert not np.any(test_split()[bits_code(bs)])
    return encode(bs,ts),ys,bs

def draw_test(seed):
    rng=np.random.default_rng(seed+800_000)
    blocks=[draw_group(rng,t,TEST_PER_TASK,True) for t in range(6)]
    bs=np.concatenate([r[0] for r in blocks],axis=0)
    ts=np.concatenate([r[1] for r in blocks])
    ys=np.concatenate([r[2] for r in blocks])
    assert np.all(test_split()[bits_code(bs)])
    return encode(bs,ts),ys,ts,bs

def initialize(seed):
    rng=np.random.default_rng(seed)
    return {
        "Win":rng.normal(0,.7/np.sqrt(22),(22,DIM)),
        "Wr":.55*np.eye(DIM)+rng.normal(0,.012,(DIM,DIM)),
        "bias":np.zeros(DIM),
        "Wout":rng.normal(0,.25/np.sqrt(DIM),(DIM,1)),
        "bout":np.zeros(1),
    }

def serialize_parameters(params):
    return np.concatenate([params[k].ravel() for k in ("Win","Wr","bias","Wout","bout")]).astype(np.float64)

def stable_prob(logit):
    return 1/(1+np.exp(-np.clip(logit,-40,40)))

def forward(params,x):
    drive=x@params["Win"]+params["bias"]
    hs=[np.zeros((x.shape[0],DIM))]
    logits=[]
    for _ in range(DEPTH):
        hs.append(np.tanh(drive+hs[-1]@params["Wr"]))
        logits.append((hs[-1]@params["Wout"]+params["bout"]).reshape(-1))
    return hs,np.stack(logits,axis=0)

def loss_and_grad(params,x,y):
    hidden,logits=forward(params,x)
    all_p=stable_prob(logits)
    weighted_bce=np.logaddexp(0,logits)-y[None,:]*logits
    loss=float(np.mean(WEIGHTS[:,None]*weighted_bce,axis=1).sum())
    dlogits=WEIGHTS[:,None]*(all_p-y[None,:])/len(y)
    grads={key:np.zeros_like(params[key]) for key in params}
    carry=np.zeros_like(hidden[0])
    for t in range(DEPTH,0,-1):
        local=dlogits[t-1].reshape(-1,1)
        grads["Wout"]+=hidden[t].T@local
        grads["bout"]+=local.sum(axis=0)
        dh=local@params["Wout"].T+carry
        dz=dh*(1-hidden[t]*hidden[t])
        grads["Win"]+=x.T@dz
        grads["Wr"]+=hidden[t-1].T@dz
        grads["bias"]+=dz.sum(axis=0)
        carry=dz@params["Wr"].T
    return loss,grads,hidden,all_p

def train(seed,update_count=UPDATES):
    params=initialize(seed)
    init_sha=hashlib.sha256(serialize_parameters(params).tobytes()).hexdigest()
    rng=np.random.default_rng(seed+100_000)
    adam1={k:np.zeros_like(a) for k,a in params.items()}
    adam2={k:np.zeros_like(a) for k,a in params.items()}
    digest=hashlib.sha256()
    logs=[]
    for step in range(1,update_count+1):
        x,y,bits=draw_train_batch(rng)
        digest.update(bits.astype(np.uint8).tobytes())
        digest.update(y.astype(np.uint8).tobytes())
        loss,grad,_,_=loss_and_grad(params,x,y)
        norm=math.sqrt(sum(float(np.sum(g*g)) for g in grad.values()))
        if norm>5:
            for key in grad:grad[key]*=5/norm
        for key in params:
            g=grad[key]
            adam1[key]=.9*adam1[key]+.1*g
            adam2[key]=.999*adam2[key]+.001*g*g
            direction=(adam1[key]/(1-.9**step))/(
                np.sqrt(adam2[key]/(1-.999**step))+1e-8)
            params[key]=params[key]-.012*direction
            if not np.all(np.isfinite(params[key])):raise ValueError("nonfinite learning")
        if step in (1,update_count//4,update_count//2,3*update_count//4,update_count):
            logs.append({"step":step,"loss":loss,"preclip_gradient_norm":norm})
    return params,init_sha,digest.hexdigest(),logs

def scores(probs,labels,tasks):
    labels=labels.astype(np.float64)
    decisions=probs>=.5
    each=[float(np.mean(decisions[tasks==k]==labels[tasks==k])) for k in range(6)]
    return {
        "task_accuracy":each,
        "macro_accuracy":float(np.mean(each)),
        "brier":float(np.mean((probs-labels)**2)),
        "cross_entropy":float(np.mean(-labels*np.log(np.clip(probs,1e-14,1-1e-14))
                           -(1-labels)*np.log(np.clip(1-probs,1e-14,1-1e-14)))),
    }

def select_probs(all_p,depths):
    return all_p[depths-1,np.arange(all_p.shape[1])]

def policies(seed,all_p,labels,tasks):
    count=len(labels)
    adaptive=np.full(count,DEPTH,dtype=np.int64)
    previous=all_p[0]
    for depth in range(2,DEPTH):
        current=all_p[depth-1]
        elig=(np.abs(current-.5)>=.18)&(np.abs(current-previous)<=.08)
        adaptive[(adaptive==DEPTH)&elig]=depth
        previous=current
    depths={f"fixed{k}":np.full(count,k,dtype=np.int64) for k in (1,2,3,5)}
    depths["adaptive"]=adaptive
    res={}
    for name,choice in depths.items():
        pred=select_probs(all_p,choice)
        res[name]={**scores(pred,labels,tasks),
                   "mean_passes":float(np.mean(choice)),
                   "passes_by_task":[int(np.sum(choice[tasks==t])) for t in range(6)],
                   "depth_histogram":[int(np.sum(choice==d)) for d in range(1,6)],
                   "wrong_predictions":int(np.sum((pred>=.5)!=labels)),
                  }
    perms={}
    for mode in ("shuffle_task","shuffle_global"):
        accuracies=[]
        task_accs=[]
        for repetition in range(100):
            local=adaptive.copy()
            rng=np.random.default_rng((99117 if mode=="shuffle_task" else 77117)
                                      +seed*1000+repetition)
            if mode=="shuffle_task":
                for task in range(6):
                    idx=np.flatnonzero(tasks==task)
                    local[idx]=local[idx][rng.permutation(len(idx))]
            else:
                local=local[rng.permutation(count)]
            v=scores(select_probs(all_p,local),labels,tasks)
            accuracies.append(v["macro_accuracy"])
            task_accs.append(v["task_accuracy"])
        perms[mode]={"macro_accuracy":float(np.mean(accuracies)),
                     "macro_accuracy_by_repeat":accuracies,
                     "task_accuracy":np.mean(np.asarray(task_accs),axis=0).tolist(),
                     "mean_passes":float(np.mean(adaptive)),
                     "passes_by_task":res["adaptive"]["passes_by_task"]
                         if mode=="shuffle_task" else None,
                    }
    res.update(perms)
    p=select_probs(all_p,adaptive)
    early=adaptive<DEPTH
    wrong=((p>=.5)!=labels)
    res["adaptive"]["early_stop_count"]=int(np.sum(early))
    res["adaptive"]["early_incorrect_count"]=int(np.sum(early&wrong))
    res["adaptive"]["early_incorrect_by_task"]=[int(np.sum(early&wrong&(tasks==i)))
                                                       for i in range(6)]
    res["adaptive"]["early_stop_by_task"]=[int(np.sum(early&(tasks==i)))
                                             for i in range(6)]
    res["adaptive"]["fixed5_disagreements"]=int(np.sum((p>=.5)!=(all_p[-1]>=.5)))
    assert all(res["adaptive"]["passes_by_task"][i]==
               perms["shuffle_task"]["passes_by_task"][i] for i in range(6))
    return res,adaptive

def summary(seeds):
    names=POLICIES
    mean_by={name:float(np.mean([entry["policy_results"][name]["macro_accuracy"]
                                 for entry in seeds])) for name in names}
    depth_saving=float(np.mean([entry["policy_results"]["adaptive"]["mean_passes"]
                                for entry in seeds]))
    adaptive=np.asarray([x["policy_results"]["adaptive"]["macro_accuracy"] for x in seeds])
    shuffle=np.asarray([x["policy_results"]["shuffle_task"]["macro_accuracy"] for x in seeds])
    diff=adaptive-shuffle
    boot=np.random.default_rng(88019).integers(0,len(seeds),size=(2000,len(seeds)))
    bootstrap=np.quantile(np.mean(diff[boot],axis=1),[.025,.975]).tolist()
    h1=(mean_by["fixed5"]-mean_by["fixed1"]>=.02)
    h2=(float(np.mean(diff))>=.01 and int(np.sum(diff>0))>=4
        and depth_saving<=4.0 and
        mean_by["fixed5"]-mean_by["adaptive"]<=.01)
    return {
        "macro_accuracy_by_policy":mean_by,
        "fixed5_minus_fixed1":mean_by["fixed5"]-mean_by["fixed1"],
        "adaptive_minus_task_shuffle":float(np.mean(diff)),
        "adaptive_vs_shuffled_paired_wins":int(np.sum(diff>0)),
        "adaptive_vs_shuffled_paired_losses":int(np.sum(diff<0)),
        "adaptive_mean_passes":depth_saving,
        "paired_bootstrap_95":bootstrap,
        "H1":"H1_EXPLORATORY_THRESHOLD_MET_NOT_VALIDATED" if h1 else "H1_NOT_SUPPORTED",
        "H2":"H2_EXPLORATORY_THRESHOLD_MET_NOT_VALIDATED" if h2 else "H2_NOT_SUPPORTED",
    }

def run(seeds=SEEDS,updates=UPDATES,n_test=TEST_PER_TASK):
    if tuple(seeds)!=SEEDS or updates!=UPDATES or n_test!=TEST_PER_TASK:
        raise ValueError("only preregistered confirmatory-shaped exploratory run supported")
    records=[]
    for seed in seeds:
        params,initial_sha,data_sha,train_logs=train(seed,updates)
        x,y,tasks,bits=draw_test(seed)
        hs,logits=forward(params,x)
        probs=stable_prob(logits)
        results,depths=policies(seed,probs,y,tasks)
        hidden_deltas=[float(np.mean(np.linalg.norm(hs[i]-hs[i-1],axis=1)))
                       for i in range(1,DEPTH+1)]
        records.append({
            "seed":seed,
            "initial_parameters_sha256":initial_sha,
            "training_stream_sha256":data_sha,
            "test_bits_sha256":hashlib.sha256(bits.astype(np.uint8).tobytes()).hexdigest(),
            "final_weights":{k:v.tolist() for k,v in params.items()},
            "final_weights_sha256":hashlib.sha256(serialize_parameters(params).tobytes()).hexdigest(),
            "training_checkpoints":train_logs,
            "policy_results":results,
            "probabilities_by_depth":probs.tolist(),
            "selected_depths":depths.tolist(),
            "hidden_delta_norm":hidden_deltas,
            "test_pattern_codes":bits_code(bits).tolist(),
            "test_targets":y.astype(np.int64).tolist(),
            "test_task_ids":tasks.tolist(),
        })
    return {
        "protocol":"ITC-001",
        "status":STATUS,
        "base_branch_commit":"905021915ae1cb32027f8ffcac60d2efb675f055",
        "registered_constants":{
            "seeds":list(SEEDS),"training_updates":UPDATES,"train_batch":BATCH,
            "test_count_per_task":TEST_PER_TASK,"recurrent_depth_max":DEPTH,
            "hidden_dim":DIM,"trainable_parameters":1153,
            "deep_supervision_weights":WEIGHTS.tolist(),
            "halt_confidence_distance":.18,"halt_stability_change":.08,
            "halt_earliest_depth":2,"task_shuffle_repetitions":100,
            "bootstrap_repetitions":2000,"bootstrap_seed":88019,
            "split_rule":"sha256('ITC001_SPLIT_V1:'+16_bit_big_endian_value)[0] < 32",
            "bit_encoding":"little_endian_weighted_sum_bits_0_to_15",
        },
        "numpy_version":np.__version__,
        "seed_records":records,
        "aggregate":summary(records),
        "limitations":list(LIMITATIONS),
    }

def save_new(obj,folder):
    folder.mkdir(parents=True,exist_ok=True)
    name="itc001-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+uuid.uuid4().hex[:8]+".json"
    target=folder/name
    raw=(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    with target.open("xb") as f:f.write(raw)
    return target,hashlib.sha256(raw).hexdigest()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--output-dir",type=Path,default=Path("evidence/itc001"))
    args=p.parse_args(argv)
    if not args.pilot:p.error("REFUSE: --pilot required; never silently run training")
    experiment=run()
    path,sha=save_new(experiment,args.output_dir)
    print("EVIDENCE:",path)
    print("SHA256:",sha)
    print("AGGREGATE:",json.dumps(experiment["aggregate"],sort_keys=True))
    print("STATUS:",STATUS)
    return 0

if __name__=="__main__":sys.exit(main())
