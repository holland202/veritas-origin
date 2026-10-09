"""ASP-001: a genuine NumPy 1->16 tanh->1 neural network with internally regulated learning.
Exploratory: not biological equivalence, a model of consciousness, or validated improvement.
See experiments/asp001/PROTOCOL.md, registered before implementation.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

PROTOCOL="ASP-001"
STATUS="EXPLORATORY_NEURAL_PLASTICITY_NOT_VALIDATED"
SEEDS=tuple(range(20261101,20261125))
ARMS=("sgd_001","sgd_003","sgd_009","scheduled_sgd","adam_001","regulated_sgd")
PHASES=("A1","B","A2")
PARAMS=49
BATCH=16
TRAIN_STEPS=64
CLIP=5.0
BOOTS=2000
BOOT_SEED=7741
LIMITATIONS=(
    "Actual small backpropagation-trained network, not an autonomous AI organism or brain",
    "Modulator is a deterministic scalar gradient-and-loss controller, not a neurotransmitter",
    "Fixed public functions and heldout grid cannot establish external task generalization",
    "Training budgets match labels and updates, not arithmetic, energy or wall-clock cost",
    "Numpy floating-point arithmetic may vary across software versions and hardware",
    "Deterministic replay checks specification agreement, not physical world truth or provenance",
    "No LLM, no subjective experience, no deployed continual learner, no research authorization",
)

def a_function(x):
    return .8*np.sin(2*np.pi*x)+.2*x

def b_function(x):
    return .8*np.sin(4*np.pi*x+.3)-.2*x+.15*np.cos(np.pi*x)

def make_seed(seed,phase_steps=TRAIN_STEPS):
    if type(seed) is not int or seed<0 or seed>=2**62: raise ValueError("invalid seed")
    if type(phase_steps) is not int or not 1<=phase_steps<=64:
        raise ValueError("invalid phase steps")
    initial=np.random.default_rng(seed)
    parameters=np.concatenate((
        (.5*initial.standard_normal((1,16))).reshape(-1),
        np.zeros(16),
        (.25*initial.standard_normal((16,1))).reshape(-1),
        np.zeros(1),
    ))
    stream=np.random.default_rng(seed+1_000_000)
    training=[]
    for i in range(3):
        xs=stream.uniform(-1,1,(phase_steps,BATCH,1))
        ys=a_function(xs) if i!=1 else b_function(xs)
        corrupt=np.zeros_like(ys,dtype=bool)
        if i==1:
            corrupt=stream.random(ys.shape)<.15
            signs=np.where(stream.random(ys.shape)<.5,-1.,1.)
            ys=ys+corrupt*signs*.75
        training.append((xs,ys,corrupt))
    held=np.linspace(-1.,1.,129,dtype=np.float64).reshape((-1,1))
    return parameters,training,held

def predict(p,x):
    h=np.tanh(x @ p[:16].reshape(1,16)+p[16:32].reshape(1,16))
    return h @ p[32:48].reshape(16,1)+p[48]

def backprop(p,x,target):
    h=np.tanh(x @ p[:16].reshape(1,16)+p[16:32].reshape(1,16))
    err=h @ p[32:48].reshape(16,1)+p[48]-target
    loss=float(np.mean(err*err))
    dy=2.*err/len(x)
    dw2=h.T @ dy
    db2=np.sum(dy)
    dh=(dy @ p[32:48].reshape(16,1).T)*(1-h*h)
    dw1=x.T @ dh
    db1=np.sum(dh,axis=0)
    grad=np.concatenate((dw1.ravel(),db1.ravel(),dw2.ravel(),np.array([db2])))
    return loss,grad

def evaluate(p,grid):
    pred=predict(p,grid)
    return {
        "A_mse":float(np.mean((pred-a_function(grid))**2)),
        "B_mse":float(np.mean((pred-b_function(grid))**2)),
    }

def train_arm(seed,name,init,batches,eval_grid,phase_steps):
    if name not in ARMS: raise ValueError("unknown optimizer arm")
    p=init.copy()
    steps_total=3*phase_steps
    loss_ema=None
    prev_gradient=None
    moment=np.zeros(PARAMS)
    second=np.zeros(PARAMS)
    history=[{
        "stage":"initial",**evaluate(p,eval_grid),
        "parameter_sha256":hashlib.sha256(p.tobytes()).hexdigest(),
        "parameters":p.tolist(),
    }]
    records=[]
    clips=0
    for phase_index,phase in enumerate(PHASES):
        xs,ys,_=batches[phase_index]
        for j in range(phase_steps):
            t=phase_index*phase_steps+j
            loss,grad=backprop(p,xs[j],ys[j])
            gradient_norm=float(np.linalg.norm(grad))
            if gradient_norm>CLIP:
                grad=grad*(CLIP/gradient_norm)
                clips+=1
            cos=0.
            shock=0.
            mod=1.
            if name=="regulated_sgd" and prev_gradient is not None:
                cos=float(np.dot(grad,prev_gradient)/(
                    np.linalg.norm(grad)*np.linalg.norm(prev_gradient)+1e-12))
                shock=float(np.clip((loss-loss_ema)/(loss_ema+.05),-2.,2.))
                mod=float(np.clip(1+.35*cos-.30*max(shock,0.),.35,1.4))
            if name=="adam_001":
                moment=.9*moment+.1*grad
                second=.999*second+.001*grad*grad
                k=t+1
                effective=.01
                change=effective*(moment/(1-.9**k))/(
                    np.sqrt(second/(1-.999**k))+1e-8)
            else:
                if name=="sgd_001": effective=.01
                elif name=="sgd_003": effective=.03
                elif name=="sgd_009": effective=.09
                elif name=="scheduled_sgd":
                    effective=.03*(.75+.25*np.cos(np.pi*t/192))
                else: effective=.03*mod
                change=effective*grad
            p=p-change
            if not np.all(np.isfinite(p)) or not math.isfinite(loss):
                raise ValueError("non-finite learned parameters/loss")
            if name=="regulated_sgd":
                loss_ema=loss if loss_ema is None else .9*loss_ema+.1*loss
                prev_gradient=grad.copy()
            records.append({
                "step":t,"phase":phase,"loss":loss,
                "gradient_norm":gradient_norm,"modulator":mod,
                "gradient_cosine":cos,"positive_shock":max(shock,0.),
                "learning_rate":float(effective),
            })
        history.append({
            "stage":phase,**evaluate(p,eval_grid),
            "parameter_sha256":hashlib.sha256(p.tobytes()).hexdigest(),
            "parameters":p.tolist(),
        })
    regs=[step["modulator"] for step in records]
    return {
        "arm":name,"checkpoints":history,"steps":records,
        "final_parameters":p.tolist(),
        "update_count":steps_total,"label_exposures":steps_total*BATCH,
        "gradient_clip_count":clips,
        "modulator_min":min(regs),
        "modulator_mean":sum(regs)/len(regs),
        "modulator_max":max(regs),
        "modulator_nonunit_steps":sum(abs(v-1)>1e-12 for v in regs),
    }

def seed_result(seed,phase_steps=TRAIN_STEPS):
    initial,train,grid=make_seed(seed,phase_steps)
    raw=b"".join(arr.tobytes() for pack in train for arr in pack)
    results=[train_arm(seed,name,initial,train,grid,phase_steps) for name in ARMS]
    return {
        "seed":seed,
        "training_inputs_sha256":hashlib.sha256(raw).hexdigest(),
        "initial_parameters_sha256":hashlib.sha256(initial.tobytes()).hexdigest(),
        "arms":results,
    }

def analyze(runs):
    by={name:[next(a for a in r["arms"] if a["arm"]==name)
              for r in runs] for name in ARMS}
    def joint(a):
        c=a["checkpoints"][2]
        return (c["A_mse"]+c["B_mse"])/2
    summaries={}
    for name,rows in by.items():
        scores=[joint(x) for x in rows]
        forgetting=[x["checkpoints"][2]["A_mse"]-
                    x["checkpoints"][1]["A_mse"] for x in rows]
        summaries[name]={
            "joint_B_by_seed":scores,"joint_B_mean":float(np.mean(scores)),
            "B_mse_after_B_mean":float(np.mean([
                x["checkpoints"][2]["B_mse"] for x in rows])),
            "A_forgetting_mean":float(np.mean(forgetting)),
            "A_mse_after_A2_mean":float(np.mean([
                x["checkpoints"][3]["A_mse"] for x in rows])),
            "B_mse_after_A2_mean":float(np.mean([
                x["checkpoints"][3]["B_mse"] for x in rows])),
            "mean_nonunit_modulator_steps":float(np.mean([
                x["modulator_nonunit_steps"] for x in rows])),
            "mean_gradient_clips":float(np.mean([
                x["gradient_clip_count"] for x in rows])),
        }
    reg=np.asarray(summaries["regulated_sgd"]["joint_B_by_seed"])
    comparisons={}
    for base in ARMS:
        if base=="regulated_sgd": continue
        delta=reg-np.asarray(summaries[base]["joint_B_by_seed"])
        brng=np.random.default_rng(BOOT_SEED)
        draws=brng.integers(0,len(delta),size=(BOOTS,len(delta)))
        boots=np.mean(delta[draws],axis=1)
        comparisons[base]={
            "regulated_minus_baseline_mean":float(np.mean(delta)),
            "regulated_wins":int(np.sum(delta<0)),
            "ties":int(np.sum(delta==0)),
            "regulated_losses":int(np.sum(delta>0)),
            "paired_bootstrap_95":np.quantile(boots,[.025,.975]).tolist(),
        }
    h1=all(comparisons[base]["regulated_minus_baseline_mean"]<0
           and comparisons[base]["regulated_wins"]>=13
           for base in ("sgd_003","adam_001"))
    nonconstant=all(x["modulator_nonunit_steps"]>0 for x in by["regulated_sgd"])
    return {
        "by_arm":summaries,"paired_comparisons":comparisons,
        "H1":"H1_EXPLORATORY_CRITERION_MET_NOT_VALIDATED" if h1
             else "H1_NOT_SUPPORTED_IN_THIS_FIXTURE",
        "regulation_anti_vacuity":"NONCONSTANT" if nonconstant
             else "FAILED_CONSTANT_MODULATOR",
    }

def run(seeds=SEEDS,phase_steps=TRAIN_STEPS):
    seeds=tuple(seeds)
    if (not seeds or len(set(seeds))!=len(seeds) or
        any(type(s) is not int or s<0 for s in seeds)):
        raise ValueError("seeds must be distinct nonnegative ints")
    if type(phase_steps) is not int or not 1<=phase_steps<=64:
        raise ValueError("phase steps out of bounds")
    results=[seed_result(seed,phase_steps) for seed in seeds]
    for r in results:
        for arm in r["arms"]:
            if (arm["update_count"]!=3*phase_steps or
                arm["label_exposures"]!=3*phase_steps*BATCH):
                raise AssertionError("unequal training exposure")
    return {
        "protocol":PROTOCOL,"status":STATUS,
        "seeds":list(seeds),"steps_per_phase":phase_steps,
        "arms":list(ARMS),"numpy_version":np.__version__,
        "registered_constants":{
            "hidden_units":16,"trainable_parameters":49,"batch_size":BATCH,
            "global_gradient_clip":CLIP,"B_outlier_probability":.15,
            "B_outlier_amplitude":.75,"heldout_grid_size":129,
            "bootstrap_seed":BOOT_SEED,"bootstrap_draws":BOOTS,
            "regulated_gain_min":.35,"regulated_gain_max":1.4,
        },
        "runs":results,"summary":analyze(results),"limitations":list(LIMITATIONS),
    }

def save_new(doc,folder):
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/("asp001-"+
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+"-"+
        uuid.uuid4().hex[:10]+".json")
    raw=(json.dumps(doc,indent=2,sort_keys=True,allow_nan=False)+"\n").encode()
    with path.open("xb") as handle:handle.write(raw)
    return path,hashlib.sha256(raw).hexdigest()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--smoke",action="store_true")
    p.add_argument("--output-dir",type=Path,default=Path("evidence/asp001"))
    args=p.parse_args(argv)
    if not args.pilot:p.error("REFUSE: --pilot required")
    doc=run([20330101],8) if args.smoke else run()
    path,sha=save_new(doc,args.output_dir)
    print("EVIDENCE:",path)
    print("SHA256:",sha)
    print("H1:",doc["summary"]["H1"])
    for name,s in doc["summary"]["by_arm"].items():
        print("ARM:",name,"JOINT_MSE_AFTER_B:",format(s["joint_B_mean"],".8f"),
              "A_FORGETTING:",format(s["A_forgetting_mean"],".8f"),
              "B_MSE:",format(s["B_mse_after_B_mean"],".8f"))
    print("STATUS:",STATUS)
    return 0

if __name__=="__main__":sys.exit(main())
