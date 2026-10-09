"""EPV-001: deterministic synthetic multiagent evidence-fusion laboratory.

No LLMs, no actual scouts, no network, no cryptographic identity enrollment.
The protected fixture's "trusted anchors" are ASSUMED, not established.
See preregistered experiments/epv001/PROTOCOL.md before using results.
"""
from __future__ import annotations
import argparse,hashlib,json,random,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

SEEDS=tuple(range(260801,260809))
CASES=(
    "INDEPENDENT_LIAR","CORRELATED_FALSE_MAJORI",
    "CORRELATED_UNPROVEN_DISSENT","FORGED_DISSENT_PROOF",
    "POISONED_AUTHORITY","CONFLICTING_AUTHORITIES",
)
POLICIES=("majority","lineage","claimed_certificate","evidence_first")
N=64
STATUS="PUBLIC_SYNTHETIC_EVIDENCE_VIGILANCE_NOT_VALIDATED"
ABSTAIN="ABSTAIN"
LIMITS=(
    "Pure synthetic four-source binary environment; not an LLM or real agent benchmark",
    "A trusted anchor registry is assumed by fixture and can itself be wrong",
    "Hashes and matched parity certify fixture consistency, not external world truth",
    "Reports sharing lineage are synthetically correlated, not independently measured",
    "Source-id and lineage metadata are supplied by fixture, not authenticated identities",
    "No evidence of model consciousness, genuine human skepticism or AI biology",
    "No human authorization, secure OS enforcement, real-world decision or deployment",
)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode()

def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def witness(rng,claim):
    bits=[rng.randrange(2) for _ in range(7)]
    bits.append((sum(bits)%2)^claim)
    assert sum(bits)%2==claim
    return bits

def report(sid,lineage,claim,verified=False,witness_bits=None):
    return {"id":sid,"lineage":lineage,"claim":claim,
            "claimed_verified":verified,"witness":witness_bits}

def fixture(rng,seed,case,index):
    truth=rng.randrange(2)
    trial_id=f"{seed}:{case}:{index}"
    true_bits=witness(rng,truth)
    false_bits=witness(rng,1-truth)
    true_anchor=sha({"trial_id":trial_id,"bits":true_bits,"claim":truth})
    false_anchor=sha({"trial_id":trial_id,"bits":false_bits,"claim":1-truth})
    t=truth;f=1-truth
    if case=="INDEPENDENT_LIAR":
        rows=[report("s0","l0",t),report("s1","l1",t),
              report("s2","l2",t),report("s3","l3",f)]
        anchors={}
    elif case in ("CORRELATED_FALSE_MAJORI","CORRELATED_UNPROVEN_DISSENT"):
        certified=case=="CORRELATED_FALSE_MAJORI"
        rows=[report("s0","common",f),report("s1","common",f),
              report("s2","common",f),
              report("s3","independent",t,certified,
                     true_bits if certified else None)]
        anchors={"s3":true_anchor} if certified else {}
    elif case=="FORGED_DISSENT_PROOF":
        rows=[report("s0","l0",t),report("s1","l1",t),
              report("s2","l2",t),report("s3","l3",f,True,false_bits)]
        # The liar forges a proof; its self-asserted label cannot change anchor.
        anchors={"s3":true_anchor}
    elif case=="POISONED_AUTHORITY":
        rows=[report("s0","l0",t),report("s1","l1",t),
              report("s2","l2",t),report("s3","l3",f,True,false_bits)]
        # INTENTIONAL FALSE CLEAN: the fixture authority is itself poisoned.
        anchors={"s3":false_anchor}
    elif case=="CONFLICTING_AUTHORITIES":
        rows=[report("s0","l0",t,True,true_bits),report("s1","l1",t),
              report("s2","l2",t),report("s3","l3",f,True,false_bits)]
        anchors={"s0":true_anchor,"s3":false_anchor}
    else:raise ValueError("unexpected fixture case")
    rng.shuffle(rows)
    return {"trial_id":trial_id,"seed":seed,"case":case,"index":index,
            "world_truth":truth,"trusted_anchors":anchors,"reports":rows,
            "reference_trust":"FIXTURE_ASSUMPTION_NOT_AUTHENTICATED",
            "deliberately_poisoned":case in
                ("POISONED_AUTHORITY","CONFLICTING_AUTHORITIES")}

def majority(reports):
    count=sum(x["claim"] for x in reports)
    if count*2==len(reports):return ABSTAIN
    return int(count*2>len(reports))

def lineage_vote(reports):
    pools={}
    for row in reports:
        pools.setdefault(row["lineage"],set()).add(row["claim"])
    independent=[next(iter(values)) for values in pools.values() if len(values)==1]
    if not independent:return ABSTAIN
    ones=sum(independent)
    if ones*2==len(independent):return ABSTAIN
    return int(ones*2>len(independent))

def verified_claims(rows,anchors,trial_id):
    valid=[]
    for row in rows:
        bits=row["witness"]
        if bits is None or row["id"] not in anchors:continue
        if (type(bits) is not list or len(bits)!=8
            or any(type(bit) is not int or bit not in (0,1) for bit in bits)):
            continue
        if sum(bits)%2!=row["claim"]:continue
        actual=sha({"trial_id":trial_id,"bits":bits,"claim":row["claim"]})
        if actual==anchors[row["id"]]:
            valid.append(row["claim"])
    return valid

def decide(trial,policy):
    reports=trial["reports"]
    if policy=="majority":return majority(reports)
    if policy=="lineage":return lineage_vote(reports)
    if policy=="claimed_certificate":
        for row in reports:
            if row["claimed_verified"]:return row["claim"]
        return majority(reports)
    if policy=="evidence_first":
        certs=verified_claims(reports,trial["trusted_anchors"],trial["trial_id"])
        if len(set(certs))>1:return ABSTAIN
        if certs:return certs[0]
        return lineage_vote(reports)
    raise ValueError("unknown policy")

def results(all_trials):
    summary={}
    for case in CASES:
        rows=[row for row in all_trials if row["case"]==case]
        if len(rows)!=N*len(SEEDS):raise ValueError("missing registered cases")
        cases={}
        for name in POLICIES:
            attempted=[row["decisions"][name] for row in rows]
            right=sum(out!=ABSTAIN and out==row["world_truth"]
                      for row,out in zip(rows,attempted))
            wrong=sum(out!=ABSTAIN and out!=row["world_truth"]
                      for row,out in zip(rows,attempted))
            stopped=sum(out==ABSTAIN for out in attempted)
            cases[name]={
                "trials":len(rows),"correct":right,"incorrect":wrong,
                "abstained":stopped,
                "coverage":(right+wrong)/len(rows),
                "error_per_all":wrong/len(rows),
                "error_per_accepted":wrong/(right+wrong) if right+wrong else None,
            }
        summary[case]=cases
    return summary

def run():
    trials=[]
    for seed in SEEDS:
        rng=random.Random(seed)
        for case in CASES:
            for index in range(N):
                entry=fixture(rng,seed,case,index)
                entry["decisions"]={name:decide(entry,name) for name in POLICIES}
                trials.append(entry)
    grouped=results(trials)
    # Registered nonvacuity and deliberate known-failure controls.
    checks={
        "independent_majority_correct":grouped["INDEPENDENT_LIAR"]["majority"]["correct"]==N*len(SEEDS),
        "correlated_majority_wrong":grouped["CORRELATED_FALSE_MAJORI"]["majority"]["incorrect"]==N*len(SEEDS),
        "certified_minor_dissent_recognized":grouped["CORRELATED_FALSE_MAJORI"]["evidence_first"]["correct"]==N*len(SEEDS),
        "uncertified_dissent_abstained":grouped["CORRELATED_UNPROVEN_DISSENT"]["evidence_first"]["abstained"]==N*len(SEEDS),
        "fake_claimed_cert_rejected":grouped["FORGED_DISSENT_PROOF"]["evidence_first"]["correct"]==N*len(SEEDS),
        "fake_claimed_cert_fools_naive":grouped["FORGED_DISSENT_PROOF"]["claimed_certificate"]["incorrect"]==N*len(SEEDS),
        "poisoned_authority_false_positive_preserved":grouped["POISONED_AUTHORITY"]["evidence_first"]["incorrect"]==N*len(SEEDS),
        "conflicting_authentic_witnesses_abstained":grouped["CONFLICTING_AUTHORITIES"]["evidence_first"]["abstained"]==N*len(SEEDS),
    }
    if not all(checks.values()):
        raise AssertionError("preregistered benchmark control failed")
    return {"protocol":"EPV-001","status":STATUS,
            "seeds":list(SEEDS),"cases":list(CASES),
            "policies":list(POLICIES),"trials_per_case_seed":N,
            "world_truth_visibility_to_policy":"NOT_PASSED",
            "trusted_anchor_authority":"FIXTURE_ASSUMPTION_NOT_WORLD_TRUTH",
            "trial_records":trials,"summary":grouped,
            "registered_controls":checks,"limitations":list(LIMITS)}

def write_once(value,folder):
    folder.mkdir(parents=True,exist_ok=True)
    dest=folder/("epv001-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
                 +"-"+uuid.uuid4().hex[:8]+".json")
    blob=json.dumps(value,sort_keys=True,indent=2,allow_nan=False).encode()+b"\n"
    with dest.open("xb") as file:file.write(blob)
    return dest,hashlib.sha256(blob).hexdigest()

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot",action="store_true")
    parser.add_argument("--output-dir",type=Path,default=Path("evidence/epv001"))
    args=parser.parse_args(argv)
    if not args.pilot:parser.error("REFUSE: exploratory run requires --pilot")
    doc=run()
    path,hashcode=write_once(doc,args.output_dir)
    print("EVIDENCE:",path)
    print("SHA256:",hashcode)
    print("TRIALS:",len(doc["trial_records"]))
    for case in CASES:
        a=doc["summary"][case]
        print("CASE:",case,
              "MAJORITY_WRONG:",a["majority"]["incorrect"],
              "EVIDENCE_WRONG:",a["evidence_first"]["incorrect"],
              "EVIDENCE_ABSTAINED:",a["evidence_first"]["abstained"])
    print("STATUS:",STATUS)
    return 0

if __name__=="__main__":sys.exit(main())
