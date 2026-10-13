#!/usr/bin/env python3
"""Mutation check on the runner itself: each mutant must make `selftest` fail. Run: python3 -I mutants.py"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "cold_review2.py"), encoding="utf-8").read()
M = [("scorer flags everything", "    lt = norm(line_text)\n    uniq", "    return True\n    lt = norm(line_text)\n    uniq"),
     ("win/reversed swapped", '(True, False): "win", (False, True): "reversed"', '(True, False): "reversed", (False, True): "win"'),
     ("truncation treated as OK", 'if msg.get("stop_reason") == "max_tokens":', 'if False:'),
     ("budget cap removed", "if spent + pend + cum + w > cap_total or cum + w > cap_batch:", "if False:"),
     ("uncollected-batch gate removed", 'if any(not b.get("collected") for b in L["batches"]):', "if False:"),
     ("resubmission allowed", "pool = [t for t in ts if t[\"id\"] not in done and", "pool = [t for t in ts if"),
     ("parse failure counted as clean", 'except Exception:\n        return "PARSE_FAIL", []\n\n\ndef flags_site', 'except Exception:\n        return "OK", []\n\n\ndef flags_site')]
bad = 0
for name, a, b in M:
    if src.count(a) != 1:
        print(f"MUTANT NOT APPLICABLE ({src.count(a)} matches): {name}"); bad += 1; continue
    p = os.path.join(HERE, "_mut.py")
    open(p, "w", encoding="utf-8").write(src.replace(a, b))
    r = subprocess.run([sys.executable, "-I", p, "selftest"], capture_output=True, text=True)
    os.remove(p)
    killed = r.returncode != 0
    bad += not killed
    print(("KILLED   " if killed else "SURVIVED ") + name)
print("MUTANTS", "ALL KILLED" if bad == 0 else f"PROBLEM ({bad})")
sys.exit(1 if bad else 0)
