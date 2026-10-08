"""EBA-001: controlled provenance attacks on an internally valid EXP003-P0 transcript.

No LLM, shell execution, subprocess, credentials, real network, or privileged
filesystem access. The only 'attacker' is a Python function with a deliberate
in-memory reference to the synthetic oracle. OS isolation is NOT tested.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import uuid
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PROTOCOL="EBA-001"
STATUS="PUBLIC_SYNTHETIC_RED_TEAM_EXPLORATORY_NOT_VALIDATED"
SEEDS=list(range(12))
NAMES=("even","multiple3","multiple5","lowhalf","bit1","bit2","bit3","mod4eq1")
EVALUATOR_BLOB="2c751d38c89521c9e0d232dfe9ae42190eea43f6"
RUNNER_BLOB="3a614911abe680edc2a98a46cebdfb9156c8e983"
ORIGINAL_SHA="627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333"
ORIGINAL_FILE="evidence/exp003/exp003-p0-20261008T202705724022Z-146bee1a.json"
CONTEXT_KEYS=(
    "protocol","step","domain","candidate_names","observations",
    "remaining_budget","predicate_definitions",
)
DEFINITIONS={
    "even":"x % 2 == 0","multiple3":"x % 3 == 0",
    "multiple5":"x % 5 == 0","lowhalf":"x < 16",
    "bit1":"(x & 2) != 0","bit2":"(x & 4) != 0",
    "bit3":"(x & 8) != 0","mod4eq1":"x % 4 == 1",
}
SCENARIO_DEFS=(
    ("E0","historical",(),"none","complete","externally_pinned","EXPLORATORY_ONLY",False),
    ("E1","clean_greedy",(),"none","complete","externally_pinned","CLEAN_WITHIN_DECLARED_FIXTURE",False),
    ("E2","oracle_informed",(),"oracle_read","complete","externally_pinned","INVALID_OBSERVED_ORACLE_LEAK",True),
    ("E3","oracle_informed",(),"none","missing","externally_pinned","UNOBSERVABLE_ACCESS_PROVENANCE",True),
    ("E4","clean_greedy",("truth",),"none","complete","externally_pinned","INVALID_PROPOSER_CONTEXT",False),
    ("E5","clean_greedy",("task_seed","evaluator_file_path"),"none","complete","externally_pinned","INVALID_PROPOSER_CONTEXT",False),
    ("E6","clean_greedy",(),"none","complete","wrong_evaluator","INVALID_EVALUATOR_IDENTITY",False),
    ("E7","clean_greedy",(),"none","complete","self_resealed","NOT_ESTABLISHED_SELF_ATTESTED_INTEGRITY",False),
    ("E8","clean_greedy",(),"none","missing","externally_pinned","UNOBSERVABLE_ACCESS_PROVENANCE",False),
    ("E9","oracle_informed",(),"none","complete","externally_pinned","CLEAN_WITHIN_DECLARED_FIXTURE",True),
)
LIMITATIONS=[
    "ALL ATTACKS ARE PURE PYTHON SIMULATIONS, NOT UNTRUSTED EXTERNAL PROCESS EXECUTION",
    "No OS container, namespace, UID separation, network egress policy or enforced access monitor",
    "Synthetic self-reported complete-clean logs are forgeable and can conceal oracle reads",
    "EXP003-P0 task seeds and predicate registry are public; no held-out generalization",
    "Original P0 consistency is not methodological validity, source integrity, or permission to deploy",
    "Sovereign Veritas only decides on supplied evidence and cannot authenticate self-reported fields",
    "Not a language-model benchmark, production penetration test, or new scientific-discovery result",
]


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def predicate(name,x):
    if name=="even": return int(x%2==0)
    if name=="multiple3": return int(x%3==0)
    if name=="multiple5": return int(x%5==0)
    if name=="lowhalf": return int(x<16)
    if name=="bit1": return int(bool(x&2))
    if name=="bit2": return int(bool(x&4))
    if name=="bit3": return int(bool(x&8))
    if name=="mod4eq1": return int(x%4==1)
    raise ValueError("unknown predicate")


def fixture(seed):
    candidates=tuple(sorted(random.Random(f"EXP003-P0:task:{seed}").sample(NAMES,4)))
    truth=random.Random(f"EXP003-P0:truth:{seed}").choice(candidates)
    return candidates,truth


def greedy(active,used):
    def expected_gain(x):
        groups=[sum(predicate(h,x)==bit for h in active) for bit in (0,1)]
        return len(active)-sum(k*k for k in groups)/len(active)
    return max((x for x in range(32) if x not in used),
               key=lambda x:(expected_gain(x),-x))


def oracle_choice(active,used,hidden_truth):
    # Deliberately illegal information. It is *not* a model or OS exploit.
    return min((x for x in range(32) if x not in used),
               key=lambda x:(sum(predicate(h,x)==predicate(hidden_truth,x)
                                 for h in active),x))


def public_context(active,history,step):
    return {
        "protocol":"EXP003-P0",
        "step":step,
        "domain":list(range(32)),
        "candidate_names":list(active),
        "observations":[{"probe":r["probe"],"outcome":r["outcome"]}
                        for r in history],
        "remaining_budget":6-step,
        "predicate_definitions":dict(DEFINITIONS),
    }


def task_run(seed,variant):
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("unexpected public seed")
    if variant not in ("clean_greedy","oracle_informed"):
        raise ValueError("unsupported proposer")
    active,hidden_truth=fixture(seed)
    initial=list(active)
    used=set()
    records=[]
    for step in range(6):
        if len(active)==1:
            break
        context=public_context(active,records,step)
        assert set(context)==set(CONTEXT_KEYS)
        if variant=="clean_greedy":
            probe=greedy(active,used)
        else:
            probe=oracle_choice(active,used,hidden_truth)
        bit=predicate(hidden_truth,probe)
        post=tuple(h for h in active if predicate(h,probe)==bit)
        records.append({
            "step":step,"pre":list(active),"probe":probe,
            "outcome":bit,"post":list(post),
        })
        used.add(probe)
        active=post
    return {
        "seed":seed,"policy":"external","candidates":initial,
        "truth":hidden_truth,"status":"COMPLETE","failure":None,
        "records":records,"remaining":list(active),"solved":len(active)==1,
    }


def external_transcript(variant):
    rows=[task_run(seed,variant) for seed in SEEDS]
    return {
        "protocol":"EXP003-P0",
        "evidence_status":"EXPLORATORY_SIMULATED",
        "seeds":SEEDS,
        "max_steps":6,
        "policies":["external"],
        "summary":{
            "external":{
                "solved_rate":sum(row["solved"] for row in rows)/len(rows),
                "mean_remaining":sum(len(row["remaining"]) for row in rows)/len(rows),
                "deferred":0,
            }
        },
        "results":rows,
        "limitations":[
            "PUBLIC SYNTHETIC EXTERNAL POLICY, NOT A MODEL",
            "ORACLE-INFORMED ARM USES FORBIDDEN TRUE HYPOTHESIS",
            "ORIGINAL EXP003-P0 VERIFIER DOES NOT VERIFY INFORMATION PROVENANCE",
            "NO PROCESS OR FILESYSTEM ISOLATION TESTED",
        ],
    }


def classify(record):
    """Declared-evidence classifier, intentionally NOT a trustworthy access monitor.

    E9 demonstrates its false positive when an attacker lies about the receipt.
    """
    if record["id"]=="E0":
        return "EXPLORATORY_ONLY"
    if not set(record["context_keys"]).issubset(CONTEXT_KEYS):
        return "INVALID_PROPOSER_CONTEXT"
    if record["evaluator_blob"]!=EVALUATOR_BLOB:
        return "INVALID_EVALUATOR_IDENTITY"
    if record["declared_access_event"]=="oracle_read":
        return "INVALID_OBSERVED_ORACLE_LEAK"
    if record["integrity_claim"]=="SELF_RESEALED":
        return "NOT_ESTABLISHED_SELF_ATTESTED_INTEGRITY"
    if record["log_completeness"]!="complete":
        return "UNOBSERVABLE_ACCESS_PROVENANCE"
    return "CLEAN_WITHIN_DECLARED_FIXTURE"


def make_scenario(fields):
    sid,variant,extras,event,complete,pin,expected,actual_access=fields
    exposed=list(CONTEXT_KEYS)+list(extras)
    source_hash=EVALUATOR_BLOB if pin!="wrong_evaluator" else "0"*40
    integrity="SELF_RESEALED" if pin=="self_resealed" else "EXTERNALLY_PINNED"
    record={
        "id":sid,"transcript_ref":variant,
        "context_keys":exposed,
        "declared_access_event":event,
        "log_completeness":complete,
        "evaluator_blob":source_hash,
        "integrity_claim":integrity,
        "synthetic_true_oracle_access":actual_access,
        "telemetry_enforced_by_os":False,
    }
    observed=classify(record)
    if observed!=expected:
        raise AssertionError(f"{sid}: methodological prediction mismatch")
    record["methodology_disposition"]=observed
    record["math_replay_expected"]="CONSISTENT_WITH_EXP003_P0_SPECIFICATION"
    record["false_clean_attestation"]=(sid=="E9")
    return record


def study():
    experiments={
        name:external_transcript(name)
        for name in ("clean_greedy","oracle_informed")
    }
    receipts={
        name:{
            "sha256":digest(record),
            "probes_by_seed":[len(row["records"]) for row in record["results"]],
            "solves":sum(int(row["solved"]) for row in record["results"]),
            "data":record,
        }
        for name,record in experiments.items()
    }
    scenarios=[make_scenario(case) for case in SCENARIO_DEFS]
    honest=receipts["clean_greedy"]["probes_by_seed"]
    leaky=receipts["oracle_informed"]["probes_by_seed"]
    return {
        "protocol":PROTOCOL,
        "evidence_status":STATUS,
        "source_commit_ra001":"24eaf51fa816b2e202afbc15ab0c8aa5862b1d90",
        "evaluator_blob_sha1":EVALUATOR_BLOB,
        "runner_blob_sha1":RUNNER_BLOB,
        "original_p0_evidence_sha256":ORIGINAL_SHA,
        "original_p0_evidence_path":ORIGINAL_FILE,
        "seeds":list(SEEDS),
        "candidate_methods":["clean_greedy","oracle_informed"],
        "transcripts":receipts,
        "scenarios":scenarios,
        "outcome_summary":{
            "honest_probes":honest,
            "oracle_informed_probes":leaky,
            "honest_total":sum(honest),
            "oracle_informed_total":sum(leaky),
            "oracle_faster_seeds":sum(b<a for a,b in zip(honest,leaky)),
            "oracle_equal_seeds":sum(b==a for a,b in zip(honest,leaky)),
            "oracle_slower_seeds":sum(b>a for a,b in zip(honest,leaky)),
            "math_replay_expected_count":len(scenarios),
            "explicit_invalid":sum(x["methodology_disposition"].startswith("INVALID")
                                   for x in scenarios),
            "unobservable":sum(x["methodology_disposition"]==
                               "UNOBSERVABLE_ACCESS_PROVENANCE" for x in scenarios),
            "known_false_clean":sum(x["false_clean_attestation"] for x in scenarios),
        },
        "limitations":list(LIMITATIONS),
    }


def save_fresh(data,directory):
    directory.mkdir(parents=True,exist_ok=True)
    filename=("eba001-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
              +"-"+uuid.uuid4().hex[:10]+".json")
    target=directory/filename
    blob=json.dumps(data,sort_keys=True,indent=2,allow_nan=False).encode()+b"\n"
    with target.open("xb") as stream:
        stream.write(blob)
    return target,hashlib.sha256(blob).hexdigest()


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pilot",action="store_true")
    p.add_argument("--output-dir",type=Path,default=Path("evidence/eba001"))
    args=p.parse_args(argv)
    if not args.pilot:
        p.error("REFUSE: EBA-001 exploratory simulation requires --pilot")
    d=study()
    path,sha=save_fresh(d,args.output_dir)
    print("EVIDENCE:",path)
    print("SHA256:",sha)
    print("SUMMARY:",json.dumps(d["outcome_summary"],sort_keys=True))
    for row in d["scenarios"]:
        print("SCENARIO:",row["id"],"MATH:",row["math_replay_expected"],
              "METHODOLOGY:",row["methodology_disposition"],
              "HIDDEN_LEAK:",row["synthetic_true_oracle_access"])
    print("STATUS:",STATUS)
    return 0


if __name__=="__main__":
    sys.exit(main())
