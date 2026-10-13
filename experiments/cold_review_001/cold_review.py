#!/usr/bin/env python3
"""COLD-REVIEW-001 runner. Standard library only. See PREREG.md.

Written by Claude (Sonnet 5.5) at Chad Holland's direction. Not reviewed line by line by Chad. Not independent.

  python3 -I cold_review.py --selftest        # scoring logic on canned responses; no network, no key
  python3 -I cold_review.py --dry-run         # builds the 9 requests, prints their sha256; no network, no key
  python3 -I cold_review.py --run [label]     # ONE execution: 9 API calls (default label run1; run 2 uses run2). Owner-authorized only.

Rules baked in: at most 9 calls ever per run; one attempt per call (no retries); the results directory must not
exist (nothing is overwritten); the key is read from the environment only and is never printed or written.
"""
import hashlib, json, os, platform, re, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "run1")
MODEL = os.environ.get("COLD_REVIEW_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = 2000
REPEATS = 3
MAX_CALLS = 9
URL = "https://api.anthropic.com/v1/messages"
CASES = [  # (id, file, role)
    ("A", "A_workflow_prefix_438e6d5.py", "target: pre-fix, known defect"),
    ("B", "B_workflow_fixed_fff4f68_commentstripped.py", "control: fixed, same file"),
    ("C", "C_thermal_policy_fff4f68.py", "control: unrelated file"),
]
# Scoring rule, fixed before the run: a finding is a HIT if its quoted_code, with whitespace collapsed,
# contains a call to execute whose only argument is a bare name `action`.
HIT_RE = re.compile(r"execute\(\s*action\s*\)")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(path):
    with open(path, "rb") as fh:
        return fh.read()


def build_request(case_file):
    prompt = read(os.path.join(HERE, "prompt.txt")).decode("utf-8")
    code = read(os.path.join(HERE, "inputs", case_file)).decode("utf-8")
    body = {"model": MODEL, "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt + "\n\n===FILE===\n" + code + "\n===END FILE==="}]}
    return json.dumps(body, sort_keys=True).encode("utf-8")


def parse_findings(text):
    """Return (status, findings). status is OK or PARSE_FAIL. A parse failure is never a 'no finding'."""
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", s).strip()
    try:
        obj = json.loads(s)
        f = obj["findings"]
        if not isinstance(f, list):
            return "PARSE_FAIL", []
        return "OK", [x for x in f if isinstance(x, dict)]
    except Exception:
        return "PARSE_FAIL", []


def score(text):
    """Return ('HIT'|'NO_HIT'|'PARSE_FAIL', n_findings)."""
    status, findings = parse_findings(text)
    if status != "OK":
        return "PARSE_FAIL", 0
    for f in findings:
        q = " ".join(str(f.get("quoted_code", "")).split())
        if HIT_RE.search(q):
            return "HIT", len(findings)
    return "NO_HIT", len(findings)


def key_ok(key):
    """Amendment 1: an API key has a known shape. Non-empty is not enough (run 1 sent a pasted command as the key)."""
    return key.startswith("sk-ant-") and len(key) >= 40 and key == key.strip() and not any(c.isspace() for c in key)


def overall(rows):
    """Amendment 1: separate 'the instrument said no' from 'the instrument never ran'."""
    ok = sum(1 for r in rows if r["http"] == 200)
    if ok == 0:
        return "INCONCLUSIVE"
    if ok < len(rows):
        return "PARTIAL"
    return "EVALUATED"


def selftest():
    hit = json.dumps({"findings": [{"title": "t", "severity": "high",
                                    "quoted_code": "execution_result = self.executor.execute(action)", "explanation": "x"}]})
    fixed = json.dumps({"findings": [{"title": "t", "severity": "low",
                                      "quoted_code": "self.executor.execute(decided_action)", "explanation": "x"}]})
    empty = json.dumps({"findings": []})
    fenced = "```json\n" + hit + "\n```"
    cases = [  # text, expected
        (hit, ("HIT", 1)), (fenced, ("HIT", 1)), (fixed, ("NO_HIT", 1)), (empty, ("NO_HIT", 0)),
        ("I found no problems.", ("PARSE_FAIL", 0)), ('{"findings": "none"}', ("PARSE_FAIL", 0)),
        (json.dumps({"findings": [{"quoted_code": "execute(  action )"}]}), ("HIT", 1)),
        (json.dumps({"findings": [{"quoted_code": "# after execute(), so"}]}), ("NO_HIT", 1)),
    ]
    bad = 0
    for text, want in cases:
        got = score(text)
        ok = got == want
        bad += not ok
        print(("ok  " if ok else "BAD ") + f"want {want} got {got}")
    # anti-vacuity: the scorer must be able to say NO_HIT and must not call a parse failure a miss
    assert score(empty)[0] == "NO_HIT" and score("not json")[0] == "PARSE_FAIL"
    # the three real inputs: only A contains the target pattern, so only A can ever be a true hit
    for cid, f, _ in CASES:
        code = " ".join(read(os.path.join(HERE, "inputs", f)).decode("utf-8").split())
        present = bool(HIT_RE.search(code))
        want = cid == "A"
        bad += present != want
        print(("ok  " if present == want else "BAD ") + f"input {cid}: pattern present in file = {present} (expected {want})")
    keys = [("echo; [ -n \"$ANTHROPIC_API_KEY\" ] && echo \"key set, ${#ANTHROPIC_API_KEY} chars\"", False),
            ("", False), ("sk-ant-api03-" + "x" * 90, True), ("sk-ant-api03-" + "x" * 90 + "\n", False),
            ("sk-ant-short", False), ("sk-ant-" + "x" * 20 + " " + "y" * 20, False)]
    for k, want in keys:
        ok = key_ok(k) == want
        bad += not ok
        print(("ok  " if ok else "BAD ") + f"key_ok shape check -> {key_ok(k)} (expected {want})")
    rows = lambda *h: [{"http": x} for x in h]
    for r, want in [(rows(401, 401, 401), "INCONCLUSIVE"), (rows(200, 401), "PARTIAL"), (rows(200, 200), "EVALUATED")]:
        ok = overall(r) == want
        bad += not ok
        print(("ok  " if ok else "BAD ") + f"overall({[x['http'] for x in r]}) = {overall(r)} (expected {want})")
    print("SELFTEST", "PASS" if bad == 0 else f"FAIL ({bad})")
    return 0 if bad == 0 else 1


def dry_run():
    n = 0
    print(f"model {MODEL}  max_tokens {MAX_TOKENS}  repeats {REPEATS}  calls {len(CASES) * REPEATS} (cap {MAX_CALLS})")
    print("prompt.txt sha256", sha(read(os.path.join(HERE, "prompt.txt"))))
    for cid, f, role in CASES:
        b = build_request(f)
        n += REPEATS
        print(f"{cid}  {role}\n   request bytes {len(b)}  ~{len(b) // 4} input tokens (rough)  sha256 {sha(b)}")
    assert n <= MAX_CALLS
    print("DRY RUN: nothing was sent.")
    return 0


def call(key, body):
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read(), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read(), time.time() - t0
    except Exception as e:  # no retry: a retry would spend credits the registration did not count
        return 0, repr(e).encode(), time.time() - t0


def run(label="run1"):
    global OUT
    OUT = os.path.join(HERE, "results", label)
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("REFUSED: ANTHROPIC_API_KEY is not set")
        return 2
    if not key_ok(key):
        print(f"REFUSED: the value does not look like an API key (length {len(key)}); nothing was sent. "
              "It should start with sk-ant- with no spaces or line breaks.")
        return 2
    if os.path.exists(OUT):
        print(f"REFUSED: {OUT} exists; every run's evidence is kept")
        return 3
    os.makedirs(os.path.join(OUT, "raw"))
    log, rows, calls = [], [], 0
    meta = {"python": platform.python_version(), "platform": platform.platform(), "model_requested": MODEL,
            "script_sha256": sha(read(os.path.abspath(__file__))), "prompt_sha256": sha(read(os.path.join(HERE, "prompt.txt"))),
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for cid, f, role in CASES:
        body = build_request(f)
        for rep in range(1, REPEATS + 1):
            assert calls < MAX_CALLS
            calls += 1
            status, raw, secs = call(key, body)
            name = f"{cid}_{rep}.json"
            with open(os.path.join(OUT, "raw", name), "wb") as fh:
                fh.write(raw)
            text, usage, model_ret = "", {}, ""
            if status == 200:
                try:
                    j = json.loads(raw)
                    text = "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
                    usage, model_ret = j.get("usage", {}), j.get("model", "")
                except Exception:
                    pass
            verdict, nf = score(text) if status == 200 else ("CALL_FAILED", 0)
            rows.append({"case": cid, "rep": rep, "http": status, "verdict": verdict, "n_findings": nf, "usage": usage,
                         "model_returned": model_ret, "seconds": round(secs, 1), "request_sha256": sha(body), "raw": name})
            line = f"{cid}#{rep} http {status} {verdict} findings {nf} usage {usage}"
            print(line)
            log.append(line)
    by = {c: [r["verdict"] for r in rows if r["case"] == c] for c, _, _ in CASES}
    p = {"P1": by["A"].count("HIT") >= 2, "P2": by["B"].count("HIT") == 0 and "CALL_FAILED" not in by["B"],
         "P3": by["C"].count("HIT") == 0 and "CALL_FAILED" not in by["C"],
         "P4": sum(r["verdict"] in ("HIT", "NO_HIT") for r in rows) >= 8}
    summary = {"meta": meta, "rows": rows, "by_case": by, "predictions": p}
    state = overall(rows)
    summary["overall"] = state
    if state == "INCONCLUSIVE":
        out = "VERDICT INCONCLUSIVE: no call reached the model; the predictions below are NOT EVALUABLE. " + "  ".join(f"{k} n/a" for k in p)
    else:
        out = f"VERDICT ({state}) " + "  ".join(f"{k} {'PASS' if v else 'FAIL'}" for k, v in p.items())
    print(out)
    log.append(out)
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    with open(os.path.join(OUT, "run.log"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\n")
    sums = []
    for base, _, files in sorted(os.walk(OUT)):
        for fn in sorted(files):
            if fn != "SHA256SUMS":
                pth = os.path.join(base, fn)
                sums.append(f"{sha(read(pth))}  {os.path.relpath(pth, OUT)}")
    with open(os.path.join(OUT, "SHA256SUMS"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sums) + "\n")
    print("evidence:", OUT)
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]:
        sys.exit(selftest())
    if a == ["--dry-run"]:
        sys.exit(dry_run())
    if a and a[0] == "--run" and len(a) <= 2:
        sys.exit(run(a[1] if len(a) == 2 else "run1"))
    print(__doc__)
    sys.exit(1)
