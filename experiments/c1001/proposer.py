"""C1-001 known test proposer. Not a sandbox for arbitrary model-generated code."""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path


def json_line(value):
    return json.dumps(value,sort_keys=True,separators=(",",":")).encode()+b"\n"


def predicate(name,x):
    if name=="even": return int(x%2==0)
    if name=="multiple3": return int(x%3==0)
    if name=="multiple5": return int(x%5==0)
    if name=="lowhalf": return int(x<16)
    if name=="bit1": return int(bool(x&2))
    if name=="bit2": return int(bool(x&4))
    if name=="bit3": return int(bool(x&8))
    if name=="mod4eq1": return int(x%4==1)
    raise ValueError("invalid predicate")


def greedy(names,observations):
    used={a["probe"] for a in observations}
    def gain(x):
        groups=[sum(predicate(n,x)==outcome for n in names)
                for outcome in (0,1)]
        return len(names)-sum(s*s for s in groups)/len(names)
    return max((x for x in range(32) if x not in used),
               key=lambda x:(gain(x),-x))


def exchange(sock,message):
    sock.sendall(json_line(message))
    result=bytearray()
    while len(result)<2048:
        byte=sock.recv(1)
        if not byte: raise RuntimeError("evaluator disconnected")
        if byte==b"\n": return json.loads(result)
        result.extend(byte)
    raise RuntimeError("evaluator response too long")


def check_file_denial(path):
    # The TEST HARNESS supplies a known path; evaluator protocol does NOT.
    for filename in (path,path.parent):
        try:
            with filename.open("rb"): pass
        except PermissionError:
            continue
        except IsADirectoryError:
            raise RuntimeError("directory unexpectedly accessible")
        raise RuntimeError("private evaluator material was readable")


def honest_client(sockpath,private,uid):
    if os.geteuid()!=uid:
        raise RuntimeError("proposer not under declared restricted UID")
    check_file_denial(private)
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
        sock.settimeout(8)
        sock.connect(str(sockpath))
        response=exchange(sock,{"op":"HELLO"})
        if response.get("status")!="PUBLIC_CONTEXT":
            raise RuntimeError("HELLO not accepted")
        view=response["context"]
        allowed={"protocol","trial_id","candidate_names","domain",
                 "predicate_definitions","observations","remaining_budget",
                 "commitment_sha256","solved"}
        if set(view)!=allowed:
            raise RuntimeError("unexpected public data schema")
        if view["remaining_budget"]!=6:
            raise RuntimeError("invalid initial budget")
        for bad in (
            {"op":"GET_SECRET"},
            {"op":"READ_FILE"},
            {"op":"HELLO","truth":"fake"},
            {"op":"PROBE","probe":True},
            {"op":"PROBE","probe":-1},
            {"op":"PROBE","probe":0,"approval":True},
        ):
            if exchange(sock,bad)!={"error":"SCHEMA_DENIED"}:
                raise RuntimeError("bad action was not schema-denied")
        if view["solved"]:
            raise RuntimeError("vacuously solved zero-probe test")
        while not view["solved"] and view["remaining_budget"]>0:
            selected=greedy(view["candidate_names"],view["observations"])
            response=exchange(sock,{"op":"PROBE","probe":selected})
            if response.get("status")!="PROBE_OK":
                raise RuntimeError("legal probe denied")
            view=response["context"]
            if any(k in view for k in
                   ("truth","salt","secret","task_seed","private_path")):
                raise RuntimeError("secret in allowed response")
            if len(view["observations"])==1:
                if exchange(sock,{"op":"PROBE","probe":selected})!={
                    "error":"DUPLICATE_PROBE"}:
                    raise RuntimeError("duplicate was admitted")
        if not view["solved"]:
            raise RuntimeError("proposer did not solve task")
        print("C1_HONEST_PROPOSER_SUCCESS",json.dumps({
            "uid":os.geteuid(),"probes":len(view["observations"]),
            "solved":view["solved"],
            "private_reads":"DENIED_BY_LINUX_DAC",
            "protocol_injection":"DENIED_BY_SCHEMA",
        },sort_keys=True))


def unauthorized_peer(sockpath,uid):
    if os.geteuid()!=uid:
        raise RuntimeError("other-peer UID mismatch")
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
        sock.settimeout(6)
        sock.connect(str(sockpath))
        buf=bytearray()
        while len(buf)<2048:
            char=sock.recv(1)
            if char==b"\n": break
            if not char: raise RuntimeError("missing peer rejection")
            buf.extend(char)
        if json.loads(buf)!={"error":"UNAUTHORIZED_PEER"}:
            raise RuntimeError("unauthorized peer accepted")
    print("C1_OTHER_PEER_DENIED_BY_SO_PEERCRED")


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--socket-path",type=Path,required=True)
    p.add_argument("--private-task-file",type=Path)
    p.add_argument("--expected-uid",type=int,required=True)
    p.add_argument("--other-peer",action="store_true")
    a=p.parse_args(argv)
    try:
        if a.other_peer:
            unauthorized_peer(a.socket_path,a.expected_uid)
        else:
            if a.private_task_file is None:
                raise RuntimeError("test harness must supply private file path")
            honest_client(a.socket_path,a.private_task_file,a.expected_uid)
    except (OSError,RuntimeError,ValueError) as exc:
        print("C1_CLIENT_FAIL:",type(exc).__name__,str(exc),file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
