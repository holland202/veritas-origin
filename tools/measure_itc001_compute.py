"""ITC-001 post-hoc *engineering* validation of real early exiting.

Separate from frozen preregistered training/primary analysis.
Uses learned weights + heldout inputs, never labels, to choose halt depths.
Actual masked recurrence must reproduce archived stopping choices exactly.
Does NOT establish a statistical-computational complexity threshold.
"""
from __future__ import annotations
import argparse,hashlib,json,platform,statistics,sys,time
from pathlib import Path
import numpy as np

def sigmoid(value):
    return 1/(1+np.exp(-np.clip(value,-40,40)))

def run_dense(theta,features,passes):
    drive=features@theta["Win"]+theta["bias"]
    state=np.zeros((len(features),24),dtype=np.float64)
    for _ in range(passes):
        state=np.tanh(drive+state@theta["Wr"])
    return sigmoid((state@theta["Wout"]+theta["bout"]).reshape(-1))

def run_adaptive_masked(theta,features):
    """Computes only the recurrent passes for rows that have not yet halted."""
    n=len(features)
    affine=features@theta["Win"]+theta["bias"]
    state=np.zeros((n,24),dtype=np.float64)
    predicted=np.empty(n,dtype=np.float64)
    depths=np.zeros(n,dtype=np.int64)
    previous=np.zeros(n,dtype=np.float64)
    active=np.arange(n,dtype=np.int64)
    for t in range(1,6):
        if len(active)==0:break
        idx=active
        new_hidden=np.tanh(affine[idx]+state[idx]@theta["Wr"])
        state[idx]=new_hidden
        value=sigmoid((new_hidden@theta["Wout"]+theta["bout"]).reshape(-1))
        predicted[idx]=value
        if t==1:
            previous[idx]=value
            continue
        if t<5:
            stop=(np.abs(value-.5)>=.18)&(np.abs(value-previous[idx])<=.08)
        else:
            stop=np.ones(len(idx),dtype=bool)
        depths[idx[stop]]=t
        previous[idx[~stop]]=value[~stop]
        active=idx[~stop]
    if not np.all((depths>=2)&(depths<=5)):
        raise ValueError("masked halting depth out of allowed range")
    return predicted,depths

def benchmark(evidence,repetitions=7):
    if type(repetitions) is not int or not 1<=repetitions<=30:
        raise ValueError("repetitions must be 1..30")
    dataset=[]
    for r in evidence["seed_records"]:
        # Unique 16-bit codes and task IDs reconstruct original model inputs;
        # test targets are never read by halting.
        bits=np.asarray(r["test_pattern_codes"],dtype=np.int64)
        tasks=np.asarray(r["test_task_ids"],dtype=np.int64)
        if bits.shape!=(3072,) or tasks.shape!=(3072,):
            raise ValueError("invalid archive test samples")
        patterns=((bits[:,None]>>np.arange(16))&1).astype(np.float64)
        features=np.zeros((len(bits),22),dtype=np.float64)
        features[:,:16]=2*patterns-1
        features[np.arange(len(bits)),16+tasks]=1.
        theta={k:np.asarray(v,dtype=np.float64) for k,v in r["final_weights"].items()}
        prob,steps=run_adaptive_masked(theta,features)
        reference=np.asarray(r["probabilities_by_depth"],dtype=np.float64)
        expected=np.asarray(r["selected_depths"],dtype=np.int64)
        if not np.array_equal(steps,expected):
            raise ValueError("real masked halting differs from archived depth")
        if not np.allclose(prob,reference[expected-1,np.arange(len(bits))],
                           rtol=0,atol=1e-12):
            raise ValueError("masked result differs from counterfactual archive")
        if int(np.sum(steps))!=sum(int(v) for v in
                                  r["policy_results"]["adaptive"]["passes_by_task"]):
            raise ValueError("computed recurrent update count does not match budget")
        if not np.allclose(run_dense(theta,features,5),reference[4],
                           rtol=0,atol=1e-12):
            raise ValueError("fixed-5 real forward differs from archived predictions")
        dataset.append((r["seed"],features,theta,int(np.sum(steps)),
                        int(np.sum(steps<5))))
    records=[]
    for seed,x,theta,passes,early in dataset:
        samples={}
        for label,call in (
            ("fixed3",lambda:run_dense(theta,x,3)),
            ("fixed5",lambda:run_dense(theta,x,5)),
            ("adaptive_masked",lambda:run_adaptive_masked(theta,x)),
        ):
            call()  # warm-up, not included in measurement
            times=[]
            for _ in range(repetitions):
                t=time.perf_counter_ns()
                call()
                times.append((time.perf_counter_ns()-t)/1e6)
            samples[label+"_median_ms"]=float(statistics.median(times))
        records.append({
            "seed":seed,"actual_adaptive_recurrent_passes":passes,
            "fixed3_recurrent_passes":3*len(x),
            "fixed5_recurrent_passes":5*len(x),
            "adaptive_early_count":early,**samples,
        })
    return {
        "protocol":"ITC-001-POSTHOC-COMPUTE-AUDIT",
        "epistemic_status":"EXPLORATORY_POST_HOC_ENGINEERING_NOT_VALIDATED",
        "numpy_version":np.__version__,
        "python_version":platform.python_version(),
        "platform":platform.platform(),
        "benchmark_repetitions":repetitions,
        "fixed5_vs_adaptive_pass_ratio":sum(r["actual_adaptive_recurrent_passes"]
                                            for r in records)/
                                        sum(r["fixed5_recurrent_passes"]
                                            for r in records),
        "execution":"REAL_MASKED_RECURRENCE_VERIFIED_AGAINST_ARCHIVED_PREDICTIONS",
        "wall_time_not_comparable_across_hardware":True,
        "records":records,
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--repetitions",type=int,default=7)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args(argv)
    raw=args.evidence.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.sha256:
        p.error("evidence SHA256 mismatch")
    data=json.loads(raw)
    if data["protocol"]!="ITC-001" or data["status"]!="PUBLIC_EXPLORATORY_INTERNAL_COMPUTATION_NOT_VALIDATED":
        p.error("not an original ITC-001 exploratory archive")
    report=benchmark(data,args.repetitions)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    path=args.output_dir/"itc001_posthoc_actual_compute_audit.json"
    with path.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,indent=2,sort_keys=True)
        stream.write("\n")
    print("AUDIT:",path)
    print("SHA256:",hashlib.sha256(path.read_bytes()).hexdigest())
    print("PASSES_RATIO:",report["fixed5_vs_adaptive_pass_ratio"])
    for row in report["records"]:
        print("SEED:",row["seed"],
              "adaptive_passes:",row["actual_adaptive_recurrent_passes"],
              "fixed5_passes:",row["fixed5_recurrent_passes"],
              "adaptive_ms:",row["adaptive_masked_median_ms"],
              "fixed5_ms:",row["fixed5_median_ms"])
    return 0

if __name__=="__main__":sys.exit(main())
