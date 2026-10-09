"""ITC-H1 (coordination/claude/ITC001_HEADROOM_PREREG.md, commit 1deba74): headroom for ITC-001 H2.
Reads the archived ITC-001 evidence only; trains nothing. Usage: python3 -I itc001_headroom.py EVIDENCE.json"""
import json, sys, hashlib
import numpy as np

raw = open(sys.argv[1], "rb").read()
print("evidence sha256", hashlib.sha256(raw).hexdigest())
d = json.loads(raw)

def macro(correct, tasks):
    return float(np.mean([correct[tasks == t].mean() for t in range(6)]))

def alloc(ok, budget, want_correct):
    """ok: (n, 5) bool correctness at depth 1..5. Choose a depth per instance, total <= budget, maximising
    (want_correct) or minimising (not want_correct) the number correct. Returns per-instance correctness."""
    n = ok.shape[0]
    target = ok if want_correct else ~ok
    base = target[:, 0].copy()                      # depth 1 for everyone, cost n
    extra = []
    for i in np.where(~base)[0]:
        hits = np.where(target[i])[0]
        if hits.size:
            extra.append((int(hits[0]), i))         # extra cost = depth_index (depth-1)
    extra.sort()
    left = budget - n
    for cost, i in extra:
        if cost <= left:
            base[i] = True
            left -= cost
    return base if want_correct else ~base

rows = []
d0 = True
for s in d["seed_records"]:
    P = np.asarray(s["probabilities_by_depth"], dtype=float)      # (5, n)
    y = np.asarray(s["test_targets"]).astype(bool)
    t = np.asarray(s["test_task_ids"])
    sel = np.asarray(s["selected_depths"])
    ok = ((P >= 0.5) == y).T                                       # (n, 5)
    pr = s["policy_results"]
    for depth, name in ((1, "fixed1"), (2, "fixed2"), (3, "fixed3"), (5, "fixed5")):
        if abs(macro(ok[:, depth - 1], t) - pr[name]["macro_accuracy"]) > 1e-12:
            d0 = False
    orc, anti = np.zeros(len(y), bool), np.zeros(len(y), bool)
    for task in range(6):
        m = t == task
        budget = int(sel[m].sum())
        orc[m] = alloc(ok[m], budget, True)
        anti[m] = alloc(ok[m], budget, False)
    rows.append(dict(seed=s["seed"], oracle=macro(orc, t), anti=macro(anti, t),
                     shuffle=pr["shuffle_task"]["macro_accuracy"], adaptive=pr["adaptive"]["macro_accuracy"],
                     any_depth=float(ok.any(axis=1).mean()), budget_mean=float(sel.mean())))

for r in rows:
    print(f"seed {r['seed']}: oracle {100*r['oracle']:.4f}  shuffle {100*r['shuffle']:.4f}  adaptive {100*r['adaptive']:.4f}"
          f"  anti {100*r['anti']:.4f}  any-depth {100*r['any_depth']:.4f}  mean passes {r['budget_mean']:.4f}")
mean = lambda k: float(np.mean([r[k] for r in rows]))
g1 = 100 * (mean("oracle") - mean("shuffle"))
g2 = 100 * (mean("anti") - mean("shuffle"))
print(f"\nD0 reconstruction matches archived fixed1/2/3/5 on all seeds: {d0}")
print(f"D1 oracle - shuffle_task (mean, pp): {g1:+.4f}  -> {'HELD' if g1 >= 1.0 else 'NOT HELD'} (registered: >= +1.0)")
print(f"D2 anti-oracle - shuffle_task (mean, pp): {g2:+.4f}  -> {'HELD' if g2 < 0 else 'NOT HELD'} (registered: < 0)")
print(f"D3 share correct at any depth (mean): {100*mean('any_depth'):.4f}%   adaptive - shuffle (archived): {100*(mean('adaptive')-mean('shuffle')):+.4f} pp")
