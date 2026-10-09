"""EPV-001 standalone independent synthetic-evidence semantic replayer.

Does not import the producer or Sovereign Veritas Gate. A consistency verdict
does not authenticate a real-world trust registry, information source, or claim.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,sys
from pathlib import Path

SEEDS=tuple(range(260801,260809))
SCENARIOS=(
    "INDEPENDENT_LIAR","CORRELATED_FALSE_MAJORI",
    "CORRELATED_UNPROVEN_DISSENT","FORGED_DISSENT_PROOF",
    "POISONED_AUTHORITY","CONFLICTING_AUTHORITIES",
)
MODES=("majority","lineage","claimed_certificate","evidence_first")
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

def require(cond,problem):
    if not cond:raise ValueError(problem)

def no_duplicates(pairs):
    result={}
    for name,value in pairs:
        require(name not in result,"duplicate JSON keys")
        result[name]=value
    return result

def invalid_json_constant(value):
    raise ValueError("nonfinite JSON numeric constant")

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode()

def h(v):return hashlib.sha256(canonical(v)).hexdigest()

def reconstruct_witness(rng,value):
    generated=[rng.randrange(2) for _ in range(7)]
    generated.append(value^(sum(generated)%2))
    return generated

def make_report(index,group,bit,claimed=False,proof=None):
    return {"id":"s"+str(index),"lineage":group,"claim":bit,
            "claimed_verified":claimed,"witness":proof}

def reconstruct_trial(rng,seed,scenario,index):
    true_bit=rng.randrange(2)
    false_bit=1-true_bit
    trial_id=f"{seed}:{scenario}:{index}"
    true_w=reconstruct_witness(rng,true_bit)
    false_w=reconstruct_witness(rng,false_bit)
    true_hash=h({"bits":true_w,"claim":true_bit,"trial_id":trial_id})
    false_hash=h({"bits":false_w,"claim":false_bit,"trial_id":trial_id})
    if scenario=="INDEPENDENT_LIAR":
        reports=[make_report(j,"l"+str(j),true_bit if j!=3 else false_bit)
                 for j in range(4)]
        anchors={}
    elif scenario=="CORRELATED_FALSE_MAJORI":
        reports=[make_report(j,"common",false_bit) for j in range(3)]
        reports.append(make_report(3,"independent",true_bit,True,true_w))
        anchors={"s3":true_hash}
    elif scenario=="CORRELATED_UNPROVEN_DISSENT":
        reports=[make_report(j,"common",false_bit) for j in range(3)]
        reports.append(make_report(3,"independent",true_bit))
        anchors={}
    elif scenario=="FORGED_DISSENT_PROOF":
        reports=[make_report(j,"l"+str(j),true_bit) for j in range(3)]
        reports.append(make_report(3,"l3",false_bit,True,false_w))
        anchors={"s3":true_hash}
    elif scenario=="POISONED_AUTHORITY":
        reports=[make_report(j,"l"+str(j),true_bit) for j in range(3)]
        reports.append(make_report(3,"l3",false_bit,True,false_w))
        anchors={"s3":false_hash}
    elif scenario=="CONFLICTING_AUTHORITIES":
        reports=[make_report(0,"l0",true_bit,True,true_w),
                 make_report(1,"l1",true_bit),
                 make_report(2,"l2",true_bit),
                 make_report(3,"l3",false_bit,True,false_w)]
        anchors={"s0":true_hash,"s3":false_hash}
    else:raise ValueError("unregistered scenario")
    rng.shuffle(reports)
    return {
        "trial_id":trial_id,"seed":seed,"case":scenario,"index":index,
        "world_truth":true_bit,"trusted_anchors":anchors,"reports":reports,
        "reference_trust":"FIXTURE_ASSUMPTION_NOT_AUTHENTICATED",
        "deliberately_poisoned":scenario in
            ("POISONED_AUTHORITY","CONFLICTING_AUTHORITIES"),
    }

def independent_decision(trial,mode):
    messages=trial["reports"]
    def raw_majority():
        yes=sum(msg["claim"] for msg in messages)
        if yes==2:return ABSTAIN
        return int(yes>2)
    def independent_lines():
        groups={}
        for msg in messages:
            groups.setdefault(msg["lineage"],set()).add(msg["claim"])
        votes=[next(iter(group)) for group in groups.values() if len(group)==1]
        if not votes or 2*sum(votes)==len(votes):return ABSTAIN
        return int(2*sum(votes)>len(votes))
    if mode=="majority":return raw_majority()
    if mode=="lineage":return independent_lines()
    if mode=="claimed_certificate":
        attestations=[msg for msg in messages if msg["claimed_verified"]]
        return attestations[0]["claim"] if attestations else raw_majority()
    if mode!="evidence_first":raise ValueError("unregistered policy")
    verified=[]
    for msg in messages:
        proof=msg["witness"]
        if proof is None or msg["id"] not in trial["trusted_anchors"]:continue
        if type(proof) is not list or len(proof)!=8:continue
        if any(type(bit) is not int or bit not in (0,1) for bit in proof):continue
        if sum(proof)%2!=msg["claim"]:continue
        statement={"bits":proof,"claim":msg["claim"],"trial_id":trial["trial_id"]}
        if h(statement)==trial["trusted_anchors"][msg["id"]]:
            verified.append(msg["claim"])
    if len(set(verified))>1:return ABSTAIN
    if verified:return verified[0]
    return independent_lines()

def score(all_rows):
    output={}
    for scenario in SCENARIOS:
        group=[trial for trial in all_rows if trial["case"]==scenario]
        require(len(group)==64*len(SEEDS),"missing scenario inventory")
        modes={}
        for mode in MODES:
            values=[item["decisions"][mode] for item in group]
            right=sum(pred==item["world_truth"] and pred!=ABSTAIN
                      for pred,item in zip(values,group))
            wrong=sum(pred!=item["world_truth"] and pred!=ABSTAIN
                      for pred,item in zip(values,group))
            abstain=sum(pred==ABSTAIN for pred in values)
            n=len(group)
            modes[mode]={
                "trials":n,"correct":right,"incorrect":wrong,
                "abstained":abstain,"coverage":(right+wrong)/n,
                "error_per_all":wrong/n,
                "error_per_accepted":wrong/(right+wrong)
                     if right+wrong else None,
            }
        output[scenario]=modes
    return output

def control_summary(groups):
    n=64*len(SEEDS)
    return {
        "independent_majority_correct":groups["INDEPENDENT_LIAR"]["majority"]["correct"]==n,
        "correlated_majority_wrong":groups["CORRELATED_FALSE_MAJORI"]["majority"]["incorrect"]==n,
        "certified_minor_dissent_recognized":groups["CORRELATED_FALSE_MAJORI"]["evidence_first"]["correct"]==n,
        "uncertified_dissent_abstained":groups["CORRELATED_UNPROVEN_DISSENT"]["evidence_first"]["abstained"]==n,
        "fake_claimed_cert_rejected":groups["FORGED_DISSENT_PROOF"]["evidence_first"]["correct"]==n,
        "fake_claimed_cert_fools_naive":groups["FORGED_DISSENT_PROOF"]["claimed_certificate"]["incorrect"]==n,
        "poisoned_authority_false_positive_preserved":groups["POISONED_AUTHORITY"]["evidence_first"]["incorrect"]==n,
        "conflicting_authentic_witnesses_abstained":groups["CONFLICTING_AUTHORITIES"]["evidence_first"]["abstained"]==n,
    }

def equal(a,b,path="record"):
    require(type(a) is type(b),path+": type mismatch")
    if type(a) is dict:
        require(set(a)==set(b),path+": keys differ")
        for k in a:equal(a[k],b[k],path+"."+k)
    elif type(a) is list:
        require(len(a)==len(b),path+": length differs")
        for j,(x,y) in enumerate(zip(a,b)):equal(x,y,f"{path}[{j}]")
    elif type(a) is float:
        require(math.isclose(a,b,rel_tol=1e-13,abs_tol=1e-13),
                path+": numeric mismatch")
    else:
        require(a==b,path+": mismatch")

def verify(raw,pinned):
    require(type(raw) is bytes and len(raw)<7_000_000,"unsupported evidence size")
    require(type(pinned) is str and len(pinned)==64 and
            all(c in "0123456789abcdef" for c in pinned),
            "invalid SHA256")
    require(hashlib.sha256(raw).hexdigest()==pinned,"SHA256 mismatch")
    doc=json.loads(raw,object_pairs_hook=no_duplicates,parse_constant=invalid_json_constant)
    require(type(doc) is dict and set(doc)=={
        "protocol","status","seeds","cases","policies",
        "trials_per_case_seed","world_truth_visibility_to_policy",
        "trusted_anchor_authority","trial_records","summary",
        "registered_controls","limitations",
    },"root schema mismatch")
    equal("EPV-001",doc["protocol"],"protocol")
    equal("PUBLIC_SYNTHETIC_EVIDENCE_VIGILANCE_NOT_VALIDATED",doc["status"],"status")
    equal(list(SEEDS),doc["seeds"],"seeds")
    equal(list(SCENARIOS),doc["cases"],"cases")
    equal(list(MODES),doc["policies"],"policies")
    equal(64,doc["trials_per_case_seed"],"fixture size")
    equal("NOT_PASSED",doc["world_truth_visibility_to_policy"],"oracle access")
    equal("FIXTURE_ASSUMPTION_NOT_WORLD_TRUTH",doc["trusted_anchor_authority"],"authority")
    equal(list(LIMITS),doc["limitations"],"limitations")
    records=doc["trial_records"]
    require(type(records) is list and len(records)==3072,
            "missing trial inventory")
    pos=0;rebuilt=[]
    for seed in SEEDS:
        rng=random.Random(seed)
        for scenario in SCENARIOS:
            for index in range(64):
                expected=reconstruct_trial(rng,seed,scenario,index)
                observed=records[pos]
                require(type(observed) is dict and
                        set(observed)==set(expected)|{"decisions"},
                        "trial schema mismatch")
                for key in expected:equal(expected[key],observed[key],
                                          f"trial.{pos}.{key}")
                choices={name:independent_decision(expected,name) for name in MODES}
                equal(choices,observed["decisions"],f"decision.{pos}")
                expected["decisions"]=choices
                rebuilt.append(expected)
                pos+=1
    computed=score(rebuilt)
    equal(computed,doc["summary"],"aggregate")
    tests=control_summary(computed)
    equal(tests,doc["registered_controls"],"registered checks")
    require(all(tests.values()),"registered falsification control failure")
    return {
        "verdict":"INDEPENDENT_SYNTHETIC_SPECIFICATION_CONSISTENT_ONLY",
        "trials":len(rebuilt),"scenarios":len(SCENARIOS),
        "policies":len(MODES),
        "critical_known_false_positive":computed["POISONED_AUTHORITY"]["evidence_first"]["incorrect"],
        "world_truth_assured":"NO",
        "source_authenticity_assured":"NO",
        "consciousness_or_general_reasoning":"NOT_TESTED",
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact",type=Path)
    p.add_argument("--sha256",required=True)
    a=p.parse_args(argv)
    try:r=verify(a.artifact.read_bytes(),a.sha256)
    except (ValueError,KeyError,TypeError,OSError,OverflowError,RecursionError) as error:
        print("VERDICT: INVALID_OR_UNVERIFIABLE",error,file=sys.stderr)
        return 1
    print("VERDICT: INDEPENDENT_SYNTHETIC_SPECIFICATION_CONSISTENT_ONLY")
    print("DETAILS:",json.dumps(r,sort_keys=True))
    return 0

if __name__=="__main__":sys.exit(main())
