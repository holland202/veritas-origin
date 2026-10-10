#!/usr/bin/env python3
"""Owner-run, one-shot DPC-001 v0.2 verifier. Public self-tests use synthetic records only.
Never prints private contracts, oracle payloads or nonce.
"""
import argparse, datetime, hashlib, json, os, pathlib, subprocess, sys, traceback

ROOT=pathlib.Path.home()/'.local/share/veritas-origin/dpc001-v02-blind'
REPO=pathlib.Path.home()/'veritas-origin'
REV='bc43adf3b51633dfb831ce420afe90ec3ac04ab7'
PREFIX='coordination/dpc001_v02/'
HASHES={'checker.py':'f2746a43e1e7360f645be912e552a84e53eca950d07d93d98adbc4d087eeca34',
'SPEC_V02_DRAFT.md':'fce85463ebbb552b0bf44a4a9bb90d5851101b378d31f91a6bb7786405737186'}

def sha(b): return hashlib.sha256(b).hexdigest()
def canon(o): return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def no_constants(s): raise ValueError('forbidden JSON constant: '+s)
def read_json(b): return json.loads(b.decode('utf-8'),parse_constant=no_constants)
def fail(s): raise RuntimeError(s)
def git_bytes(name):
    cp=subprocess.run(['git','-C',str(REPO),'show',f'{REV}:{PREFIX}{name}'],capture_output=True)
    if cp.returncode: fail('cannot retrieve frozen '+name)
    if sha(cp.stdout)!=HASHES[name]: fail('frozen '+name+' SHA mismatch')
    return cp.stdout

def compare(expected, actual):
    if not isinstance(actual,dict):return False,['OUTPUT_NOT_OBJECT']
    problems=[]
    if actual.get('primary')!=expected.get('primary'):problems.append('PRIMARY_MISMATCH')
    must=expected.get('reason_codes',[])
    if not isinstance(must,list) or not all(isinstance(x,str) for x in must):fail('bad expected reasons')
    if not isinstance(actual.get('reason_codes'),list):problems.append('INVALID_REASONS')
    elif any(x not in actual['reason_codes'] for x in must):problems.append('REASON_MISMATCH')
    if actual.get('replay_status')!='NOT_RUN':problems.append('REPLAY_STATUS_INVALID')
    if not isinstance(actual.get('gates'),dict):problems.append('GATES_INVALID')
    if not isinstance(actual.get('limitations'),list):problems.append('LIMITATIONS_INVALID')
    return not problems,problems

def selftest():
    expected={'primary':'READY_FOR_COMPARISON','reason_codes':['SYNTHETIC'],'case_id':'SYNTHETIC'}
    correct={'primary':'READY_FOR_COMPARISON','reason_codes':['SYNTHETIC'],'replay_status':'NOT_RUN','gates':{},'limitations':[]}
    broken=dict(correct,primary='CONTRACT_INVALID')
    wrong=dict(expected,primary='STRUCTURAL_TEST')
    checks={'correct accepted':compare(expected,correct)[0],
    'broken classifier rejected':not compare(expected,broken)[0],
    'wrong oracle rejected':not compare(wrong,correct)[0],
    'missing reason rejected':not compare(dict(expected,reason_codes=['MISSING']),correct)[0],
    'wrong replay status rejected':not compare(expected,dict(correct,replay_status='PASS'))[0],
    'invalid shape rejected':not compare(expected,[])[0]}
    for k,v in checks.items():print(('PASS' if v else 'FAIL')+': '+k)
    print('HARNESS_SELF_TEST:', 'PASS' if all(checks.values()) else 'FAIL')
    return all(checks.values())

def safe_read(p):
    if p.is_symlink() or not p.is_file() or (p.stat().st_mode&0o077):fail('missing/insecure private file')
    return p.read_bytes()

def run(authorized):
    if authorized!='I_AUTHORIZE_ONE_BLIND_RUN':fail('explicit run authorization flag missing')
    if not selftest():fail('harness self-test failed')
    os.umask(0o077)
    ev=ROOT/'evidence'; target=ev/'blind_run_v1.json'
    # Exclusive creation is a durable one-run latch. Retain even on failure/interruption.
    fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    os.close(fd)
    result={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'frozen_commit':REV,'runner_sha256':sha(pathlib.Path(__file__).read_bytes()),
    'status':'INCOMPLETE','cases':[],'checks':{},'errors':[]}
    try:
        c=git_bytes('checker.py');git_bytes('SPEC_V02_DRAFT.md')
        pub=read_json(safe_read(ev/'public_commitment.json'))
        sealed=read_json(safe_read(ev/'sealed_manifest.json'))
        case_bytes=safe_read(ROOT/'cases/cases.json');oracle_bytes=safe_read(ROOT/'oracle/oracle.json')
        cases=read_json(case_bytes);oracle=read_json(oracle_bytes)
        if not all(isinstance(x,list) and len(x)==24 for x in (cases,oracle)):fail('24-case invariant failed')
        if pub.get('frozen_commit')!=REV or sealed.get('frozen_commit')!=REV:fail('revision mismatch')
        if pub.get('case_count')!=24 or sealed.get('case_count')!=24:fail('count mismatch')
        if sha(case_bytes)!=sealed.get('cases_file_sha256') or sha(oracle_bytes)!=sealed.get('oracle_file_sha256'):fail('raw file digest mismatch')
        for k,data in [('cases',cases),('oracle',oracle)]:
            digest=sha(canon({'nonce':sealed['nonce'],k:data}))
            if digest!=sealed.get(k+'_sha256') or digest!=pub.get(k+'_sha256'):fail('sealed '+k+' digest mismatch')
        ids=[f'T{i:02d}' for i in range(1,25)]
        for i,cse in enumerate(cases):
            if not isinstance(cse,dict) or cse.get('case_id')!=ids[i] or not isinstance(cse.get('contract'),dict):fail('case order/schema mismatch')
        for i,o in enumerate(oracle):
            if not isinstance(o,dict) or o.get('case_id')!=ids[i] or not isinstance(o.get('primary'),str):fail('oracle order/schema mismatch')
        scope={'__name__':'frozen_checker'}
        exec(compile(c.decode('utf-8'),str(REPO)+'/'+PREFIX+'checker.py','exec'),scope)
        classify=scope['classify'];result['checks']={'frozen_hashes':'PASS','sealed_commitments':'PASS','harness_controls':'PASS'}
        for i in range(24):
            cid=ids[i]
            try:
                actual=classify(cases[i]['contract'])
                ok,issues=compare(oracle[i],actual)
                result['cases'].append({'case_id':cid,'expected_primary':oracle[i]['primary'],'actual_primary':actual.get('primary') if isinstance(actual,dict) else None,'status':'PASS' if ok else 'FAIL','issues':issues})
            except Exception as exc:
                result['cases'].append({'case_id':cid,'status':'FAIL','issues':['CHECKER_EXCEPTION'],'exception_type':type(exc).__name__})
        result['status']='PASS' if all(r['status']=='PASS' for r in result['cases']) else 'FAIL'
    except BaseException as exc:
        result['errors'].append(type(exc).__name__+': '+str(exc))
        result['status']='INCOMPLETE'
    finally:
        # Always preserve terminal result; no retry under same version.
        with target.open('w',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n');f.flush();os.fsync(f.fileno())
        print('BLIND_RUN_STATUS:',result['status'])
        print('COMPLETED_CASES:',len(result['cases']))
        print('EVIDENCE_PATH:',target)
        for line in result['cases']:print(line['case_id'],line['status'],line.get('expected_primary','?'),line.get('actual_primary','?'),','.join(line['issues']))
        if result['errors']:print('ERROR_TYPES:',','.join(x.split(':')[0] for x in result['errors']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--authorization');a=p.parse_args()
    try:
        if a.self_test and not a.run:sys.exit(0 if selftest() else 2)
        if a.run and not a.self_test:run(a.authorization)
        else:p.error('choose exactly one mode')
    except Exception as exc:
        print('HALT:',type(exc).__name__,str(exc),file=sys.stderr);sys.exit(2)
