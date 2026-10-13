#!/usr/bin/env python3
"""AUTO-TWIN-001: 8-domain, offline dynamics + optional bounded Claude adversarial proposals.
All effects simulated. Does not operate equipment or claim real-world safety.
Python stdlib only. No request submission in 'selftest', 'baseline', or 'report'.
"""
import argparse, hashlib, json, os, pathlib, sys, urllib.request, urllib.error
from datetime import datetime, timezone

VERSION = "AUTO-TWIN-001-v1"
DOMAINS = {
    "drone": (9.0, 3.0, 0.25, 5.0),
    "mobile_robot": (2.0, 1.5, 0.15, 0.6),
    "robot_arm": (1.2, 2.0, 0.08, 0.4),
    "industrial_machine": (2.5, 4.0, 0.08, 0.7),
    "warehouse_agv": (3.0, 2.0, 0.20, 1.0),
    "building_actuator": (0.4, 0.8, 0.35, 0.4),
    "marine_robot": (4.0, 0.8, 0.50, 4.0),
    "software_agent": (1.0, 1.0, 0.0, 0.0),
}
SCENARIOS = ("nominal", "obstacle", "revoked", "stale", "spoofed", "missing_sensor",
             "replay", "changed_action", "conflict")
MAX_CLAUDE_CALLS = 2
MODEL = "claude-haiku-4-5-20251001"
MAX_OUTPUT_TOKENS = 700
MAX_INPUT_CHARS = 5500

def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), allow_nan=False)

def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def stop_bound(v, a, latency, margin):
    return v*v/(2*a) + v*latency + margin

def generate(domain, scenario, seed=0, delta=None):
    v,a,l,m = DOMAINS[domain]
    gap = stop_bound(v,a,l,m)
    perturb = (seed % 11)*0.13
    if delta is not None:
        perturb = delta
    distance = gap+8+perturb if scenario=="nominal" else gap-0.6-perturb
    return dict(domain=domain, scenario=scenario, seed=seed, speed=v,
                brake=a, latency=l, margin=m, distance=distance,
                token_epoch=1, world_epoch=2 if scenario=="revoked" else 1,
                token_seen=scenario=="replay",
                requested_action="accelerate" if scenario=="changed_action" else "move",
                sensor_valid=scenario not in ("missing_sensor","spoofed","conflict","stale"),
                sensor_age=20 if scenario=="stale" else 0,
                sensor_conflict=scenario=="conflict",
                sensor_claim=distance+100 if scenario=="spoofed" else distance)

def fresh_gate(c):
    """Reference authorization policy, NOT an imported Sovereign Veritas runtime."""
    if c["token_epoch"] != c["world_epoch"] or c["token_seen"]:
        return "REFUSE"
    if c["requested_action"]!="move":
        return "REFUSE"
    if not c["sensor_valid"] or c["sensor_conflict"] or c["sensor_age"]>1:
        return "DEFER"
    if c["distance"] < stop_bound(c["speed"],c["brake"],c["latency"],c["margin"]):
        return "DEFER"
    return "ALLOW"

def stale_gate(c):
    """Intentionally unsafe comparator: an earlier approval is cached forever."""
    return "ALLOW"

def trial(c):
    correct=fresh_gate(c)
    cached=stale_gate(c)
    nominal=(c["scenario"]=="nominal")
    return dict(case=c, expected="ALLOW" if nominal else
                ("REFUSE" if c["scenario"] in ("revoked","replay","changed_action") else "DEFER"),
                fresh=correct, cached=cached,
                fresh_safe=(correct=="ALLOW")==nominal,
                cached_unsafe=(cached=="ALLOW" and not nominal),
                stopping_bound=stop_bound(c["speed"],c["brake"],c["latency"],c["margin"]))

def selftest():
    rows=[trial(generate(d,s,i)) for d in DOMAINS for s in SCENARIOS for i in range(40)]
    assert len(rows)==2880
    assert all(r["fresh"]==r["expected"] for r in rows)
    assert sum(r["cached_unsafe"] for r in rows)==2560
    assert all(r["fresh_safe"] for r in rows)
    # Anti-vacuity: a refuse-everything mutant fails the 320 positive cases.
    assert sum(r["expected"]=="ALLOW" for r in rows)==320
    # Reversing comparator must be discovered, not silently accepted.
    assert all(stop_bound(*DOMAINS[d])>0 for d in DOMAINS)
    print("SELFTEST PASS: 2880 deterministic simulated cases; 320 positive, 2560 negative")
    return rows

def newdir(base):
    t=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    path=pathlib.Path(base).expanduser()/("run-"+t)
    path.mkdir(parents=True,exist_ok=False)
    return path

def preserve(folder, objects):
    for name, obj in objects.items():
        (folder/name).write_text(json.dumps(obj,sort_keys=True,indent=2)+"\n")
    paths=sorted(x for x in folder.iterdir() if x.is_file() and x.name!="SHA256SUMS")
    (folder/"SHA256SUMS").write_text("".join(
       f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in paths))
    print("evidence:",folder)

def baseline(base):
    rows=selftest()
    counts={d:{"total":sum(r["case"]["domain"]==d for r in rows),
               "fresh_expected":sum(r["case"]["domain"]==d and r["fresh"]==r["expected"] for r in rows),
               "stale_unsafe":sum(r["case"]["domain"]==d and r["cached_unsafe"] for r in rows)}
            for d in DOMAINS}
    output=newdir(base)
    preserve(output,{"summary.json":{"version":VERSION,"scope":"SIMULATION_ONLY",
                     "source_sha256":hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                     "total":len(rows),"domains":counts,"paid_calls":0,"trained_models":0}})
    return output

def validate_proposals(content):
    """Fail closed on malformed / out-of-bound Claude results."""
    if not isinstance(content,dict) or not isinstance(content.get("cases"),list):
        raise ValueError("expected JSON object with cases list")
    proposals=content["cases"]
    if not 1<=len(proposals)<=12:
        raise ValueError("1..12 proposals required")
    accepted=[]
    for p in proposals:
        if not isinstance(p,dict) or set(p)!={"domain","scenario","seed","perturb"}:
            raise ValueError("invalid proposal keys")
        if p["domain"] not in DOMAINS or p["scenario"] not in SCENARIOS:
            raise ValueError("unknown domain/scenario")
        if type(p["seed"]) is not int or not 0<=p["seed"]<=100000:
            raise ValueError("seed out of bounds")
        if type(p["perturb"]) not in (float,int) or not 0<=p["perturb"]<=5:
            raise ValueError("perturb out of bounds")
        accepted.append(trial(generate(p["domain"],p["scenario"],p["seed"],p["perturb"])))
    return accepted

def claude(base, calls, model):
    if not 1<=calls<=MAX_CLAUDE_CALLS:
        raise SystemExit("pilot cap is 2 calls")
    if model!=MODEL:
        raise SystemExit("model must be pinned in source; amendment required")
    key=os.environ.get("ANTHROPIC_API_KEY","")
    if not(key.startswith("sk-ant-") and len(key)>=40 and not any(c.isspace() for c in key)):
        raise SystemExit("Missing/malformed API key (kept only in device environment)")
    prompt=(
      "Generate hard *SIMULATED* authorization scenario configurations to stress a deterministic "
      "policy comparing fresh authorization against an intentionally unsafe cached ALLOW. "
      "Domains: "+", ".join(DOMAINS)+". Scenarios: "+", ".join(SCENARIOS)+". "
      "Return ONLY JSON: {\"cases\":[{\"domain\":\"drone\",\"scenario\":\"obstacle\","
      "\"seed\":1,\"perturb\":0.5}, ...]}. Supply 8-12 diverse cases, each scenario is "
      "simulated; avoid hardware-specific commands, code, credentials, and operational instructions. "
      "Fields MUST be domain,scenario,seed integer 0..100000,perturb number 0..5. "
      "Look for blind spots; don't assert that any case proves real-world safety."
    )[:MAX_INPUT_CHARS]
    output=newdir(base)
    ledger={"version":VERSION,"model":model,"max_output_tokens":MAX_OUTPUT_TOKENS,
            "maximum_calls":calls,"requests":[],"status":"STARTED"}
    # Write before external calls; never overwrite records.
    preserve(output,{"ledger.json":ledger})
    for j in range(calls):
        body={"model":model,"max_tokens":MAX_OUTPUT_TOKENS,
              "temperature":0.7,"messages":[{"role":"user","content":prompt}]}
        payload=canonical(body).encode()
        req=urllib.request.Request("https://api.anthropic.com/v1/messages",
            data=payload,method="POST",headers={"x-api-key":key,
            "anthropic-version":"2023-06-01","content-type":"application/json"})
        item={"iteration":j+1,"request_sha256":hashlib.sha256(payload).hexdigest()}
        try:
            with urllib.request.urlopen(req,timeout=60) as resp:
                raw=resp.read(100000).decode()
                item["http_status"]=resp.status
            response=json.loads(raw)
            item["usage"]=response.get("usage",{})
            texts=[c.get("text","") for c in response.get("content",[]) if c.get("type")=="text"]
            data=json.loads("\n".join(texts))
            cases=validate_proposals(data)
            item["result"]="VALIDATED_PROPOSALS"
            item["tested"]=len(cases)
            item["unexpected"]=sum(r["fresh"]!=r["expected"] for r in cases)
            item["cases"]=cases
        except Exception as exc:
            item["result"]="FAILED_OR_UNEVALUABLE"
            item["error_type"]=type(exc).__name__
            if isinstance(exc,urllib.error.HTTPError):
                item["http_status"]=exc.code
        ledger["requests"].append(item)
        preserve(output,{"ledger.json":ledger})
    ledger["status"]="COMPLETE_WITH_ERRORS" if any(x["result"]!="VALIDATED_PROPOSALS" for x in ledger["requests"]) else "COMPLETE"
    preserve(output,{"ledger.json":ledger})
    print("API calls attempted:",len(ledger["requests"]))
    print("unexpected simulated outcomes:",sum(x.get("unexpected",0) for x in ledger["requests"]))
    print("usage (API-reported):",[x.get("usage") for x in ledger["requests"]])
    print("No real-world control or integrated SV Gate tested")
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("selftest","baseline","claude-pilot"))
    p.add_argument("--evidence",default="~/auto-twin-001-evidence")
    p.add_argument("--calls",type=int,default=1)
    p.add_argument("--model",default=MODEL)
    args=p.parse_args()
    if args.command=="selftest": selftest()
    elif args.command=="baseline": baseline(args.evidence)
    else: claude(args.evidence,args.calls,args.model)

if __name__=="__main__":
    main()
