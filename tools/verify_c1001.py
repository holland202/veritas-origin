"""Independently replay C1-001 receipt AFTER the evaluator has closed.

Does not import evaluator/proposer; mathematical agreement is not an
attestation of Linux permissions or authenticity of the local root recorder.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

MAX_FILE=32768
SCOPE="PARTIAL_DAC_DEMONSTRATED_NOT_SANDBOXED"
NAMES={"even","multiple3","multiple5","lowhalf","bit1","bit2","bit3","mod4eq1"}
FIELDS={
    "protocol","scope","trial","events","solved","peer_uid_allowed",
    "evaluator_euid","peer_denials","protocol_denials",
    "untrusted_proposer_access_log","os_controls",
}

def demand(x,label):
    if not x: raise ValueError(label)

def unique(pairs):
    out={}
    for k,v in pairs:
        demand(k not in out,"duplicate JSON key")
        out[k]=v
    return out

def nonfinite(s):
    raise ValueError("nonfinite JSON number: "+s)

def canonical(doc):
    return json.dumps(doc,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode()

def predicate(name,x):
    if name=="even": return int(x%2==0)
    if name=="multiple3": return int(x%3==0)
    if name=="multiple5": return int(x%5==0)
    if name=="lowhalf": return int(x<16)
    if name=="bit1": return int((x&2)!=0)
    if name=="bit2": return int((x&4)!=0)
    if name=="bit3": return int((x&8)!=0)
    if name=="mod4eq1": return int(x%4==1)
    raise ValueError("unsupported predicate")

def verify(raw,declared_sha):
    demand(type(raw) is bytes and len(raw)<=MAX_FILE,
           "invalid or oversized receipt")
    demand(type(declared_sha) is str and len(declared_sha)==64 and
           all(c in "0123456789abcdef" for c in declared_sha),
           "invalid pinned sha")
    demand(hashlib.sha256(raw).hexdigest()==declared_sha,"SHA256 mismatch")
    doc=json.loads(raw,object_pairs_hook=unique,parse_constant=nonfinite)
    demand(type(doc) is dict and set(doc)==FIELDS,"incorrect receipt schema")
    demand(doc["protocol"]=="C1-001" and doc["scope"]==SCOPE,
           "invalid scope; cannot promote to full isolation")
    task=doc["trial"]
    demand(type(task) is dict and set(task)=={
        "trial_id","salt","truth","candidates","commitment_sha256"
    },"invalid private task disclosure schema")
    demand(type(task["trial_id"]) is str and len(task["trial_id"])==32 and
           all(c in "0123456789abcdef" for c in task["trial_id"]),
           "invalid trial id")
    demand(type(task["salt"]) is str and len(task["salt"])==64 and
           all(c in "0123456789abcdef" for c in task["salt"]),
           "invalid salt")
    demand(type(task["candidates"]) is list and len(task["candidates"])==4
           and len(set(task["candidates"]))==4 and
           all(type(v) is str and v in NAMES for v in task["candidates"])
           and task["candidates"]==sorted(task["candidates"]),
           "invalid challenge roster")
    demand(type(task["truth"]) is str and
           task["truth"] in task["candidates"],"hidden truth invalid")
    expected=hashlib.sha256(canonical({
        "trial_id":task["trial_id"],"salt":task["salt"],
        "candidates":task["candidates"],"truth":task["truth"]
    })).hexdigest()
    demand(task["commitment_sha256"]==expected,
           "salted commitment mismatch")
    demand(type(doc["events"]) is list and 1<=len(doc["events"])<=6,
           "nonvacuous probe count invalid")
    remaining=tuple(task["candidates"])
    visited=set()
    for i,row in enumerate(doc["events"]):
        demand(type(row) is dict and set(row)=={
            "step","before","probe","outcome","after"
        },"event schema mismatch")
        demand(type(row["step"]) is int and row["step"]==i,
               "event sequence mismatch")
        x=row["probe"]
        demand(type(x) is int and x in range(32) and x not in visited,
               "probe domain/duplicate violation")
        demand(row["before"]==list(remaining) and len(remaining)>1,
               "invalid prior-state history")
        truth_bit=predicate(task["truth"],x)
        demand(type(row["outcome"]) is int and
               row["outcome"]==truth_bit,"oracle outcome mismatch")
        remaining=tuple(n for n in remaining if predicate(n,x)==truth_bit)
        demand(row["after"]==list(remaining),"candidate update mismatch")
        visited.add(x)
    demand(type(doc["solved"]) is bool and
           doc["solved"]==(len(remaining)==1) and doc["solved"],
           "honest success non-vacuity failed")
    demand(type(doc["peer_uid_allowed"]) is int and
           doc["peer_uid_allowed"]==32002 and
           type(doc["evaluator_euid"]) is int and
           doc["evaluator_euid"]==32001 and
           doc["peer_uid_allowed"]!=doc["evaluator_euid"],
           "unexpected identities")
    demand(type(doc["peer_denials"]) is int and
           doc["peer_denials"]>=1,"no unauthorized peer was denied")
    demand(type(doc["protocol_denials"]) is int and
           doc["protocol_denials"]>=7,"invalid actions did not exercise guard")
    demand(doc["untrusted_proposer_access_log"]==
           "NOT_ACCEPTED_AS_ISOLATION_PROOF",
           "attempted promotion of self-reported access log")
    demand(doc["os_controls"]=={
        "private_dir_mode":"0700","private_file_mode":"0600",
        "transport":"AF_UNIX_SOCK_STREAM_SO_PEERCRED",
        "socket_mode":"0660","network_egress_blocked":False,
        "full_process_isolation":False,
    },"unsupported sandbox security assertion")
    return {
        "verdict":"MATHEMATICAL_RECEIPT_CONSISTENT_ONLY",
        "probes":len(doc["events"]),"solved":True,
        "commitment":"MATCHED_AFTER_DISCLOSURE",
        "evaluator_process_boundary":"RECORDED_DAC_ASSERTION_ONLY",
        "os_enforcement":"MUST_BE_TESTED_SEPARATELY_ON_LINUX",
        "secure_sandbox":"NOT_ESTABLISHED",
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("receipt",type=Path)
    p.add_argument("--sha256",required=True)
    args=p.parse_args(argv)
    try:
        outcome=verify(args.receipt.read_bytes(),args.sha256)
    except (ValueError,TypeError,KeyError,OSError,OverflowError) as exc:
        print("VERDICT: INVALID_OR_UNVERIFIABLE",exc,file=sys.stderr)
        return 1
    print("VERDICT: MATHEMATICAL_RECEIPT_CONSISTENT_ONLY")
    print("DETAILS:",json.dumps(outcome,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
