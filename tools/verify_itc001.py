"""ITC-001 independently authored numerical replay (no runner import).

Verifies full recurrent weights by repeating optimization; recomputes all toy
labels, logits, halt decisions, cost-matched shuffles and registered outcomes.
Consistency with published math is not independent scientific validation.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from functools import lru_cache
from pathlib import Path
import numpy as np

SEEDS=list(range(20261161,20261167))
NAMES=("copy1","and2","xor2","parity4","majority5","parity8")
W=np.asarray((.1,.1,.15,.25,.4),dtype=np.float64)
EXPECTED=("fixed1","fixed2","fixed3","fixed5","adaptive","shuffle_task","shuffle_global")
LIMITS=(
    "Hidden recurrent numerical iterations are not human thoughts or conscious experiences",
    "Small fixed public binary task families do not establish general intelligence",
    "Train/test split excludes shared exact bit patterns but does not hide task definitions",
    "Adaptive halting uses uncalibrated confidence and prediction stability, not correctness",
    "Task-preserving depth shuffling is a matched allocation control, not an independent agent",
    "Matched recurrent passes are not measured joules, processor instructions or runtime",
    "Internal numerical replay shares NumPy and algorithm assumptions, not world-truth authority",
    "No external model, no autonomous tool action, no publication authorization",
)


def demand(ok,description):
    if not ok:raise ValueError(description)

def unique(pairs):
    obj={}
    for key,val in pairs:
        demand(key not in obj,"duplicate JSON keys")
        obj[key]=val
    return obj

def fail_constant(k):raise ValueError("nonfinite JSON value "+k)

def check(expected,observed,context="evidence"):
    demand(type(expected) is type(observed),context+": type mismatch")
    if isinstance(expected,dict):
        demand(set(expected)==set(observed),context+": key set mismatch")
        for key in expected:check(expected[key],observed[key],context+"."+key)
    elif isinstance(expected,list):
        demand(len(expected)==len(observed),context+": array length mismatch")
        for i,(left,right) in enumerate(zip(expected,observed)):
            check(left,right,context+f"[{i}]")
    elif type(expected) is float:
        demand(math.isfinite(observed) and
               math.isclose(expected,observed,rel_tol=2e-8,abs_tol=1e-9),
               context+": numeric replay mismatch")
    else:demand(expected==observed,context+": mismatch")

@lru_cache(None)
def reserved_input_patterns():
    return np.fromiter((hashlib.sha256(b"ITC001_SPLIT_V1:"+i.to_bytes(2,"big")).digest()[0]<32
                        for i in range(65536)),dtype=bool,count=65536)


def bits_to_index(bits):
    # Note: little endian vector -> 16-bit integer, hashed big-endian bytes.
    return np.sum(bits*(1<<np.arange(16,dtype=np.int64)),axis=1,dtype=np.int64)

def labels_for(bits,task):
    b=bits
    formulas=[b[:,0],b[:,0]&b[:,1],b[:,0]^b[:,1],
              b[:,:4].sum(axis=1)%2,(b[:,:5].sum(axis=1)>2).astype(np.int64),
              b[:,:8].sum(axis=1)%2]
    return np.asarray(formulas[task],dtype=np.float64)

def generate_bits(rng,task,size,heldout):
    bits=rng.integers(0,2,size=(size,16),dtype=np.int64)
    for _ in range(150):
        bad=reserved_input_patterns()[bits_to_index(bits)] != heldout
        n=int(np.count_nonzero(bad))
        if n==0:break
        bits[bad,:]=rng.integers(0,2,size=(n,16),dtype=np.int64)
    else:raise ValueError("unable to generate split samples")
    return bits,labels_for(bits,task)

def assemble(rng,n,heldout):
    bs=[];ts=[];ys=[]
    for group in range(6):
        b,y=generate_bits(rng,group,n,heldout)
        bs.append(b);ys.append(y);ts.append(np.repeat(group,n))
    bits=np.vstack(bs)
    tasks=np.concatenate(ts)
    target=np.concatenate(ys)
    features=np.zeros((len(bits),22),dtype=np.float64)
    features[:,:16]=2*bits-1
    features[np.arange(len(bits)),16+tasks]=1.0
    return bits,tasks,target,features

def seed_parameters(seed):
    rng=np.random.default_rng(seed)
    wi=rng.normal(0,.7/math.sqrt(22),(22,24))
    wr=np.eye(24)*.55+rng.normal(0,.012,(24,24))
    wo=rng.normal(0,.25/math.sqrt(24),(24,1))
    return [wi,wr,np.zeros(24),wo,np.zeros(1)]

def serialize(theta):return np.concatenate([v.ravel() for v in theta]).tobytes()

def latent(theta,features):
    wi,wr,bs,wo,bo=theta
    affine=np.add(features@wi,bs)
    states=[np.zeros((len(features),24))]
    output=[]
    for t in range(5):
        states.append(np.tanh(affine+states[-1]@wr))
        output.append((states[-1]@wo+bo).reshape(len(features)))
    return states,np.stack(output)

def derivative(theta,features,target):
    wi,wr,bs,wo,bo=theta
    states,output=latent(theta,features)
    sigmoid=1/(1+np.exp(-np.clip(output,-40,40)))
    loss=float(np.mean(W[:,None]*(np.logaddexp(0,output)-target[None,:]*output),axis=1).sum())
    grads=[np.zeros_like(a) for a in theta]
    propagated=np.zeros((len(features),24))
    for i in (4,3,2,1,0):
        dl=(W[i]*(sigmoid[i]-target)/len(target)).reshape(-1,1)
        grads[3]+=np.matmul(states[i+1].T,dl)
        grads[4]+=np.sum(dl,axis=0)
        hidden_grad=np.matmul(dl,wo.T)+propagated
        core_grad=hidden_grad*(1-np.square(states[i+1]))
        grads[0]+=features.T@core_grad
        grads[1]+=states[i].T@core_grad
        grads[2]+=np.sum(core_grad,axis=0)
        propagated=core_grad@wr.T
    return loss,grads

def fit(seed,num_updates=640):
    params=seed_parameters(seed)
    init_hash=hashlib.sha256(serialize(params)).hexdigest()
    generator=np.random.default_rng(seed+100_000)
    first=[np.zeros_like(p) for p in params]
    second=[np.zeros_like(p) for p in params]
    trace=[]
    hasher=hashlib.sha256()
    for step in range(1,num_updates+1):
        bits,task,labels,x=assemble(generator,16,False)
        demand(not np.any(reserved_input_patterns()[bits_to_index(bits)]),"training leaked withheld pattern")
        hasher.update(bits.astype(np.uint8).tobytes())
        hasher.update(labels.astype(np.uint8).tobytes())
        loss,grads=derivative(params,x,labels)
        scale=math.sqrt(sum(float(np.sum(a*a)) for a in grads))
        if scale>5:
            grads=[g*(5/scale) for g in grads]
        for i in range(len(params)):
            first[i]=.9*first[i]+.1*grads[i]
            second[i]=.999*second[i]+.001*grads[i]*grads[i]
            m=first[i]/(1-.9**step)
            v=second[i]/(1-.999**step)
            direction=m/(np.sqrt(v)+1e-8)
            params[i]=params[i]-.012*direction
            demand(np.all(np.isfinite(params[i])),"nonfinite training")
        if step in (1,160,320,480,640):
            trace.append({"step":step,"loss":loss,"preclip_gradient_norm":scale})
    return params,init_hash,hasher.hexdigest(),trace

def probs_of(theta,x):
    states,logits=latent(theta,x)
    probabilities=1/(1+np.exp(-np.clip(logits,-40,40)))
    transitions=[float(np.mean(np.linalg.norm(states[i]-states[i-1],axis=1)))
                 for i in range(1,6)]
    return probabilities,transitions

def measure(probs,labels,tasks):
    correct=(probs>=.5)==labels
    by=[float(np.mean(correct[tasks==t])) for t in range(6)]
    safe=np.clip(probs,1e-14,1-1e-14)
    return {"task_accuracy":by,
            "macro_accuracy":float(np.mean(by)),
            "brier":float(np.mean((probs-labels)**2)),
            "cross_entropy":float(np.mean(-labels*np.log(safe)-(1-labels)*np.log1p(-safe)))}

def pick(table,depth):return np.take_along_axis(table,(depth-1)[None,:],axis=0)[0]

def derive_policies(seed,table,labels,tasks):
    count=len(labels)
    stop=np.repeat(5,count).astype(np.int64)
    for t in (2,3,4):
        current=table[t-1]
        prior=table[t-2]
        threshold=(np.abs(current-.5)>=.18)&(np.abs(current-prior)<=.08)
        stop[(stop==5)&threshold]=t
    output={}
    for t in (1,2,3,5):
        depths=np.full(count,t,dtype=np.int64)
        prediction=pick(table,depths)
        output[f"fixed{t}"]={**measure(prediction,labels,tasks),
            "mean_passes":float(np.mean(depths)),
            "passes_by_task":[int(np.sum(depths[tasks==task])) for task in range(6)],
            "depth_histogram":[int(np.sum(depths==d)) for d in range(1,6)],
            "wrong_predictions":int(np.sum((prediction>=.5)!=labels))}
    prediction=pick(table,stop)
    output["adaptive"]={**measure(prediction,labels,tasks),
            "mean_passes":float(np.mean(stop)),
            "passes_by_task":[int(np.sum(stop[tasks==task])) for task in range(6)],
            "depth_histogram":[int(np.sum(stop==d)) for d in range(1,6)],
            "wrong_predictions":int(np.sum((prediction>=.5)!=labels))}
    for kind in ("shuffle_task","shuffle_global"):
        all_scores=[]
        all_task_scores=[]
        for repetition in range(100):
            seed_for_shuffle=(99117 if kind=="shuffle_task" else 77117)+seed*1000+repetition
            random=np.random.default_rng(seed_for_shuffle)
            depths=stop.copy()
            if kind=="shuffle_task":
                for task in range(6):
                    index=np.nonzero(tasks==task)[0]
                    depths[index]=depths[index][random.permutation(len(index))]
            else:depths=depths[random.permutation(len(depths))]
            metrics=measure(pick(table,depths),labels,tasks)
            all_scores.append(metrics["macro_accuracy"])
            all_task_scores.append(metrics["task_accuracy"])
        output[kind]={
            "macro_accuracy":float(np.mean(all_scores)),
            "macro_accuracy_by_repeat":all_scores,
            "task_accuracy":np.mean(np.asarray(all_task_scores),axis=0).tolist(),
            "mean_passes":float(np.mean(stop)),
            "passes_by_task":output["adaptive"]["passes_by_task"]
                             if kind=="shuffle_task" else None,
        }
    early=stop<5
    wrong=(prediction>=.5)!=labels
    output["adaptive"].update({
        "early_stop_count":int(np.sum(early)),
        "early_incorrect_count":int(np.sum(early&wrong)),
        "early_incorrect_by_task":[int(np.sum(early&wrong&(tasks==task)))
                                   for task in range(6)],
        "early_stop_by_task":[int(np.sum(early&(tasks==task)))
                              for task in range(6)],
        "fixed5_disagreements":int(np.sum((prediction>=.5)!=(table[-1]>=.5))),
    })
    return output,stop

def total_summary(rows):
    policies=("fixed1","fixed2","fixed3","fixed5","adaptive","shuffle_task","shuffle_global")
    scores={name:float(np.mean([r["policy_results"][name]["macro_accuracy"] for r in rows]))
            for name in policies}
    adaptive=np.asarray([r["policy_results"]["adaptive"]["macro_accuracy"] for r in rows])
    shuffled=np.asarray([r["policy_results"]["shuffle_task"]["macro_accuracy"] for r in rows])
    delta=adaptive-shuffled
    mean_passes=float(np.mean([r["policy_results"]["adaptive"]["mean_passes"] for r in rows]))
    indices=np.random.default_rng(88019).integers(0,len(rows),size=(2000,len(rows)))
    ci=np.quantile(np.mean(delta[indices],axis=1),(.025,.975)).tolist()
    h1=(scores["fixed5"]-scores["fixed1"])>=.02
    h2=(float(np.mean(delta))>=.01 and int(np.sum(delta>0))>=4
        and mean_passes<=4 and scores["fixed5"]-scores["adaptive"]<=.01)
    return {
        "macro_accuracy_by_policy":scores,
        "fixed5_minus_fixed1":scores["fixed5"]-scores["fixed1"],
        "adaptive_minus_task_shuffle":float(np.mean(delta)),
        "adaptive_vs_shuffled_paired_wins":int(np.sum(delta>0)),
        "adaptive_vs_shuffled_paired_losses":int(np.sum(delta<0)),
        "adaptive_mean_passes":mean_passes,
        "paired_bootstrap_95":ci,
        "H1":"H1_EXPLORATORY_THRESHOLD_MET_NOT_VALIDATED" if h1 else "H1_NOT_SUPPORTED",
        "H2":"H2_EXPLORATORY_THRESHOLD_MET_NOT_VALIDATED" if h2 else "H2_NOT_SUPPORTED",
    }

def verify(raw,sha):
    demand(type(raw) is bytes and len(raw)<=15_000_000,"bounded evidence bytes expected")
    demand(type(sha) is str and len(sha)==64 and all(x in "0123456789abcdef" for x in sha),"invalid SHA256")
    demand(hashlib.sha256(raw).hexdigest()==sha,"SHA256 mismatch")
    info=json.loads(raw,object_pairs_hook=unique,parse_constant=fail_constant)
    demand(type(info) is dict and set(info)=={
        "protocol","status","base_branch_commit","registered_constants", "numpy_version",
        "seed_records","aggregate","limitations"},"top-level schema mismatch")
    demand(info["protocol"]=="ITC-001" and
           info["status"]=="PUBLIC_EXPLORATORY_INTERNAL_COMPUTATION_NOT_VALIDATED",
           "invalid protocol or attempted validation promotion")
    demand(info["base_branch_commit"]=="905021915ae1cb32027f8ffcac60d2efb675f055",
           "wrong repository base")
    demand(type(info["numpy_version"]) is str and info["numpy_version"].startswith("2."),
           "unexpected NumPy version")
    check({
        "seeds":SEEDS,"training_updates":640,"train_batch":96,
        "test_count_per_task":512,"recurrent_depth_max":5,
        "hidden_dim":24,"trainable_parameters":1153,
        "deep_supervision_weights":[.1,.1,.15,.25,.4],
        "halt_confidence_distance":.18,"halt_stability_change":.08,
        "halt_earliest_depth":2,"task_shuffle_repetitions":100,
        "bootstrap_repetitions":2000,"bootstrap_seed":88019,
        "split_rule":"sha256('ITC001_SPLIT_V1:'+16_bit_big_endian_value)[0] < 32",
        "bit_encoding":"little_endian_weighted_sum_bits_0_to_15",
    },info["registered_constants"],"constants")
    check(list(LIMITS),info["limitations"],"scope")
    rows=info["seed_records"]
    demand(type(rows) is list and len(rows)==len(SEEDS),"missing seed record")
    rebuilt=[]
    for i,seed in enumerate(SEEDS):
        row=rows[i]
        demand(type(row) is dict and set(row)=={
            "seed","initial_parameters_sha256","training_stream_sha256","test_bits_sha256",
            "final_weights","final_weights_sha256","training_checkpoints","policy_results",
            "probabilities_by_depth","selected_depths","hidden_delta_norm",
            "test_pattern_codes","test_targets","test_task_ids"},"seed record schema mismatch")
        demand(type(row["seed"]) is int and row["seed"]==seed,"seed mismatch")
        learned,sha_start,sha_train,logs=fit(seed)
        check(sha_start,row["initial_parameters_sha256"],"init digest")
        check(sha_train,row["training_stream_sha256"],"training stream digest")
        for k,v in zip(("Win","Wr","bias","Wout","bout"),learned):
            array=np.asarray(row["final_weights"][k],dtype=np.float64)
            demand(array.shape==v.shape,"weight shape mismatch")
            demand(np.allclose(array,v,atol=1e-8,rtol=1e-8),"learned weights mismatch")
        flat=np.concatenate([np.asarray(row["final_weights"][key]).ravel()
                             for key in ("Win","Wr","bias","Wout","bout")])
        check(hashlib.sha256(flat.tobytes()).hexdigest(),row["final_weights_sha256"],
              "serialized learned weights SHA256")
        check(logs,row["training_checkpoints"],"training trace")
        random=np.random.default_rng(seed+800_000)
        bits,tasks,labels,x=assemble(random,512,True)
        demand(np.all(reserved_input_patterns()[bits_to_index(bits)]),"test split contaminated")
        check(hashlib.sha256(bits.astype(np.uint8).tobytes()).hexdigest(),
              row["test_bits_sha256"],"test bits digest")
        check(bits_to_index(bits).tolist(),row["test_pattern_codes"],"withheld bits codes")
        check(tasks.tolist(),row["test_task_ids"],"test tasks")
        check(labels.astype(np.int64).tolist(),row["test_targets"],"test targets")
        probs,trajectory=probs_of(learned,x)
        check(probs.tolist(),row["probabilities_by_depth"],"five internal predictions")
        check(trajectory,row["hidden_delta_norm"],"internal state trajectory")
        results,stopping=derive_policies(seed,probs,labels,tasks)
        check(results,row["policy_results"],"matched stopping policy outcomes")
        check(stopping.tolist(),row["selected_depths"],"halting decision")
        demand(np.max(stopping)<=5 and np.min(stopping)>=2,"invalid halting depth")
        rebuilt.append({"policy_results":results})
    check(total_summary(rebuilt),info["aggregate"],"registered summary")
    return {"verdict":"INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY",
            "seeds":len(SEEDS),"total_test_decisions":len(SEEDS)*6*512,
            "model_params":1153,"H1":info["aggregate"]["H1"],
            "H2":info["aggregate"]["H2"],
            "authority":"NONE","human_thought":"NOT_ESTABLISHED"}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    args=p.parse_args(argv)
    try:result=verify(args.evidence.read_bytes(),args.sha256)
    except (ValueError,TypeError,KeyError,IndexError,OSError,OverflowError) as exc:
        print("VERDICT: INVALID_OR_UNVERIFIABLE",exc,file=sys.stderr);return 1
    print("VERDICT: INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY")
    print("RESULT:",json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":sys.exit(main())
