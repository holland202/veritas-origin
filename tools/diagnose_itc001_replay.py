"""ITC-001 forensic drift report: NEVER promotes a failed replay to PASS.

Measures differences between archived original numerical weights, a fresh
independently reconstructed BPTT run and a fresh producer run under current
NumPy, CPU and BLAS environment. Pure diagnostic; no changed original bytes.
"""
from __future__ import annotations
import argparse,hashlib,json,os,platform,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"/"origin"))
sys.path.insert(0,str(ROOT/"tools"))
import itc001 as producer
import verify_itc001 as independent

NAMES=("Win","Wr","bias","Wout","bout")
EXPECTED_SHA="701703011d39482020bbfd9c40c203fc23fcd64859887cb9edcf15ea93d7ff68"

def audit(raw):
    if hashlib.sha256(raw).hexdigest()!=EXPECTED_SHA:
        raise ValueError("original evidence bytes do not match anchored digest")
    doc=json.loads(raw)
    if doc.get("status")!="PUBLIC_EXPLORATORY_INTERNAL_COMPUTATION_NOT_VALIDATED":
        raise ValueError("missing exploratory classification")
    report={
        "status":"DIAGNOSTIC_ONLY_NO_APPROVAL",
        "original_sha256":EXPECTED_SHA,
        "recorded_numpy_version":doc["numpy_version"],
        "current_numpy_version":np.__version__,
        "python":platform.python_version(),
        "machine":platform.machine(),
        "processor":platform.processor(),
        "platform":platform.platform(),
        "openblas_coretype":os.environ.get("OPENBLAS_CORETYPE","NOT_PINNED"),
        "openblas_threads":os.environ.get("OPENBLAS_NUM_THREADS","UNSPECIFIED"),
        "seeds":[],
    }
    for row in doc["seed_records"]:
        seed=row["seed"]
        replay_theta,init,stream,logs=independent.fit(seed)
        theta,prod_init,prod_stream,prod_logs=producer.train(seed)
        info={
            "seed":seed,
            "init_sha_matched":init==row["initial_parameters_sha256"],
            "training_stream_sha_matched":stream==row["training_stream_sha256"],
            "producer_init_matched":prod_init==row["initial_parameters_sha256"],
            "producer_stream_matched":prod_stream==row["training_stream_sha256"],
            "layers":{},
        }
        for key,index in zip(NAMES,range(5)):
            ref=np.array(row["final_weights"][key],dtype=np.float64)
            a=replay_theta[index]
            b=theta[key]
            info["layers"][key]={
                "independent_equal_bits":bool(np.array_equal(a,ref)),
                "independent_isclose_1e8":bool(np.allclose(a,ref,rtol=1e-8,atol=1e-8)),
                "independent_max_abs":float(np.max(np.abs(a-ref))),
                "independent_root_mean_square":float(np.sqrt(np.mean((a-ref)**2))),
                "producer_equal_bits":bool(np.array_equal(b,ref)),
                "producer_max_abs":float(np.max(np.abs(b-ref))),
                "producer_vs_independent_max_abs":float(np.max(np.abs(b-a))),
            }
        info["training_reproduced_to_prior_tolerance"]=all(
            v["independent_isclose_1e8"] for v in info["layers"].values())
        report["seeds"].append(info)
    report["all_seeds_reproduced_to_prior_tolerance"]=all(
        v["training_reproduced_to_prior_tolerance"] for v in report["seeds"])
    return report

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original",type=Path)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args(argv)
    original=a.original.read_bytes()
    report=audit(original)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    destination=a.output_dir/"itc001_fresh_training_drift_diagnostic.json"
    with destination.open("x",encoding="utf-8") as file:
        json.dump(report,file,indent=2,sort_keys=True);file.write("\n")
    print("DIAGNOSTIC:",destination)
    print("SHA256:",hashlib.sha256(destination.read_bytes()).hexdigest())
    print("EXACT_STATUS: ORIGINAL_BYTE_SHA256_MATCHED; FRESH_TRAINING=",report["all_seeds_reproduced_to_prior_tolerance"])
    for item in report["seeds"]:
        print("SEED",item["seed"],"OK",item["training_reproduced_to_prior_tolerance"],
              "TRAIN_STREAM_OK",item["training_stream_sha_matched"],
              "WIN_MAX_ABS",item["layers"]["Win"]["independent_max_abs"],
              "WOUT_MAX_ABS",item["layers"]["Wout"]["independent_max_abs"],
              "BOUT_MAX_ABS",item["layers"]["bout"]["independent_max_abs"])
    return 0

if __name__=="__main__":sys.exit(main())
