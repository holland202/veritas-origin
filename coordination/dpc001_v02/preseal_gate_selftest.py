"""Self-test for preseal_gate.py, built from the published blind_run_1 files (no checker involved).
Each row: (name, mutation, expected gate verdict). Malformed input must give FAIL, never a traceback.
Written by Claude (Opus 5.5), 2026-10-09, after ChatGPT's review (PR #25 note vo/chatgpt/032).
Usage: python3 -I preseal_gate_selftest.py   (run from this directory)
"""
import copy, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "blind_run_1")
cases = json.load(open(os.path.join(B, "cases/cases.json"))); oracle = json.load(open(os.path.join(B, "oracle/oracle.json")))


def mut_cases(f):
    c = copy.deepcopy(cases); f(c); return c, oracle


def mut_oracle(f):
    o = copy.deepcopy(oracle); f(o); return cases, o


ROWS = [
    ("blind_run_1 as sealed (T01/T09 defect)", (cases, oracle), "FAIL"),
    ("T01 with intended invalid schema", mut_cases(lambda c: c[0]["contract"].__setitem__("schema", "dpc-study-v0.1")), "PASS"),
    ("oracle order reversed", (cases, list(reversed(oracle))), "FAIL"),
    ("case_id is a list", mut_cases(lambda c: c[1].__setitem__("case_id", ["T02"])), "FAIL"),
    ("case_id missing", mut_cases(lambda c: c[2].pop("case_id")), "FAIL"),
    ("oracle entry not an object", mut_oracle(lambda o: o.__setitem__(3, "READY_FOR_COMPARISON")), "FAIL"),
    ("oracle case_id is a dict", mut_oracle(lambda o: o[4].__setitem__("case_id", {"id": "T05"})), "FAIL"),
    ("contract not an object", mut_cases(lambda c: c[5].__setitem__("contract", "x")), "FAIL"),
    ("unknown expected label", mut_oracle(lambda o: o[6].__setitem__("primary", "MAYBE")), "FAIL"),
]
ok = 0
with tempfile.TemporaryDirectory() as td:
    for name, (c, o), want in ROWS:
        cp, op = os.path.join(td, "c.json"), os.path.join(td, "o.json")
        json.dump(c, open(cp, "w")); json.dump(o, open(op, "w"))
        r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "preseal_gate.py"), cp, op], capture_output=True, text=True)
        got = "PASS" if "PRESEAL_GATE  PASS" in r.stdout else "FAIL" if "PRESEAL_GATE  FAIL" in r.stdout else "CRASH"
        good = got == want and "Traceback" not in r.stderr
        ok += good
        print(f"{'OK ' if good else 'BAD'}  expected {want:<4} got {got:<5} {name}")
print(f"\nSELFTEST  {ok} of {len(ROWS)} as expected")
sys.exit(0 if ok == len(ROWS) else 1)
