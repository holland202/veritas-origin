"""C1-001: a narrow Linux Unix-socket evaluator under a separate non-root UID.

Demonstrates DAC and SO_PEERCRED for one known test client; this does NOT
sandbox arbitrary code or attest independent human approvals.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import secrets
import socket
import stat
import struct
import sys
from pathlib import Path

NAMES = ("even","multiple3","multiple5","lowhalf","bit1","bit2","bit3","mod4eq1")
DEFINITIONS = {
    "even":"x % 2 == 0","multiple3":"x % 3 == 0",
    "multiple5":"x % 5 == 0","lowhalf":"x < 16",
    "bit1":"(x & 2) != 0","bit2":"(x & 4) != 0",
    "bit3":"(x & 8) != 0","mod4eq1":"x % 4 == 1",
}
MAX_STEPS=6
MAX_LINE=2048

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),
                      ensure_ascii=False,allow_nan=False).encode()

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

def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError("duplicate JSON key")
        out[k]=v
    return out

def no_nonfinite(x):
    raise ValueError("nonfinite JSON numeric value")

def parse_request(raw):
    if type(raw) is not bytes or len(raw)>MAX_LINE:
        raise ValueError("request too large")
    doc=json.loads(raw,object_pairs_hook=unique,parse_constant=no_nonfinite)
    if type(doc) is not dict or "op" not in doc:
        raise ValueError("invalid request object")
    if doc["op"]=="HELLO" and set(doc)=={"op"}:
        return "HELLO",None
    if doc["op"]=="PROBE" and set(doc)=={"op","probe"}:
        if type(doc["probe"]) is not int or not 0<=doc["probe"]<32:
            raise ValueError("probe must be a bounded integer")
        return "PROBE",doc["probe"]
    raise ValueError("unknown action or prohibited fields")

def emit(sock,obj):
    payload=canonical(obj)+b"\n"
    if len(payload)>MAX_LINE: raise RuntimeError("response too large")
    sock.sendall(payload)

def read_line(sock):
    out=bytearray()
    while len(out)<=MAX_LINE:
        c=sock.recv(1)
        if not c:
            return None if not out else bytes(out)
        if c==b"\n":
            return bytes(out)
        out.extend(c)
    raise ValueError("overlong request line")

def exclusive_write(path,raw):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,"wb") as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())
    if stat.S_IMODE(path.stat().st_mode)!=0o600:
        raise RuntimeError("private receipt mode mismatch")

class Session:
    def __init__(self):
        self.trial_id=secrets.token_hex(16)
        self.salt=secrets.token_hex(32)
        self.candidates=tuple(sorted(secrets.SystemRandom().sample(NAMES,4)))
        self.truth=secrets.choice(self.candidates)
        self.commitment=digest({
            "trial_id":self.trial_id,"salt":self.salt,
            "candidates":list(self.candidates),"truth":self.truth,
        })
        self.active=self.candidates
        self.used=set()
        self.events=[]
        self.session_open=False
        self.finished=False
        self.peer_denials=0
        self.protocol_denials=0

    def public_view(self):
        return {
            "protocol":"C1-001","trial_id":self.trial_id,
            "candidate_names":list(self.active),
            "domain":list(range(32)),
            "predicate_definitions":dict(DEFINITIONS),
            "observations":[{"probe":v["probe"],"outcome":v["outcome"]}
                            for v in self.events],
            "remaining_budget":MAX_STEPS-len(self.events),
            "commitment_sha256":self.commitment,
            "solved":len(self.active)==1,
        }

    def react(self,raw):
        try:
            op,probe=parse_request(raw)
        except (ValueError,TypeError,UnicodeDecodeError):
            self.protocol_denials+=1
            return {"error":"SCHEMA_DENIED"}
        if op=="HELLO":
            self.session_open=True
            return {"status":"PUBLIC_CONTEXT","context":self.public_view()}
        if not self.session_open:
            self.protocol_denials+=1
            return {"error":"HELLO_REQUIRED"}
        if self.finished:
            self.protocol_denials+=1
            return {"error":"SESSION_FINISHED"}
        if probe in self.used:
            self.protocol_denials+=1
            return {"error":"DUPLICATE_PROBE"}
        if len(self.events)>=MAX_STEPS:
            self.protocol_denials+=1
            return {"error":"PROBE_BUDGET_EXHAUSTED"}
        original=list(self.active)
        bit=predicate(self.truth,probe)
        self.active=tuple(h for h in self.active if predicate(h,probe)==bit)
        self.used.add(probe)
        self.events.append({
            "step":len(self.events),"before":original,"probe":probe,
            "outcome":bit,"after":list(self.active)
        })
        self.finished=len(self.active)==1 or len(self.events)==MAX_STEPS
        return {"status":"PROBE_OK","context":self.public_view()}

    def private_task(self):
        return {
            "trial_id":self.trial_id,"salt":self.salt,
            "truth":self.truth,"candidates":list(self.candidates),
            "commitment_sha256":self.commitment,
        }

    def receipt(self,evaluator_uid,allowed_uid):
        return {
            "protocol":"C1-001",
            "scope":"PARTIAL_DAC_DEMONSTRATED_NOT_SANDBOXED",
            "trial":self.private_task(),"events":list(self.events),
            "solved":len(self.active)==1,
            "peer_uid_allowed":allowed_uid,
            "evaluator_euid":evaluator_uid,
            "peer_denials":self.peer_denials,
            "protocol_denials":self.protocol_denials,
            "untrusted_proposer_access_log":"NOT_ACCEPTED_AS_ISOLATION_PROOF",
            "os_controls":{
                "private_dir_mode":"0700","private_file_mode":"0600",
                "transport":"AF_UNIX_SOCK_STREAM_SO_PEERCRED",
                "socket_mode":"0660","network_egress_blocked":False,
                "full_process_isolation":False,
            },
        }

def enforce_fs(private,socket_dir,expected_uid,group):
    if os.geteuid()!=expected_uid or os.getegid()!=group:
        raise RuntimeError("evaluator UID/GID not privilege-separated")
    if private.is_symlink() or socket_dir.is_symlink():
        raise RuntimeError("symlinked security directory refused")
    p,s=private.stat(),socket_dir.stat()
    if p.st_uid!=expected_uid or stat.S_IMODE(p.st_mode)!=0o700:
        raise RuntimeError("private directory must be evaluator-owned 0700")
    if s.st_gid!=group or stat.S_IMODE(s.st_mode)!=0o770:
        raise RuntimeError("socket directory must be group-owned 0770")

def serve(private,socket_path,evaluator_uid,proposer_uid,socket_gid):
    if not hasattr(socket,"SO_PEERCRED"):
        raise RuntimeError("Linux SO_PEERCRED missing; abort")
    enforce_fs(private,socket_path.parent,evaluator_uid,socket_gid)
    if socket_path.exists() or socket_path.is_symlink():
        raise RuntimeError("socket path already used; no overwrite")
    session=Session()
    exclusive_write(private/"answer.json",canonical(session.private_task())+b"\n")
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    try:
        listener.bind(str(socket_path))
        os.chmod(socket_path,0o660)
        if stat.S_IMODE(socket_path.stat().st_mode)!=0o660:
            raise RuntimeError("socket mode mismatch")
        listener.listen(3)
        listener.settimeout(25)
        while not session.finished:
            conn,_=listener.accept()
            with conn:
                conn.settimeout(8)
                pid,uid,gid=struct.unpack(
                    "3i",conn.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,
                                         struct.calcsize("3i"))
                )
                if uid!=proposer_uid:
                    session.peer_denials+=1
                    emit(conn,{"error":"UNAUTHORIZED_PEER"})
                    continue
                try:
                    while not session.finished:
                        line=read_line(conn)
                        if line is None: break
                        emit(conn,session.react(line))
                except (ValueError,socket.timeout):
                    session.protocol_denials+=1
                    try: emit(conn,{"error":"INVALID_STREAM"})
                    except OSError: pass
        exclusive_write(private/"receipt.json",
                        canonical(session.receipt(os.geteuid(),proposer_uid))+b"\n")
    finally:
        listener.close()
        if socket_path.exists(): socket_path.unlink()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-dir",required=True,type=Path)
    p.add_argument("--socket-path",required=True,type=Path)
    p.add_argument("--evaluator-uid",required=True,type=int)
    p.add_argument("--proposer-uid",required=True,type=int)
    p.add_argument("--socket-gid",required=True,type=int)
    a=p.parse_args(argv)
    try:
        serve(a.private_dir,a.socket_path,a.evaluator_uid,
              a.proposer_uid,a.socket_gid)
    except (OSError,RuntimeError,ValueError) as exc:
        print("C1_EVALUATOR_FAIL:",type(exc).__name__,str(exc),file=sys.stderr)
        return 1
    print("C1_EVALUATOR_SESSION_COMPLETE: receipt sealed before disclosure")
    return 0

if __name__=="__main__":
    sys.exit(main())
