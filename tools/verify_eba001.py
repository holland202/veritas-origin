"""EBA-001 independent semantic reconstruction, not an import of the runner.

Rebuilds 12 tasks x 2 proposer algorithms, P0 evidence summaries, context
dispositions and the known E9 false-clean self-attestation counterexample.
A complete replay establishes internal specification agreement only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import random
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
METHODS=("clean_greedy","oracle_informed")
BASELINE="24eaf51fa816b2e202afbc15ab0c8aa5862b1d90"
RUNNER_SHA="3a614911abe680edc2a98a46cebdfb9156c8e983"
VERIFIER_SHA="2c751d38c89521c9e0d232dfe9ae42190eea43f6"
ARCHIVE_SHA="627eb778e8eef80d9d664c9ac6f3b7743d51e6a97a677eea8cac51e79b467333"
ARCHIVE="evidence/exp003/exp003-p0-20261008T202705724022Z-146bee1a.json"
ALLOWED=("protocol","step","domain","candidate_names",
         "observations","remaining_budget","predicate_definitions")
NAMED=("even","multiple3","multiple5","lowhalf",
       "bit1","bit2","bit3","mod4eq1")
DEFINITIONS={
    "even":"x % 2 == 0","multiple3":"x % 3 == 0",
    "multiple5":"x % 5 == 0","lowhalf":"x < 16",
    "bit1":"(x & 2) != 0","bit2":"(x & 4) != 0",
    "bit3":"(x & 8) != 0","mod4eq1":"x % 4 == 1",
}
CONDITIONS=(
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
LIMITS=[
    "ALL ATTACKS ARE PURE PYTHON SIMULATIONS, NOT UNTRUSTED EXTERNAL PROCESS EXECUTION",
    "No OS container, namespace, UID separation, network egress policy or enforced access monitor",
    "Synthetic self-reported complete-clean logs are forgeable and can conceal oracle reads",
    "EXP003-P0 task seeds and predicate registry are public; no held-out generalization",
    "Original P0 consistency is not methodological validity, source integrity, or permission to deploy",
    "Sovereign Veritas only decides on supplied evidence and cannot authenticate self-reported fields",
    "Not a language-model benchmark, production penetration test, or new scientific-discovery result",
]
SCHEMA={
    "protocol","evidence_status","source_commit_ra001","evaluator_blob_sha1",
    "runner_blob_sha1","original_p0_evidence_sha256","original_p0_evidence_path",
    "seeds","candidate_methods","transcripts","scenarios","outcome_summary","limitations",
}


def check(expr,reason):
    if not expr:
        raise ValueError(reason)


def nodup(pairs):
    d={}
    for key,val in pairs:
        check(key not in d,"duplicate JSON key")
        d[key]=val
    return d


def no_constant(s):
    raise ValueError("nonfinite numeric constant "+s)


def parse(raw):
    check(type(raw) is bytes and len(raw)<2_000_000,"evidence size or type invalid")
    return json.loads(raw,object_pairs_hook=nodup,parse_constant=no_constant)


def stringify(d):
    return json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=False,
                      allow_nan=False).encode()


def match(a,b,path="evidence"):
    check(type(a) is type(b),path+": type mismatch")
    if type(a) is dict:
        check(set(a)==set(b),path+": fields mismatch")
        for k in a:
            match(a[k],b[k],f"{path}.{k}")
    elif type(a) is list:
        check(len(a)==len(b),path+": length mismatch")
        for i,(x,y) in enumerate(zip(a,b)):
            match(x,y,f"{path}[{i}]")
    elif type(a) is float:
        check(math.isfinite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),
              path+": numeric replay mismatch")
    else:
        check(a==b,path+": replay mismatch")


def mathematical_predicate(n,x):
    if n=="even": return int(x%2==0)
    if n=="multiple3": return int(x%3==0)
    if n=="multiple5": return int(x%5==0)
    if n=="lowhalf": return int(x<16)
    if n=="bit1": return int((x&2)!=0)
    if n=="bit2": return int((x&4)!=0)
    if n=="bit3": return int((x&8)!=0)
    if n=="mod4eq1": return int(x%4==1)
    raise ValueError("unknown predicate")


def challenge(seed):
    registry=tuple(sorted(random.Random(f"EXP003-P0:task:{seed}").sample(NAMED,4)))
    hidden=random.Random(f"EXP003-P0:truth:{seed}").choice(registry)
    return registry,hidden


def fair_greedy(remaining,old_probes):
    rankings=[]
    for x in range(32):
        if x in old_probes:
            continue
        histogram=[sum(mathematical_predicate(n,x)==bit for n in remaining)
                   for bit in (0,1)]
        gain=len(remaining)-sum(c*c for c in histogram)/len(remaining)
        rankings.append((gain,-x,x))
    return max(rankings)[2]


def illegitimate_selector(remaining,old_probes,hidden):
    candidates=[]
    for x in range(32):
        if x in old_probes:
            continue
        outcome=mathematical_predicate(hidden,x)
        subset=sum(mathematical_predicate(n,x)==outcome for n in remaining)
        candidates.append((subset,x))
    return min(candidates)[1]


def independent_task(seed,method):
    remaining,hidden=challenge(seed)
    initial=list(remaining)
    log=[]
    used=set()
    for index in range(6):
        if len(remaining)==1:
            break
        if method=="clean_greedy":
            point=fair_greedy(remaining,used)
        else:
            # Synthetic illegal oracle access. No actual OS attack performed.
            point=illegitimate_selector(remaining,used,hidden)
        output=mathematical_predicate(hidden,point)
        new=tuple(n for n in remaining if mathematical_predicate(n,point)==output)
        log.append({
            "step":index,"pre":list(remaining),"probe":point,
            "outcome":output,"post":list(new),
        })
        used.add(point)
        remaining=new
    return {
        "seed":seed,"policy":"external","candidates":initial,
        "truth":hidden,"status":"COMPLETE","failure":None,
        "records":log,"remaining":list(remaining),
        "solved":len(remaining)==1,
    }


def transcript_for(method):
    rows=[independent_task(i,method) for i in range(12)]
    return {
        "protocol":"EXP003-P0","evidence_status":"EXPLORATORY_SIMULATED",
        "seeds":list(range(12)),"max_steps":6,"policies":["external"],
        "summary":{"external":{
            "solved_rate":sum(int(x["solved"]) for x in rows)/12,
            "mean_remaining":sum(len(x["remaining"]) for x in rows)/12,
            "deferred":0,
        }},
        "results":rows,
        "limitations":[
            "PUBLIC SYNTHETIC EXTERNAL POLICY, NOT A MODEL",
            "ORACLE-INFORMED ARM USES FORBIDDEN TRUE HYPOTHESIS",
            "ORIGINAL EXP003-P0 VERIFIER DOES NOT VERIFY INFORMATION PROVENANCE",
            "NO PROCESS OR FILESYSTEM ISOLATION TESTED",
        ],
    }


def classify(declared):
    """Intentionally limited policy for a self-attested telemetry feed."""
    if declared["id"]=="E0":
        return "EXPLORATORY_ONLY"
    if not set(declared["context_keys"]).issubset(ALLOWED):
        return "INVALID_PROPOSER_CONTEXT"
    if declared["evaluator_blob"]!=VERIFIER_SHA:
        return "INVALID_EVALUATOR_IDENTITY"
    if declared["declared_access_event"]=="oracle_read":
        return "INVALID_OBSERVED_ORACLE_LEAK"
    if declared["integrity_claim"]=="SELF_RESEALED":
        return "NOT_ESTABLISHED_SELF_ATTESTED_INTEGRITY"
    if declared["log_completeness"]!="complete":
        return "UNOBSERVABLE_ACCESS_PROVENANCE"
    return "CLEAN_WITHIN_DECLARED_FIXTURE"


def expected_scenario(spec):
    sid,method,additional,event,log,identity,disposition,real_access=spec
    expected={
        "id":sid,"transcript_ref":method,
        "context_keys":list(ALLOWED)+list(additional),
        "declared_access_event":event,
        "log_completeness":log,
        "evaluator_blob":VERIFIER_SHA if identity!="wrong_evaluator" else "0"*40,
        "integrity_claim":"SELF_RESEALED" if identity=="self_resealed" else "EXTERNALLY_PINNED",
        "synthetic_true_oracle_access":real_access,
        "telemetry_enforced_by_os":False,
    }
    observed=classify(expected)
    check(observed==disposition,"frozen scenario's expected disposition wrong")
    expected["methodology_disposition"]=observed
    expected["math_replay_expected"]="CONSISTENT_WITH_EXP003_P0_SPECIFICATION"
    expected["false_clean_attestation"]=(sid=="E9")
    return expected


def run_summary(a,b,scenarios):
    aa=[len(z["records"]) for z in a["results"]]
    bb=[len(z["records"]) for z in b["results"]]
    return {
        "honest_probes":aa,
        "oracle_informed_probes":bb,
        "honest_total":sum(aa),
        "oracle_informed_total":sum(bb),
        "oracle_faster_seeds":sum(y<x for x,y in zip(aa,bb)),
        "oracle_equal_seeds":sum(y==x for x,y in zip(aa,bb)),
        "oracle_slower_seeds":sum(y>x for x,y in zip(aa,bb)),
        "math_replay_expected_count":len(scenarios),
        "explicit_invalid":sum(z["methodology_disposition"].startswith("INVALID")
                               for z in scenarios),
        "unobservable":sum(z["methodology_disposition"]==
                           "UNOBSERVABLE_ACCESS_PROVENANCE" for z in scenarios),
        "known_false_clean":sum(bool(z["false_clean_attestation"]) for z in scenarios),
    }


def load_legacy_verifier():
    path=ROOT/"tools/verify_exp003_p0.py"
    spec=importlib.util.spec_from_file_location("legacy_independent_p0",path)
    check(spec is not None and spec.loader is not None,"legacy verifier missing")
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def verify(raw,pinned_sha,root=ROOT):
    check(type(pinned_sha) is str and len(pinned_sha)==64 and
          all(z in "0123456789abcdef" for z in pinned_sha),
          "invalid pinned SHA256")
    check(hashlib.sha256(raw).hexdigest()==pinned_sha,
          "artifact SHA256 mismatch")
    doc=parse(raw)
    check(type(doc) is dict and set(doc)==SCHEMA,"EBA-001 root fields invalid")
    check(doc["protocol"]=="EBA-001" and
          doc["evidence_status"]=="PUBLIC_SYNTHETIC_RED_TEAM_EXPLORATORY_NOT_VALIDATED",
          "false validated status or wrong protocol")
    checks={
        "source_commit_ra001":BASELINE,
        "evaluator_blob_sha1":VERIFIER_SHA,
        "runner_blob_sha1":RUNNER_SHA,
        "original_p0_evidence_sha256":ARCHIVE_SHA,
        "original_p0_evidence_path":ARCHIVE,
        "seeds":list(range(12)),
        "candidate_methods":list(METHODS),
        "limitations":LIMITS,
    }
    for key,value in checks.items():
        match(value,doc[key],key)
    check(type(doc["transcripts"]) is dict and
          set(doc["transcripts"])==set(METHODS),"transcript roster missing")
    check(type(doc["scenarios"]) is list and
          len(doc["scenarios"])==len(CONDITIONS),"scenario count changed")
    check(type(root) is Path,"root must be a Path")
    archive_path=root/ARCHIVE
    check(archive_path.is_file() and not archive_path.is_symlink(),
          "original historical evidence missing")
    legacy=load_legacy_verifier()
    archive_bytes=archive_path.read_bytes()
    check(hashlib.sha256(archive_bytes).hexdigest()==ARCHIVE_SHA,
          "original historical archive SHA changed")
    # Validate original pilot independently too, not simply via its digest.
    legacy.verify(archive_bytes,ARCHIVE_SHA)

    generated={}
    for method in METHODS:
        candidate=transcript_for(method)
        generated[method]=candidate
        r=doc["transcripts"][method]
        check(type(r) is dict and set(r)=={
            "sha256","probes_by_seed","solves","data",
        },"transcript record fields missing")
        match(candidate,r["data"],f"transcript.{method}")
        computed_sha=hashlib.sha256(stringify(candidate)).hexdigest()
        match(computed_sha,r["sha256"],f"transcript_sha.{method}")
        match([len(k["records"]) for k in candidate["results"]],
              r["probes_by_seed"],f"counts.{method}")
        match(sum(int(k["solved"]) for k in candidate["results"]),
              r["solves"],f"solved.{method}")
        legacy.verify(stringify(candidate),computed_sha)
    reconstructed=[expected_scenario(x) for x in CONDITIONS]
    match(reconstructed,doc["scenarios"],"scenarios")
    counts=run_summary(generated["clean_greedy"],
                       generated["oracle_informed"],reconstructed)
    match(counts,doc["outcome_summary"],"summary")
    check(counts["known_false_clean"]==1,"known blind spot lost")
    return {
        "verdict":"INTERNAL_SPECIFICATION_CONSISTENCY_ONLY",
        "historical_p0":"CONSISTENT_WITH_SPECIFICATION",
        "external_policy_transcripts":2,
        "mathematically_valid_external_tasks":24,
        "scenarios":len(CONDITIONS),
        "oracle_faster_seeds":counts["oracle_faster_seeds"],
        "forged_clean_log_false_positives":counts["known_false_clean"],
        "missing_provenance":"UNOBSERVABLE_NOT_CLEAN",
        "os_boundary":"NOT_TESTED",
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    args=p.parse_args(argv)
    try:
        result=verify(args.evidence.read_bytes(),args.sha256)
    except (ValueError,TypeError,KeyError,IndexError,OSError,OverflowError,
            AssertionError) as err:
        print("VERDICT: INCONSISTENT_OR_UNVERIFIABLE",err,file=sys.stderr)
        return 1
    print("VERDICT: CONSISTENT WITH EBA-001 REGISTERED TOY SPECIFICATION")
    print("DETAILS:",json.dumps(result,sort_keys=True))
    print("LIMIT: logs and model access are not independently enforced; E9 can falsely pass")
    return 0


if __name__=="__main__":
    sys.exit(main())
