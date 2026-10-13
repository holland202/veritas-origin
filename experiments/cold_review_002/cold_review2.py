#!/usr/bin/env python3
"""COLD-REVIEW-002 runner. Standard library only. See PREREG.md.

Written by Claude (Sonnet 5.5) at Chad Holland's direction. Not reviewed line by line by Chad. Not independent.

  python3 -I cold_review2.py selftest            no network, no key
  python3 -I cold_review2.py plan                no network, no key: tasks, worst-case cost, guaranteed request count
  python3 -I cold_review2.py auto --yes-usd 10   the ONE authorized execution: submit/poll/collect cycles under a hard cap
  python3 -I cold_review2.py status | collect    resume after an interruption (needs key)
  python3 -I cold_review2.py report              offline: scores the saved raw results

Rules baked in: Batch API only; one attempt per request, no retries; a request is never submitted twice; the cap is a
WORST-CASE bound (actual spend of collected batches + max_tokens cost of everything pending + the new batch <= cap);
the key is read from the environment only and never printed or written; raw results are never overwritten.
"""
import hashlib, json, math, os, platform, random, re, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FILES = os.path.join(HERE, "corpus", "files")
MANIFEST = os.path.join(HERE, "corpus", "manifest.json")
API = "https://api.anthropic.com/v1/messages/batches"

MODELS = [("haiku", "claude-haiku-5-5"), ("sonnet", "claude-sonnet-5-5"), ("opus", "claude-opus-5-5"), ("fable", "claude-fable-5-1")]
BATCH_PRICE = {"haiku": (0.05, 0.25), "sonnet": (1.0, 5.0), "opus": (2.0, 10.0), "fable": (5.0, 25.0)}  # USD per MTok, batch
MAX_TOKENS = 8000          # includes thinking tokens on the adaptive-thinking models
CAP_TOTAL = 10.00          # hard worst-case cap, USD
CAP_BATCH = 4.00           # worst-case cap per submitted batch, so actual spend is re-read often
REPS = 2                   # rep 1 is the primary analysis; rep 2 is a top-up if budget remains
PILOT_BASES = 2
BYTES_PER_TOKEN = 2.5      # deliberately pessimistic estimate of input tokens
PROMPT_TOKENS = 600


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    with open(p, "rb") as fh:
        return fh.read()


def norm(s):
    return " ".join(str(s).split())


def load_manifest():
    return json.load(open(MANIFEST, encoding="utf-8"))


def role_file(base, role):
    return os.path.join(FILES, f"{base['id']}__{role}.py")


def numbered(text):
    return "\n".join(f"{i:04d}| {l}" for i, l in enumerate(text.split("\n"), 1))


def build_params(model_id, base, role, prompt):
    code = read(role_file(base, role)).decode("utf-8")
    return {"model": model_id, "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt + "\n\n===FILE===\n" + numbered(code) + "\n===END FILE==="}]}


def params_bytes(p):
    return json.dumps(p, sort_keys=True).encode("utf-8")


def worst_usd(short, params):
    est_in = len(params_bytes(params)) / BYTES_PER_TOKEN + PROMPT_TOKENS
    pin, pout = BATCH_PRICE[short]
    return (est_in * pin + MAX_TOKENS * pout) / 1e6


def usd(short, usage):
    pin, pout = BATCH_PRICE[short]
    return (usage.get("input_tokens", 0) * pin + usage.get("output_tokens", 0) * pout) / 1e6


def tasks(man):
    """Deterministic priority order. Group 'pilot' = first PILOT_BASES bases x all models x C,D rep 1.
    Then base-major rep 1 (every model gets the same bases before any model gets more), then base-major rep 2."""
    bases = [b["id"] for b in man["bases"]]
    out, seen = [], set()

    def add(group, base, rep):
        for short, mid in MODELS:
            for role in ("C", "D"):
                tid = f"{short}-{base}-{role}-{rep}"
                if tid not in seen:
                    seen.add(tid)
                    out.append({"id": tid, "group": group, "model": short, "model_id": mid, "base": base, "role": role, "rep": rep})
    for b in bases[:PILOT_BASES]:
        add("pilot", b, 1)
    for b in bases:
        add("main", b, 1)
    for rep in range(2, REPS + 1):
        for b in bases:
            add("topup", b, rep)
    for t in out:
        assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", t["id"]), t["id"]
    return out


# ---------- scoring (mechanical, fixed before any run) ----------
def parse_message(msg):
    """Return (status, findings). Truncation, bad JSON, wrong shape are never 'no finding'."""
    if msg.get("stop_reason") == "max_tokens":
        return "TRUNCATED", []
    text = "".join(b.get("text", "") for b in msg.get("content", []) if b.get("type") == "text").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text).strip()
    try:
        f = json.loads(text)["findings"]
        if not isinstance(f, list):
            return "PARSE_FAIL", []
        return "OK", [x for x in f if isinstance(x, dict)]
    except Exception:
        return "PARSE_FAIL", []


def flags_site(findings, file_text, line_no, line_text):
    """A finding points at the site if its line number equals the site line, or its quoted code contains the site's
    line text AND that text occurs on exactly one line of the file (so a short generic line cannot match by accident)."""
    lines = file_text.split("\n")
    lt = norm(line_text)
    uniq = lt != "" and sum(1 for l in lines if lt in norm(l)) == 1
    for f in findings:
        try:
            if int(f.get("line")) == line_no:
                return True
        except Exception:
            pass
        if uniq and lt in norm(f.get("quoted_code", "")):
            return True
    return False


def sign_p(w, r):
    n = w + r
    if n == 0:
        return None
    k = min(w, r)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def classify(d_flag, c_flag):
    return {(True, False): "win", (False, True): "reversed", (True, True): "both", (False, False): "neither"}[(d_flag, c_flag)]


# ---------- ledger ----------
def ledger_path():
    return os.path.join(RES, "ledger.json")


def load_ledger():
    if os.path.exists(ledger_path()):
        return json.load(open(ledger_path(), encoding="utf-8"))
    return {"batches": []}


def save_ledger(L):
    os.makedirs(RES, exist_ok=True)
    tmp = ledger_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(L, fh, indent=1, sort_keys=True)
    os.replace(tmp, ledger_path())


def spent_and_pending(L):
    spent = sum(b["actual_usd"] for b in L["batches"] if b.get("collected"))
    pend = sum(b["worst_usd"] for b in L["batches"] if not b.get("collected"))
    return spent, pend


def plan_next(L, ts, params_of, cap_total=CAP_TOTAL, cap_batch=CAP_BATCH, excluded=()):
    """Choose the next batch under the worst-case rule. Returns (list_of_tasks, reason)."""
    if any(not b.get("collected") for b in L["batches"]):
        return [], "a batch is still uncollected; collect it first so its actual spend is known"
    done = {i for b in L["batches"] for i in b["tasks"]}
    spent, pend = spent_and_pending(L)
    pool = [t for t in ts if t["id"] not in done and t["model"] not in excluded]
    if not L["batches"]:
        pool = [t for t in pool if t["group"] == "pilot"]
    chosen, cum = [], 0.0
    for t in pool:
        w = worst_usd(t["model"], params_of(t))
        if spent + pend + cum + w > cap_total or cum + w > cap_batch:
            break
        chosen.append(t)
        cum += w
    if not chosen:
        return [], "no further task fits under the worst-case cap" if pool else "all tasks submitted"
    return chosen, f"{len(chosen)} requests, worst case ${cum:.2f}, spent so far ${spent:.4f}"


def key_ok(key):
    return key.startswith("sk-ant-") and len(key) >= 40 and key == key.strip() and not any(c.isspace() for c in key)


# ---------- transport ----------
class Real:
    def __init__(self, key):
        self.h = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}

    def _do(self, url, data=None):
        req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET", headers=self.h)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:  # no retry
            return 0, repr(e).encode()

    def create(self, requests):
        return self._do(API, json.dumps({"requests": requests}).encode())

    def get(self, bid):
        return self._do(f"{API}/{bid}")

    def results(self, bid):
        return self._do(f"{API}/{bid}/results")


# ---------- actions ----------
def make_requests(chosen, params_of):
    reqs, digests = [], {}
    for t in chosen:
        p = params_of(t)
        reqs.append({"custom_id": t["id"], "params": p})
        digests[t["id"]] = sha(params_bytes(p))
    return reqs, digests


def submit_next(tr, ts, params_of, L, excluded=()):
    chosen, why = plan_next(L, ts, params_of, excluded=excluded)
    if not chosen:
        return None, why
    reqs, dg = make_requests(chosen, params_of)
    st, raw = tr.create(reqs)
    if st != 200:
        return None, f"batch create failed: HTTP {st} {raw[:300]!r} (nothing recorded as submitted)"
    j = json.loads(raw)
    w = sum(worst_usd(t["model"], params_of(t)) for t in chosen)
    L["batches"].append({"batch_id": j["id"], "stage": chosen[0]["group"], "tasks": [t["id"] for t in chosen],
                         "request_sha256": dg, "worst_usd": round(w, 6), "submitted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "collected": False, "actual_usd": None})
    save_ledger(L)
    return j["id"], why


def collect_ready(tr, L, ts_by_id):
    got = 0
    for b in L["batches"]:
        if b.get("collected"):
            continue
        st, raw = tr.get(b["batch_id"])
        if st != 200:
            print(f"  {b['batch_id']}: status HTTP {st}")
            continue
        if json.loads(raw).get("processing_status") != "ended":
            print(f"  {b['batch_id']}: {json.loads(raw).get('processing_status')}")
            continue
        path = os.path.join(RES, "raw", b["batch_id"] + ".jsonl")
        if os.path.exists(path):
            raise SystemExit(f"REFUSED: {path} exists; evidence is never overwritten")
        st, body = tr.results(b["batch_id"])
        if st != 200:
            print(f"  {b['batch_id']}: results HTTP {st}")
            continue
        os.makedirs(os.path.join(RES, "raw"), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(body)
        total = 0.0
        for line in body.decode("utf-8").splitlines():
            r = json.loads(line)
            t = ts_by_id.get(r["custom_id"])
            if r["result"]["type"] == "succeeded" and t:
                total += usd(t["model"], r["result"]["message"].get("usage", {}))
        b["collected"], b["actual_usd"] = True, round(total, 6)
        save_ledger(L)
        got += 1
        print(f"  {b['batch_id']}: collected, actual ${total:.4f}")
    return got


def load_rows(man, ts_by_id, L):
    """Score every collected result. Returns {task_id: row}. Missing results for submitted tasks => row status NO_RESULT."""
    bases = {b["id"]: b for b in man["bases"]}
    rows = {}
    for b in L["batches"]:
        if not b.get("collected"):
            continue
        seen = set()
        for line in open(os.path.join(RES, "raw", b["batch_id"] + ".jsonl"), encoding="utf-8"):
            r = json.loads(line)
            t = ts_by_id[r["custom_id"]]
            seen.add(t["id"])
            res = r["result"]
            row = {"task": t, "status": res["type"].upper(), "n_findings": 0, "flag": None, "usage": {}, "cost": 0.0, "stop": None}
            if res["type"] == "succeeded":
                msg = res["message"]
                st, fs = parse_message(msg)
                row.update(status=st, n_findings=len(fs), usage=msg.get("usage", {}), cost=usd(t["model"], msg.get("usage", {})), stop=msg.get("stop_reason"))
                if st == "OK":
                    base = bases[t["base"]]
                    text = read(role_file(base, t["role"])).decode("utf-8")
                    ln = base["line_defect"] if t["role"] == "D" else base["line_clean"]
                    lt = base["defect_line_text"] if t["role"] == "D" else base["clean_line_text"]
                    row["flag"] = flags_site(fs, text, ln, lt)
            rows[t["id"]] = row
        for tid in b["tasks"]:
            if tid not in seen:
                rows[tid] = {"task": ts_by_id[tid], "status": "NO_RESULT", "n_findings": 0, "flag": None, "usage": {}, "cost": 0.0, "stop": None}
    return rows


def analyse(man, rows):
    bases = {b["id"]: b for b in man["bases"]}
    short_names = [m for m, _ in MODELS]
    pairs = {}  # (model, base, rep) -> class or None
    for (short, _) in MODELS:
        for bid in bases:
            for rep in range(1, REPS + 1):
                c = rows.get(f"{short}-{bid}-C-{rep}")
                d = rows.get(f"{short}-{bid}-D-{rep}")
                if c and d and c["status"] == "OK" and d["status"] == "OK":
                    pairs[(short, bid, rep)] = classify(d["flag"], c["flag"])
    tally = {m: {"win": 0, "reversed": 0, "both": 0, "neither": 0} for m in short_names}
    for (m, bid, rep), k in pairs.items():
        if rep == 1:
            tally[m][k] += 1
    n_req = len(rows)
    n_ok = sum(1 for r in rows.values() if r["status"] == "OK")
    common = [bid for bid in bases if all((m, bid, 1) in pairs for m in short_names)]
    seeded = [b for b in common if bases[b]["kind"] == "mutation"]
    wins_common = {m: sum(1 for b in common if pairs[(m, b, 1)] == "win") for m in short_names}
    out = {"n_requests_scored": n_req, "n_ok": n_ok, "tally_rep1_all_available": tally, "common_bases": common, "wins_on_common": wins_common}
    # P1 ordering
    if len(common) >= 8:
        w = wins_common
        out["P1"] = w["fable"] >= w["opus"] >= w["sonnet"] >= w["haiku"]
    else:
        out["P1"] = "NOT_EVALUABLE"
    # P2 best model detects >= 50% of seeded defects
    if len(seeded) >= 8:
        best = max(sum(1 for b in seeded if pairs[(m, b, 1)] == "win") for m in short_names)
        out["P2"] = best / len(seeded) >= 0.5
        out["P2_best_rate"] = round(best / len(seeded), 3)
    else:
        out["P2"] = "NOT_EVALUABLE"
    # P3 control cleanliness: C-site flag rate <= 10% for every model (rep 1, seeded bases with an OK C row)
    rates, ok3 = {}, True
    for m in short_names:
        cs = [rows[f"{m}-{b}-C-1"] for b in bases if bases[b]["kind"] == "mutation" and f"{m}-{b}-C-1" in rows and rows[f"{m}-{b}-C-1"]["status"] == "OK"]
        if len(cs) < 8:
            rates[m] = None
            ok3 = None if ok3 is not False else False
            continue
        rates[m] = round(sum(1 for r in cs if r["flag"]) / len(cs), 3)
        if rates[m] > 0.10:
            ok3 = False
    out["P3"], out["P3_rates"] = ("NOT_EVALUABLE" if ok3 is None else ok3), rates
    # P4 known defect: at least 2 of 4 models win on sv_attack_001
    k = [pairs.get((m, "sv_attack_001", 1)) for m in short_names]
    out["P4"] = ("NOT_EVALUABLE" if sum(x is not None for x in k) < 2 else sum(1 for x in k if x == "win") >= 2)
    out["P4_classes"] = dict(zip(short_names, k))
    # P5 operator effect (pooled over models, rep 1, seeded)
    def rate(ops):
        n = w = 0
        for m in short_names:
            for b in seeded:
                if bases[b]["operator"] in ops:
                    n += 1
                    w += pairs[(m, b, 1)] == "win"
        return (w / n if n else None), n
    rl, nl = rate(("bool_swap", "drop_not"))
    rc, nc = rate(("compare_flip",))
    out["P5_rates"] = {"logic_ops(bool_swap,drop_not)": rl, "compare_flip": rc, "n_logic": nl, "n_compare": nc}
    out["P5"] = "NOT_EVALUABLE" if (nl < 12 or nc < 12) else rl > rc
    # P6 reliability
    out["P6"] = ("NOT_EVALUABLE" if n_req == 0 else n_ok / n_req >= 0.95)
    out["P6_rate"] = round(n_ok / n_req, 4) if n_req else None
    # sign tests per model (descriptive)
    out["sign_tests"] = {m: {"wins": tally[m]["win"], "reversed": tally[m]["reversed"], "p_two_sided": sign_p(tally[m]["win"], tally[m]["reversed"])} for m in short_names}
    # failures by status
    fails = {}
    for r in rows.values():
        if r["status"] != "OK":
            fails.setdefault(r["task"]["model"], {}).setdefault(r["status"], 0)
            fails[r["task"]["model"]][r["status"]] += 1
    out["non_ok_by_model"] = fails
    # rep agreement (descriptive)
    ag = n = 0
    for (m, b, rep), kls in pairs.items():
        if rep == 2 and (m, b, 1) in pairs:
            n += 1
            ag += (pairs[(m, b, 1)] == kls)
    out["rep_agreement"] = {"n": n, "agree": ag}
    out["cost_by_model"] = {m: round(sum(r["cost"] for r in rows.values() if r["task"]["model"] == m), 4) for m in short_names}
    return out


def report():
    man, L = load_manifest(), load_ledger()
    ts_by_id = {t["id"]: t for t in tasks(man)}
    rows = load_rows(man, ts_by_id, L)
    a = analyse(man, rows)
    spent, pend = spent_and_pending(L)
    print("COLD-REVIEW-002 REPORT (failures first)")
    print(f"  requests scored {a['n_requests_scored']}, OK {a['n_ok']}, non-OK by model {a['non_ok_by_model']}")
    print(f"  P6 reliability rate {a['P6_rate']}")
    for m in ("haiku", "sonnet", "opus", "fable"):
        t = a["tally_rep1_all_available"][m]
        print(f"  {m:6s} win {t['win']:2d} reversed {t['reversed']:2d} both {t['both']:2d} neither {t['neither']:2d}  sign-test p {a['sign_tests'][m]['p_two_sided']}  cost ${a['cost_by_model'][m]}")
    print(f"  common bases (all four models, rep 1): {len(a['common_bases'])}  wins on common {a['wins_on_common']}")
    for p in ("P1", "P2", "P3", "P4", "P5", "P6"):
        v = a[p]
        print(f"  {p}: {'PASS' if v is True else 'FAIL' if v is False else v}")
    print(f"  P2 best seeded-win rate {a.get('P2_best_rate')}; P3 C-site flag rates {a['P3_rates']}; P4 {a['P4_classes']}; P5 {a['P5_rates']}")
    print(f"  rep agreement (rep2 vs rep1 pair class) {a['rep_agreement']}")
    print(f"  recorded spend (collected batches, from usage) ${spent:.4f}; uncollected worst case ${pend:.4f}. Check the Console for the true bill.")
    with open(os.path.join(RES, "REPORT.json"), "w", encoding="utf-8") as fh:
        json.dump(a, fh, indent=1, sort_keys=True, default=str)
    return a


# ---------- commands ----------
def params_factory(man):
    prompt = read(os.path.join(HERE, "prompt.txt")).decode("utf-8")
    bases = {b["id"]: b for b in man["bases"]}
    cache = {}

    def f(t):
        if t["id"] not in cache:
            cache[t["id"]] = build_params(t["model_id"], bases[t["base"]], t["role"], prompt)
        return cache[t["id"]]
    return f


def plan():
    man = load_manifest()
    ts = tasks(man)
    pf = params_factory(man)
    print(f"bases {len(man['bases'])}  tasks {len(ts)} (4 models x 2 files x {REPS} reps)  max_tokens {MAX_TOKENS}  cap ${CAP_TOTAL:.2f} worst-case")
    print("prompt sha256", sha(read(os.path.join(HERE, "prompt.txt"))))
    tot = 0.0
    for short, _ in MODELS:
        w = [worst_usd(short, pf(t)) for t in ts if t["model"] == short and t["rep"] == 1]
        tot += sum(w)
        print(f"  {short:6s} rep-1 requests {len(w):3d}  worst case ${sum(w):6.2f}  per request max ${max(w):.4f}")
    print(f"  all rep-1 tasks worst case ${tot:.2f} (cap ${CAP_TOTAL:.2f}); the staged guard decides how far it gets from ACTUAL spend")
    L = {"batches": []}
    ch, why = plan_next(L, ts, pf)
    print("first batch (pilot):", why)
    run = 0.0
    n = 0
    for t in ts:
        w = worst_usd(t["model"], pf(t))
        if run + w > CAP_TOTAL:
            break
        run += w
        n += 1
    print(f"guaranteed minimum requests if every request hit max_tokens: {n}; at most {len(ts)}")
    return 0


def need_key():
    k = os.environ.get("ANTHROPIC_API_KEY", "")
    if not k or not key_ok(k):
        raise SystemExit(f"REFUSED: ANTHROPIC_API_KEY missing or not key-shaped (length {len(k)}). Nothing was sent.")
    return k


def pilot_excluded(man, ts_by_id, L):
    """After the pilot is collected, a model with zero OK pilot results is dropped from the main run (and reported)."""
    pil = [b for b in L["batches"] if b["stage"] == "pilot" and b.get("collected")]
    if not pil:
        return ()
    rows = load_rows(man, ts_by_id, {"batches": pil})
    bad = []
    for short, _ in MODELS:
        rs = [r for r in rows.values() if r["task"]["model"] == short]
        if rs and not any(r["status"] == "OK" for r in rs):
            bad.append(short)
    return tuple(bad)


def auto(args):
    if args[:1] != ["--yes-usd"] or len(args) != 2 or float(args[1]) != CAP_TOTAL:
        raise SystemExit(f"REFUSED: authorization must be exactly `auto --yes-usd {CAP_TOTAL:g}`")
    tr = Real(need_key())
    man = load_manifest()
    ts = tasks(man)
    ts_by_id = {t["id"]: t for t in ts}
    pf = params_factory(man)
    L = load_ledger()
    cycles = 0
    while cycles < 20:
        cycles += 1
        exc = pilot_excluded(man, ts_by_id, L)
        if exc:
            print("  excluded after pilot (no OK result):", exc)
        bid, why = submit_next(tr, ts, pf, L, excluded=exc)
        print(f"cycle {cycles}: submit -> {bid or 'none'} ({why})")
        if bid is None and "uncollected" not in why:
            break
        t0 = time.time()
        while any(not b.get("collected") for b in L["batches"]):
            if time.time() - t0 > 4 * 3600:
                print("timeout waiting; resume later with `status`/`collect`")
                return 4
            time.sleep(30)
            collect_ready(tr, L, ts_by_id)
        if cycles == 1:
            rows = load_rows(man, ts_by_id, L)
            ok = sum(1 for r in rows.values() if r["status"] == "OK")
            print(f"  pilot: {ok}/{len(rows)} OK")
            if ok == 0:
                print("PILOT INCONCLUSIVE: nothing parsed. Stopping; no further money spent.")
                return 5
    report()
    return 0


def status_collect(collect):
    tr = Real(need_key())
    man = load_manifest()
    L = load_ledger()
    ts_by_id = {t["id"]: t for t in tasks(man)}
    if not L["batches"]:
        print("no batches submitted")
        return 0
    collect_ready(tr, L, ts_by_id)
    sp, pe = spent_and_pending(L)
    print(f"spent {sp:.4f}  pending worst {pe:.4f}")
    return 0


# ---------- selftest ----------
def fake_msg(findings, stop="end_turn", text=None, usage=(2000, 300)):
    t = text if text is not None else json.dumps({"findings": findings})
    return {"stop_reason": stop, "content": [{"type": "thinking", "thinking": "x"}, {"type": "text", "text": t}],
            "usage": {"input_tokens": usage[0], "output_tokens": usage[1]}}


class Fake:
    """In-process stand-in for the API. Detector modes: oracle / everything / anti / none / garbage."""
    def __init__(self, man, mode):
        self.man, self.mode, self.sent, self.n = man, mode, [], 0
        self.bases = {b["id"]: b for b in man["bases"]}

    def create(self, requests):
        self.n += 1
        self.sent.append(requests)
        return 200, json.dumps({"id": f"msgbatch_fake{self.n}", "processing_status": "in_progress"}).encode()

    def get(self, bid):
        return 200, json.dumps({"processing_status": "ended"}).encode()

    def results(self, bid):
        reqs = self.sent[int(bid.replace("msgbatch_fake", "")) - 1]
        lines = []
        for r in reqs:
            short, rest = r["custom_id"].split("-", 1)
            base_id, role, rep = rest.rsplit("-", 2)
            b = self.bases[base_id]
            ln = b["line_defect"] if role == "D" else b["line_clean"]
            lt = (b["defect_line_text"] if role == "D" else b["clean_line_text"]).strip()
            if self.mode == "oracle":
                msg = fake_msg([{"line": ln, "quoted_code": lt}] if role == "D" else [])
            elif self.mode == "everything":
                msg = fake_msg([{"line": ln, "quoted_code": lt}])
            elif self.mode == "anti":
                msg = fake_msg([{"line": ln, "quoted_code": lt}] if role == "C" else [])
            elif self.mode == "garbage":
                msg = fake_msg([], text="no bugs here")
            else:
                msg = fake_msg([])
            lines.append(json.dumps({"custom_id": r["custom_id"], "result": {"type": "succeeded", "message": msg}}))
        return 200, "\n".join(lines).encode()


def selftest():
    import shutil, tempfile
    global RES
    bad = 0

    def chk(name, cond):
        nonlocal bad
        bad += not cond
        print(("ok  " if cond else "BAD ") + name)
    man = load_manifest()
    # 1. scorer
    chk("truncated is not 'no finding'", parse_message({"stop_reason": "max_tokens", "content": []})[0] == "TRUNCATED")
    chk("prose is PARSE_FAIL", parse_message(fake_msg([], text="looks fine"))[0] == "PARSE_FAIL")
    chk("empty findings is OK with 0", parse_message(fake_msg([])) == ("OK", []))
    chk("fenced JSON parses", parse_message(fake_msg([], text='```json\n{"findings":[]}\n```'))[0] == "OK")
    src = "a = 1\nif x:\n    y = 2\nif x:\n    z = 3\n"
    chk("line number match", flags_site([{"line": 3}], src, 3, "y = 2"))
    chk("unique quote match without line", flags_site([{"line": 99, "quoted_code": "  y = 2 "}], src, 3, "y = 2"))
    chk("non-unique quote cannot match by text", not flags_site([{"line": 99, "quoted_code": "if x:"}], src, 2, "if x:"))
    chk("wrong line, wrong quote -> no flag", not flags_site([{"line": 1, "quoted_code": "a = 1"}], src, 3, "y = 2"))
    chk("bad line value does not crash", not flags_site([{"line": "abc"}], src, 3, "y = 2"))
    chk("sign test: 8 vs 0 p=0.0078", abs(sign_p(8, 0) - 0.0078125) < 1e-9 and sign_p(0, 0) is None and sign_p(3, 3) == 1.0)
    # 2. corpus integrity
    kinds = 0
    for b in man["bases"]:
        c, d = read(role_file(b, "C")).decode(), read(role_file(b, "D")).decode()
        compile(c, "c", "exec"), compile(d, "d", "exec")
        chk_ok = sha(c.encode()) == b["sha256_clean"] and sha(d.encode()) == b["sha256_defect"] and c != d
        if b["kind"] == "mutation":
            la, lb = c.split("\n"), d.split("\n")
            chk_ok = chk_ok and len(la) == len(lb) and [i + 1 for i, (x, y) in enumerate(zip(la, lb)) if x != y] == [b["line_defect"]]
            kinds += 1
        chk(f"corpus {b['id']}: hashes, compiles, differs as registered", chk_ok)
        dl = d.split("\n")[b["line_defect"] - 1]
        cl = c.split("\n")[b["line_clean"] - 1]
        chk(f"corpus {b['id']}: manifest line texts match files", dl == b["defect_line_text"] and cl == b["clean_line_text"])
    chk("known defect present as base 0", man["bases"][0]["id"] == "sv_attack_001")
    # 3. task list
    ts = tasks(man)
    ids = [t["id"] for t in ts]
    chk(f"task ids unique ({len(ids)})", len(ids) == len(set(ids)) and len(ids) == len(man["bases"]) * 2 * 4 * REPS)
    chk("pilot group is first and small", ts[0]["group"] == "pilot" and sum(t["group"] == "pilot" for t in ts) == PILOT_BASES * 8)
    pf = params_factory(man)
    chk("every request is under 100k estimated input tokens", all(len(params_bytes(pf(t))) / BYTES_PER_TOKEN + PROMPT_TOKENS < 100000 for t in ts))
    # 4. cost guard
    L0 = {"batches": []}
    ch, _ = plan_next(L0, ts, pf)
    chk("first batch is only pilot tasks", ch and all(t["group"] == "pilot" for t in ch))
    chk("batch cap respected", sum(worst_usd(t["model"], pf(t)) for t in ch) <= CAP_BATCH)
    ch2, why = plan_next({"batches": [{"tasks": [], "collected": False, "worst_usd": 1}]}, ts, pf)
    chk("refuses while a batch is uncollected", ch2 == [] and "uncollected" in why)
    done = [t["id"] for t in ts]
    ch3, why = plan_next({"batches": [{"tasks": done[:10], "collected": True, "actual_usd": 9.999, "worst_usd": 9.9}]}, ts, pf)
    chk("refuses when remaining budget is below one request", ch3 == [])
    ch4, _ = plan_next({"batches": [{"tasks": done[:10], "collected": True, "actual_usd": 0.5, "worst_usd": 9.9}]}, ts, pf)
    chk("never re-submits an already submitted task", all(t["id"] not in done[:10] for t in ch4))
    big = sum(worst_usd(t["model"], pf(t)) for t in ts)
    chk(f"full task list worst case (${big:.2f}) exceeds cap, so the guard is not vacuous", big > CAP_TOTAL)
    # 5. end to end with fake transport, per detector
    tmp = tempfile.mkdtemp()
    old = RES
    try:
        for mode, want in (("oracle", "all_win"), ("everything", "no_discord"), ("anti", "all_rev"), ("none", "nothing"), ("garbage", "unparsed")):
            RES = os.path.join(tmp, mode)
            tr = Fake(man, mode)
            L = {"batches": []}
            ts_by_id = {t["id"]: t for t in ts}
            for _ in range(12):
                bid, why = submit_next(tr, ts, pf, L)
                if bid is None:
                    break
                collect_ready(tr, L, ts_by_id)
            rows = load_rows(man, ts_by_id, L)
            a = analyse(man, rows)
            t = a["tally_rep1_all_available"]["fable"]
            ok = {"all_win": t["win"] >= 5 and t["reversed"] == 0 and t["both"] == 0,
                  "no_discord": t["win"] == 0 and t["reversed"] == 0 and t["both"] >= 5,
                  "all_rev": t["reversed"] >= 5 and t["win"] == 0,
                  "nothing": t["neither"] >= 5 and t["win"] == 0 and t["reversed"] == 0,
                  "unparsed": a["n_ok"] == 0 and t["win"] + t["reversed"] + t["both"] + t["neither"] == 0}[want]
            chk(f"fake detector '{mode}' -> {want} (fable tally {t}, ok {a['n_ok']}/{a['n_requests_scored']})", ok)
            spent, pend = spent_and_pending(L)
            chk(f"fake '{mode}': recorded spend + pending <= cap (${spent:.2f})", spent + pend <= CAP_TOTAL)
            chk(f"fake '{mode}': no task submitted twice", len([i for b in L["batches"] for i in b["tasks"]]) == len({i for b in L["batches"] for i in b["tasks"]}))
            if mode == "oracle":
                chk("oracle: P4 passes only because the known defect is won by the detector", a["P4"] is True)
                chk("oracle: sign test is significant", a["sign_tests"]["fable"]["p_two_sided"] is not None and a["sign_tests"]["fable"]["p_two_sided"] < 0.05)
            if mode == "everything":
                chk("flag-everything detector: P3 FAILS (control cleanliness catches it)", a["P3"] is False)
            if mode == "garbage":
                chk("garbage: P6 FAILS, nothing counted as 'no finding'", a["P6"] is False)
            if mode in ("anti", "none"):
                chk(f"{mode}: P2 FAILS (the instrument can say no)", a["P2"] is False or a["P2"] == "NOT_EVALUABLE")
        # refusal to overwrite raw evidence
        RES = os.path.join(tmp, "oracle")
        L = load_ledger()
        L["batches"][0]["collected"] = False
        try:
            collect_ready(Fake(man, "oracle"), L, {t["id"]: t for t in ts})
            chk("refuses to overwrite raw evidence", False)
        except SystemExit:
            chk("refuses to overwrite raw evidence", True)
    finally:
        RES = old
        shutil.rmtree(tmp, ignore_errors=True)
    # 6. key shape
    for k, want in (("", False), ("echo; [ -n x ]", False), ("sk-ant-api03-" + "x" * 90, True), ("sk-ant-short", False), ("sk-ant-" + "x" * 50 + "\n", False)):
        chk(f"key_ok({k[:14]!r}...) == {want}", key_ok(k) == want)
    print("SELFTEST", "PASS" if bad == 0 else f"FAIL ({bad})")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    cmd = a[0] if a else ""
    if cmd == "selftest":
        sys.exit(selftest())
    if cmd == "plan":
        sys.exit(plan())
    if cmd == "auto":
        sys.exit(auto(a[1:]))
    if cmd in ("status", "collect"):
        sys.exit(status_collect(cmd == "collect"))
    if cmd == "report":
        report()
        sys.exit(0)
    print(__doc__)
    sys.exit(1)
