"""ASP-001 independent NumPy replayer. DOES NOT import the experiment producer.

Reconstructs all six policies, each public seed, every gradient and regulatory
signal. This shows agreement with disclosed mathematics, not physical-world
truth, neurobiology, independent authorization, or external task generalization.
"""
from __future__ import annotations
import argparse,hashlib,json,math,sys
from pathlib import Path
import numpy as np

ARMS=("sgd_001","sgd_003","sgd_009","scheduled_sgd","adam_001","regulated_sgd")
PHASES=("A1","B","A2")
STAT="EXPLORATORY_NEURAL_PLASTICITY_NOT_VALIDATED"
LIMITS=[
    "Actual small backpropagation-trained network, not an autonomous AI organism or brain",
    "Modulator is a deterministic scalar gradient-and-loss controller, not a neurotransmitter",
    "Fixed public functions and heldout grid cannot establish external task generalization",
    "Training budgets match labels and updates, not arithmetic, energy or wall-clock cost",
    "Numpy floating-point arithmetic may vary across software versions and hardware",
    "Deterministic replay checks specification agreement, not physical world truth or provenance",
    "No LLM, no subjective experience, no deployed continual learner, no research authorization",
]
CONSTANTS={
    "hidden_units":16,"trainable_parameters":49,"batch_size":16,
    "global_gradient_clip":5.0,"B_outlier_probability":.15,
    "B_outlier_amplitude":.75,"heldout_grid_size":129,
    "bootstrap_seed":7741,"bootstrap_draws":2000,
    "regulated_gain_min":.35,"regulated_gain_max":1.4,
}

def need(ok,reason):
    if not ok:raise ValueError(reason)

def unique(pairs):
    obj={}
    for k,v in pairs:
        need(k not in obj,"duplicate JSON key")
        obj[k]=v
    return obj

def no_nonfinite(k):
    raise ValueError("nonfinite JSON value: "+k)

def compare(a,b,location="evidence"):
    need(type(a) is type(b),location+": type mismatch")
    if isinstance(a,dict):
        need(set(a)==set(b),location+": schema mismatch")
        for key in a:compare(a[key],b[key],location+"."+key)
    elif isinstance(a,list):
        need(len(a)==len(b),location+": length mismatch")
        for j,(v,w) in enumerate(zip(a,b)):
            compare(v,w,location+"["+str(j)+"]")
    elif type(a) is float:
        need(math.isfinite(b) and
             math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),
             location+": numeric replay mismatch")
    else:
        need(a==b,location+": replay mismatch")

def truth_a(x):return .8*np.sin(2*np.pi*x)+.2*x
def truth_b(x):return .8*np.sin(4*np.pi*x+.3)-.2*x+.15*np.cos(np.pi*x)

def inputs_for(seed,steps):
    init_rng=np.random.default_rng(seed)
    theta=np.empty(49,dtype=np.float64)
    theta[:16]=init_rng.standard_normal(16)*.5
    theta[16:32]=0
    theta[32:48]=init_rng.standard_normal(16)*.25
    theta[48]=0
    data_rng=np.random.default_rng(seed+1_000_000)
    packs=[]
    for phase_index in range(3):
        xx=data_rng.uniform(-1,1,(steps,16,1))
        yy=truth_a(xx) if phase_index!=1 else truth_b(xx)
        altered=np.zeros_like(yy,dtype=bool)
        if phase_index==1:
            altered=data_rng.random(yy.shape)<.15
            signs=np.where(data_rng.random(yy.shape)<.5,-1.,1.)
            yy=yy+altered*signs*.75
        packs.append((xx,yy,altered))
    grid=np.linspace(-1.,1.,129,dtype=np.float64).reshape((-1,1))
    digest=hashlib.sha256(b"".join(a.tobytes() for p in packs for a in p)).hexdigest()
    return theta,packs,grid,digest

def derivatives(theta,x,target):
    weights1=theta[:16].reshape(1,16)
    offsets1=theta[16:32].reshape(1,16)
    weights2=theta[32:48].reshape(16,1)
    hidden=np.tanh(x @ weights1+offsets1)
    prediction=hidden @ weights2+theta[48]
    err=prediction-target
    value=float(np.mean(err*err))
    dy=2*err/len(x)
    hidden_delta=(dy @ weights2.T)*(1-hidden*hidden)
    g_w2=hidden.T @ dy
    g_w1=x.T @ hidden_delta
    g_b1=np.sum(hidden_delta,axis=0)
    g_b2=np.sum(dy)
    gradient=np.concatenate((g_w1.ravel(),g_b1.ravel(),g_w2.ravel(),np.array([g_b2])))
    return value,gradient

def test_metrics(theta,grid):
    hidden=np.tanh(grid@theta[:16].reshape(1,16)+theta[16:32].reshape(1,16))
    predicted=hidden@theta[32:48].reshape(16,1)+theta[48]
    return {"A_mse":float(np.mean((predicted-truth_a(grid))**2)),
            "B_mse":float(np.mean((predicted-truth_b(grid))**2))}

def independently_fit(initial,data,grid,arm,steps):
    theta=initial.copy()
    running=None
    previous=None
    moment=np.zeros(49)
    variance=np.zeros(49)
    clips=0
    log=[]
    checkpoints=[{
        "stage":"initial",**test_metrics(theta,grid),
        "parameter_sha256":hashlib.sha256(theta.tobytes()).hexdigest(),
        "parameters":theta.tolist(),
    }]
    for phase_index,phase in enumerate(PHASES):
        xx,yy,_=data[phase_index]
        for j in range(steps):
            t=phase_index*steps+j
            loss,g=derivatives(theta,xx[j],yy[j])
            size=float(np.linalg.norm(g))
            if size>5.:
                g=g*(5./size)
                clips+=1
            cosine=0.
            shock=0.
            modulation=1.
            if arm=="regulated_sgd" and previous is not None:
                cosine=float(np.dot(g,previous)/(
                    np.linalg.norm(g)*np.linalg.norm(previous)+1e-12))
                shock=float(np.clip((loss-running)/(running+.05),-2.,2.))
                modulation=float(np.clip(1+.35*cosine-.30*max(shock,0.),.35,1.4))
            if arm=="adam_001":
                moment=.9*moment+.1*g
                variance=.999*variance+.001*g*g
                eta=.01
                theta=theta-eta*(moment/(1-.9**(t+1)))/(
                    np.sqrt(variance/(1-.999**(t+1)))+1e-8)
            else:
                if arm=="sgd_001":eta=.01
                elif arm=="sgd_003":eta=.03
                elif arm=="sgd_009":eta=.09
                elif arm=="scheduled_sgd":eta=.03*(.75+.25*np.cos(np.pi*t/192))
                else:eta=.03*modulation
                theta=theta-eta*g
            need(np.all(np.isfinite(theta)) and math.isfinite(loss),"nonfinite update")
            if arm=="regulated_sgd":
                running=loss if running is None else .9*running+.1*loss
                previous=g.copy()
            log.append({
                "step":t,"phase":phase,
                "loss":loss,"gradient_norm":size,
                "modulator":modulation,
                "gradient_cosine":cosine,"positive_shock":max(shock,0.),
                "learning_rate":float(eta),
            })
        checkpoints.append({
            "stage":phase,**test_metrics(theta,grid),
            "parameter_sha256":hashlib.sha256(theta.tobytes()).hexdigest(),
            "parameters":theta.tolist(),
        })
    mods=[x["modulator"] for x in log]
    return {
        "arm":arm,"checkpoints":checkpoints,"steps":log,
        "final_parameters":theta.tolist(),
        "update_count":3*steps,"label_exposures":3*steps*16,
        "gradient_clip_count":clips,
        "modulator_min":min(mods),
        "modulator_mean":sum(mods)/len(mods),
        "modulator_max":max(mods),
        "modulator_nonunit_steps":sum(abs(x-1)>1e-12 for x in mods),
    }

def aggregate(recreated):
    by={}
    for name in ARMS:
        arms=[next(a for a in row["arms"] if a["arm"]==name) for row in recreated]
        joint=[(a["checkpoints"][2]["A_mse"]+a["checkpoints"][2]["B_mse"])/2
               for a in arms]
        by[name]={
            "joint_B_by_seed":joint,
            "joint_B_mean":float(np.mean(joint)),
            "B_mse_after_B_mean":float(np.mean([
                a["checkpoints"][2]["B_mse"] for a in arms])),
            "A_forgetting_mean":float(np.mean([
                a["checkpoints"][2]["A_mse"]-a["checkpoints"][1]["A_mse"]
                for a in arms])),
            "A_mse_after_A2_mean":float(np.mean([
                a["checkpoints"][3]["A_mse"] for a in arms])),
            "B_mse_after_A2_mean":float(np.mean([
                a["checkpoints"][3]["B_mse"] for a in arms])),
            "mean_nonunit_modulator_steps":float(np.mean([
                a["modulator_nonunit_steps"] for a in arms])),
            "mean_gradient_clips":float(np.mean([
                a["gradient_clip_count"] for a in arms])),
        }
    reg=np.asarray(by["regulated_sgd"]["joint_B_by_seed"])
    comps={}
    for baseline in ARMS:
        if baseline=="regulated_sgd":continue
        delta=reg-np.asarray(by[baseline]["joint_B_by_seed"])
        rng=np.random.default_rng(7741)
        draws=rng.integers(0,len(delta),size=(2000,len(delta)))
        values=np.mean(delta[draws],axis=1)
        comps[baseline]={
            "regulated_minus_baseline_mean":float(np.mean(delta)),
            "regulated_wins":int(np.sum(delta<0)),
            "ties":int(np.sum(delta==0)),
            "regulated_losses":int(np.sum(delta>0)),
            "paired_bootstrap_95":np.quantile(values,[.025,.975]).tolist(),
        }
    valid=all(comps[key]["regulated_minus_baseline_mean"]<0
              and comps[key]["regulated_wins"]>=13
              for key in ("sgd_003","adam_001"))
    active=all(next(a for a in row["arms"] if a["arm"]=="regulated_sgd")[
        "modulator_nonunit_steps"]>0 for row in recreated)
    return {
        "by_arm":by,"paired_comparisons":comps,
        "H1":"H1_EXPLORATORY_CRITERION_MET_NOT_VALIDATED" if valid
             else "H1_NOT_SUPPORTED_IN_THIS_FIXTURE",
        "regulation_anti_vacuity":"NONCONSTANT" if active
             else "FAILED_CONSTANT_MODULATOR",
    }

def verify(raw,pinned):
    need(type(raw) is bytes and len(raw)<18_000_000,"invalid evidence size")
    need(type(pinned) is str and len(pinned)==64 and
         all(ch in "0123456789abcdef" for ch in pinned),"invalid SHA256")
    need(hashlib.sha256(raw).hexdigest()==pinned,"SHA256 mismatch")
    doc=json.loads(raw,object_pairs_hook=unique,parse_constant=no_nonfinite)
    need(type(doc) is dict and set(doc)=={
        "protocol","status","seeds","steps_per_phase","arms","numpy_version",
        "registered_constants","runs","summary","limitations"
    },"schema mismatch")
    need(doc["protocol"]=="ASP-001" and doc["status"]==STAT,
         "invalid protocol or false validation status")
    compare(list(ARMS),doc["arms"],"arms")
    compare(LIMITS,doc["limitations"],"limitations")
    compare(CONSTANTS,doc["registered_constants"],"constants")
    need(type(doc["numpy_version"]) is str and doc["numpy_version"].startswith("2."),
         "unexpected NumPy version")
    seeds=doc["seeds"];steps=doc["steps_per_phase"]
    need(type(steps) is int and 1<=steps<=64,"invalid training steps")
    need(type(seeds) is list and 1<=len(seeds)<=24 and
         len(set(seeds))==len(seeds) and
         all(type(x) is int and x>=0 for x in seeds),"seed roster invalid")
    need((seeds==list(range(20261101,20261125)) and steps==64)
         or (seeds==[20330101] and steps==8),
         "fixture outside preregistration")
    obs=doc["runs"]
    need(type(obs) is list and len(obs)==len(seeds),"missing runs")
    rows=[]
    for i,seed in enumerate(seeds):
        initial,training,held,data_hash=inputs_for(seed,steps)
        item=obs[i]
        need(type(item) is dict and set(item)=={
            "seed","training_inputs_sha256","initial_parameters_sha256","arms"
        },"per-seed schema invalid")
        need(type(item["seed"]) is int and item["seed"]==seed,
             "wrong seed identity")
        compare(data_hash,item["training_inputs_sha256"],"training input digest")
        compare(hashlib.sha256(initial.tobytes()).hexdigest(),
                item["initial_parameters_sha256"],"initialization digest")
        need(type(item["arms"]) is list and len(item["arms"])==6,"missing arm")
        reconstructed=[]
        for j,name in enumerate(ARMS):
            expected=independently_fit(initial,training,held,name,steps)
            actual=item["arms"][j]
            for snap in actual["checkpoints"]:
                p=np.array(snap["parameters"],dtype=np.float64)
                need(len(p)==49,"checkpoint parameters missing")
                need(hashlib.sha256(p.tobytes()).hexdigest()==
                     snap["parameter_sha256"],
                     "checkpoint parameter digest mismatch")
            # Check *reported* snapshot digest from its numeric values, while
            # allowing sub-ULP independent-platform float differences.
            for k,snapshot in enumerate(expected["checkpoints"]):
                snapshot["parameter_sha256"]=actual["checkpoints"][k]["parameter_sha256"]
            compare(expected,actual,f"seed.{seed}.{name}")
            need(actual["update_count"]==3*steps and
                 actual["label_exposures"]==3*steps*16,
                 "training budget mismatch")
            reconstructed.append(expected)
        rows.append({"seed":seed,"arms":reconstructed})
    computed=aggregate(rows)
    compare(computed,doc["summary"],"summary")
    need(computed["regulation_anti_vacuity"]=="NONCONSTANT",
         "modulator vacuous")
    return {
        "verdict":"INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY",
        "seeds":len(seeds),"arms":len(ARMS),
        "update_count_per_arm":3*steps,
        "H1":computed["H1"],"status":"EXPLORATORY_NOT_VALIDATED",
        "biological_equivalence":"NOT_ESTABLISHED",
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    args=p.parse_args(argv)
    try:result=verify(args.evidence.read_bytes(),args.sha256)
    except (ValueError,TypeError,KeyError,OSError,OverflowError) as error:
        print("VERDICT: INVALID_OR_UNVERIFIABLE",error,file=sys.stderr)
        return 1
    print("VERDICT: INDEPENDENT_NUMERICAL_REPLAY_CONSISTENT_ONLY")
    print("DETAILS:",json.dumps(result,sort_keys=True))
    return 0

if __name__=="__main__":sys.exit(main())
