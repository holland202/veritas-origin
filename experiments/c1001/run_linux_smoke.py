"""C1-001 actual Linux per-UID DAC/AF_UNIX integration smoke.

Requires root *only* for ephemeral provisioning; refuses to mock OS isolation.
Proposer and evaluator are distinct non-root UIDs. Test client is controlled,
not an arbitrary hostile program; network, ptrace, kernel and side channels
are explicitly OUTSIDE this test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
EVALUATOR=Path(__file__).resolve().with_name("evaluator.py")
CLIENT=Path(__file__).resolve().with_name("proposer.py")
E_UID=32001
P_UID=32002
O_UID=32004
GID=32003

def demand(condition,reason):
    if not condition:
        raise RuntimeError(reason)

def restricted(uid,command,timeout=16,cwd=None):
    env={"PATH":"/usr/bin:/bin","LANG":"C.UTF-8","HOME":"/nonexistent"}
    args=[
        "setpriv",f"--reuid={uid}",f"--regid={GID}",
        "--clear-groups","--no-new-privs",sys.executable,*command,
    ]
    return subprocess.run(
        args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        check=False,timeout=timeout,env=env,cwd=str(cwd or ROOT),
    )

def execute(output):
    demand(platform.system()=="Linux","real Linux kernel required")
    demand(os.geteuid()==0,"requires real root provisioning; refuse mock")
    demand(shutil.which("setpriv") is not None,"setpriv not available")
    demand(hasattr(socket,"SO_PEERCRED"),"real Linux SO_PEERCRED unavailable")
    demand(E_UID!=P_UID and P_UID!=O_UID,"invalid UID separation")
    parent=Path(tempfile.mkdtemp(prefix="c1001-linux-"))
    private=parent/"private"
    public=parent/"socket"
    process=None
    try:
        os.chmod(parent,0o755)
        private.mkdir(mode=0o700)
        public.mkdir(mode=0o770)
        os.chown(private,E_UID,GID)
        os.chmod(private,0o700)
        os.chown(public,0,GID)
        os.chmod(public,0o770)
        demand(private.stat().st_uid==E_UID and
               stat.S_IMODE(private.stat().st_mode)==0o700,
               "private directory ownership/mode incorrect")
        demand(public.stat().st_gid==GID and
               stat.S_IMODE(public.stat().st_mode)==0o770,
               "socket directory ownership/mode incorrect")
        # Non-root users may not traverse the GitHub runner's checkout.
        # Stage only public reviewed programs outside it; never stage secrets.
        programs=parent/"programs"
        programs.mkdir(mode=0o755)
        staged_evaluator=programs/"evaluator.py"
        staged_proposer=programs/"proposer.py"
        for original,staged in ((EVALUATOR,staged_evaluator),
                                (CLIENT,staged_proposer)):
            shutil.copyfile(original,staged)
            os.chmod(staged,0o644)
            demand(hashlib.sha256(original.read_bytes()).digest()==
                   hashlib.sha256(staged.read_bytes()).digest(),
                   "staged program integrity mismatch")
        socket_path=public/"eval.sock"
        env={"PATH":"/usr/bin:/bin","LANG":"C.UTF-8","HOME":"/nonexistent"}
        argv=[
            "setpriv",f"--reuid={E_UID}",f"--regid={GID}",
            "--clear-groups","--no-new-privs",sys.executable,str(staged_evaluator),
            "--private-dir",str(private),"--socket-path",str(socket_path),
            "--evaluator-uid",str(E_UID),"--proposer-uid",str(P_UID),
            "--socket-gid",str(GID),
        ]
        process=subprocess.Popen(argv,env=env,cwd=str(parent),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,text=True)
        for _ in range(100):
            if socket_path.exists(): break
            if process.poll() is not None:
                sout,serr=process.communicate(timeout=2)
                raise RuntimeError("evaluator exited before socket: "+serr[:400]+sout[:100])
            time.sleep(.05)
        demand(socket_path.exists(),"evaluator socket never opened")
        sd=socket_path.stat()
        demand(stat.S_ISSOCK(sd.st_mode) and sd.st_uid==E_UID
               and sd.st_gid==GID and stat.S_IMODE(sd.st_mode)==0o660,
               "socket peer boundary modes/identity mismatched")
        secret_file=private/"answer.json"
        demand(secret_file.is_file() and
               stat.S_IMODE(secret_file.stat().st_mode)==0o600 and
               secret_file.stat().st_uid==E_UID,
               "private answer not evaluator-only")
        outsider=restricted(O_UID,[
            str(staged_proposer),"--socket-path",str(socket_path),
            "--expected-uid",str(O_UID),"--other-peer"
        ],cwd=parent)
        demand(outsider.returncode==0 and
               "C1_OTHER_PEER_DENIED_BY_SO_PEERCRED" in outsider.stdout,
               "foreign socket peer incorrectly admitted: "+outsider.stderr[:500])
        proposer=restricted(P_UID,[
            str(staged_proposer),"--socket-path",str(socket_path),
            "--private-task-file",str(secret_file),
            "--expected-uid",str(P_UID),
        ],cwd=parent)
        demand(proposer.returncode==0 and
               "C1_HONEST_PROPOSER_SUCCESS" in proposer.stdout,
               "honest restricted proposer failed: "+proposer.stderr[:500])
        sout,serr=process.communicate(timeout=15)
        demand(process.returncode==0 and
               "C1_EVALUATOR_SESSION_COMPLETE" in sout,
               "evaluator did not seal successful receipt: "+serr[:500])
        receipt=private/"receipt.json"
        demand(receipt.is_file() and
               stat.S_IMODE(receipt.stat().st_mode)==0o600 and
               receipt.stat().st_uid==E_UID,"receipt lacked private owner/mode")
        raw=receipt.read_bytes() # PRIVILEGED HARNESS, AFTER session ends only
        sys.path.insert(0,str(ROOT))
        from tools.verify_c1001 import verify
        sha=hashlib.sha256(raw).hexdigest()
        replay=verify(raw,sha)
        demand(replay["solved"] is True,"mathematical replay failure")
        output.mkdir(parents=True,exist_ok=True)
        copied=output/"c1001-independent-replay-receipt.json"
        with copied.open("xb") as stream: stream.write(raw)
        audit={
            "protocol":"C1-001",
            "scope":"PARTIAL_DAC_DEMONSTRATED_NOT_SANDBOXED",
            "kernel":platform.release(),"platform":platform.platform(),
            "evaluator_uid":E_UID,"proposer_uid":P_UID,"other_uid":O_UID,
            "socket_gid":GID,"private_dir_mode":"0700",
            "private_answer_mode":"0600","socket_mode":"0660",
            "linux_private_path_negative":"EACCES_OBSERVED_BY_RESTRICTED_TEST_CLIENT",
            "so_peercred_negative":"DENIED_UID_32004_WITH_SOCKET_GROUP_ACCESS",
            "legal_proposer_positive":"COMPLETE",
            "protocol_injection_negative":"SCHEMA_DENIED",
            "independent_replay":replay,
            "record_sha256":sha,
            "untrusted_telemetry":"NOT_AN_ATTESTATION",
            "network_isolation":"NOT_TESTED",
            "host_root_integrity":"NOT_ESTABLISHED",
            "user_code_sandbox":"NOT_TESTED",
        }
        audit_path=output/"c1001-os-control-report.json"
        with audit_path.open("xb") as stream:
            stream.write((json.dumps(audit,indent=2,sort_keys=True)+"\n").encode())
        print("RECEIPT:",copied)
        print("RECEIPT_SHA256:",sha)
        print("AUDIT:",audit_path)
        print("OBSERVED:",json.dumps({
            "private_file":"EACCES","unauthorized_socket":"DENIED",
            "honest_completion":True,"replay":"CONSISTENT",
            "scope":audit["scope"],
        },sort_keys=True))
        return 0
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate(timeout=4)
        # Only remove the disposable OS test, never historical repository data.
        shutil.rmtree(parent)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,required=True)
    p.add_argument("--run-linux-dac",action="store_true")
    args=p.parse_args(argv)
    if not args.run_linux_dac:
        p.error("REFUSE: explicit --run-linux-dac required")
    try:
        return execute(args.output_dir)
    except (OSError,RuntimeError,AssertionError,ValueError,
            subprocess.TimeoutExpired) as exc:
        print("C1_OS_VALIDATION_FAILED:",type(exc).__name__,str(exc),
              file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())
