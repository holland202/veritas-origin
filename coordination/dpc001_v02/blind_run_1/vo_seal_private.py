#!/usr/bin/env python3
"""Owner-local sealing utility. Does not execute a checker or generate tests.
Input files: cases/cases.json, oracle/oracle.json in private workspace.
Output: private sealed manifest and a public-safe commitment summary.
"""
import hashlib, json, os, secrets, stat, sys
from pathlib import Path

ROOT=Path.home()/'.local/share/veritas-origin/dpc001-v02-blind'
TARGET='bc43adf3b51633dfb831ce420afe90ec3ac04ab7'

def fail(msg): raise SystemExit('HALT: '+msg)
def digest(data): return hashlib.sha256(data).hexdigest()
def canon(obj): return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')
def private_file(path):
    if path.is_symlink() or not path.is_file(): fail('missing or symlinked private file: '+str(path))
    if stat.S_IMODE(path.stat().st_mode)&0o077: fail('insecure file permissions: '+str(path))
    return path.read_bytes()
def main():
    os.umask(0o077)
    if ROOT.is_symlink() or not ROOT.is_dir() or stat.S_IMODE(ROOT.stat().st_mode)!=0o700: fail('private root must be non-symlink directory mode 0700')
    case_bytes=private_file(ROOT/'cases/cases.json')
    oracle_bytes=private_file(ROOT/'oracle/oracle.json')
    try: cases=json.loads(case_bytes,parse_constant=lambda x: fail('nonfinite value '+x)); oracle=json.loads(oracle_bytes,parse_constant=lambda x: fail('nonfinite value '+x))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc: fail('invalid JSON: '+str(exc))
    if not isinstance(cases,list) or len(cases)!=24: fail('cases must be a list of exactly 24 contracts')
    if not isinstance(oracle,list) or len(oracle)!=24: fail('oracle must be a list of exactly 24 expected results')
    ids=[f'T{i:02d}' for i in range(1,25)]
    if any(not isinstance(x,dict) or x.get('case_id')!=ids[i] or not isinstance(x.get('contract'),dict) for i,x in enumerate(cases)): fail('case records must be ordered T01..T24 with contract objects')
    if any(not isinstance(x,dict) or x.get('case_id')!=ids[i] or not isinstance(x.get('primary'),str) for i,x in enumerate(oracle)): fail('oracle records must be ordered T01..T24 with primary strings')
    sealed=ROOT/'evidence/sealed_manifest.json'
    public=ROOT/'evidence/public_commitment.json'
    if sealed.exists() or public.exists(): fail('sealed commitment already exists, refusing overwrite')
    # Random nonce protects against straightforward hash matching on guessable small candidate sets.
    nonce=secrets.token_hex(32)
    c_hash=digest(canon({'nonce':nonce,'cases':cases}))
    o_hash=digest(canon({'nonce':nonce,'oracle':oracle}))
    manifest={'version':1,'frozen_commit':TARGET,'case_count':24,'nonce':nonce,'cases_sha256':c_hash,'oracle_sha256':o_hash,'cases_file_sha256':digest(case_bytes),'oracle_file_sha256':digest(oracle_bytes)}
    public_data={'version':1,'frozen_commit':TARGET,'case_count':24,'cases_sha256':c_hash,'oracle_sha256':o_hash,'status':'COMMITTED_NOT_RUN','warning':'Nonce withheld until after execution; this is a commitment, not validation.'}
    for path,obj in ((sealed,manifest),(public,public_data)):
        with path.open('x',encoding='utf-8') as f: json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
        path.chmod(0o600)
    print('SEALED: 24 cases + oracle commitments created. NOT RUN.')
    print('Public-safe JSON path:',public)
    print('Do not publish sealed_manifest.json, cases.json or oracle.json.')
if __name__=='__main__': main()
