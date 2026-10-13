#!/usr/bin/env python3
"""COLD-REVIEW-002 corpus builder. Standard library only. Deterministic: same source + same seed => same corpus.

Written by Claude (Sonnet 5.5) at Chad Holland's direction. Not reviewed line by line by Chad. Not independent.

Reads the sovereign-veritas kernel at a pinned commit (read from a local checkout), and for each eligible file builds
two versions: CLEAN (the file as it is) and DEFECT (the same file with exactly one single-token mutation inside a
function body). The mutation site is chosen by a seeded RNG, never by hand. The corpus order is also seeded.

  python3 -I corpus.py --src <path to sovereign-veritas checkout at the pinned commit> --out corpus
"""
import ast, hashlib, io, json, os, random, subprocess, sys, tokenize

SEED = 20261013          # fixed before any corpus was generated; no re-rolls
PINNED = "fff4f68f5a775212de344af6afc9d1f099e71457"
MIN_BYTES, MAX_BYTES = 1200, 13000

FLIP = {"==": "!=", "!=": "==", "<": "<=", ">": ">=", "<=": "<", ">=": ">"}


def function_lines(tree):
    spans = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.append((n.lineno, n.end_lineno))
    return spans


def sites(src):
    """Return candidate single-token mutations as (line, col, old, new, operator). Only inside function bodies."""
    tree = ast.parse(src)
    spans = function_lines(tree)
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    out = []
    for i, t in enumerate(toks):
        (row, col), s, kind = t.start, t.string, t.type
        if not any(a < row <= b for a, b in spans):
            continue
        prev = toks[i - 1].string if i else ""
        nxt = toks[i + 1].string if i + 1 < len(toks) else ""
        if kind == tokenize.OP and s in FLIP:
            out.append((row, col, s, FLIP[s], "compare_flip"))
        elif kind == tokenize.NAME and s in ("and", "or"):
            out.append((row, col, s, "or" if s == "and" else "and", "bool_swap"))
        elif kind == tokenize.NAME and s == "not" and prev != "is" and nxt != "in":
            out.append((row, col, "not ", "", "drop_not"))
        elif kind == tokenize.NAME and s in ("True", "False") and prev == "return":
            out.append((row, col, s, "False" if s == "True" else "True", "return_flip"))
    return out


def apply(src, site):
    row, col, old, new, _ = site
    lines = src.split("\n")
    line = lines[row - 1]
    assert line[col:col + len(old)] == old, "site does not match the source text"
    lines[row - 1] = line[:col] + new + line[col + len(old):]
    return "\n".join(lines)


def diff_lines(a, b):
    la, lb = a.split("\n"), b.split("\n")
    if len(la) != len(lb):
        return None
    return [i + 1 for i, (x, y) in enumerate(zip(la, lb)) if x != y]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build(src_dir, out_dir):
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=src_dir, capture_output=True, text=True).stdout.strip()
    if head != PINNED:
        raise SystemExit(f"source checkout is at {head}, expected pinned {PINNED}")
    kdir = os.path.join(src_dir, "sovereign_veritas")
    names = sorted(f for f in os.listdir(kdir) if f.endswith(".py") and f not in ("__init__.py",))
    eligible = []
    for f in names:
        with open(os.path.join(kdir, f), "rb") as fh:
            raw = fh.read()
        if not (MIN_BYTES <= len(raw) <= MAX_BYTES):
            continue
        text = raw.decode("utf-8")
        if not text.endswith("\n"):
            continue
        ss = sites(text)
        if ss:
            eligible.append((f, text, ss))
    rng = random.Random(SEED)
    rng.shuffle(eligible)
    os.makedirs(os.path.join(out_dir, "files"), exist_ok=True)
    bases = []
    for f, text, ss in eligible:
        r = random.Random(f"{SEED}:{f}")
        site = r.choice(ss)
        mutated = apply(text, site)
        compile(mutated, f, "exec")  # must still be valid Python
        dl = diff_lines(text, mutated)
        assert dl == [site[0]], (f, dl, site)
        slug = f[:-3]
        for role, body in (("C", text), ("D", mutated)):
            with open(os.path.join(out_dir, "files", f"{slug}__{role}.py"), "w", encoding="utf-8", newline="") as fh:
                fh.write(body)
        orig_line = text.split("\n")[site[0] - 1]
        mut_line = mutated.split("\n")[site[0] - 1]
        bases.append({"id": slug, "kind": "mutation", "operator": site[4], "line_defect": site[0], "line_clean": site[0],
                      "defect_line_text": mut_line, "clean_line_text": orig_line,
                      "sha256_clean": sha(text.encode()), "sha256_defect": sha(mutated.encode())})
    return {"seed": SEED, "pinned_commit": PINNED, "n_mutation_bases": len(bases), "bases": bases}


def add_sv_attack(man, inputs_dir, out_dir):
    """The known public SV-ATTACK-001 pair from COLD-REVIEW-001, as base 0. Not a seeded mutation: a real defect."""
    a = open(os.path.join(inputs_dir, "A_workflow_prefix_438e6d5.py"), encoding="utf-8").read()
    b = open(os.path.join(inputs_dir, "B_workflow_fixed_fff4f68_commentstripped.py"), encoding="utf-8").read()
    for role, body in (("D", a), ("C", b)):
        with open(os.path.join(out_dir, "files", f"sv_attack_001__{role}.py"), "w", encoding="utf-8", newline="") as fh:
            fh.write(body)
    al, bl = a.split("\n"), b.split("\n")
    li = next(i for i, x in enumerate(al, 1) if "self.executor.execute(action)" in x)
    lc = next(i for i, x in enumerate(bl, 1) if "self.executor.execute(decided_action)" in x)
    man["bases"].insert(0, {"id": "sv_attack_001", "kind": "known_public_defect", "operator": "real_defect",
                            "line_defect": li, "line_clean": lc, "defect_line_text": al[li - 1],
                            "clean_line_text": bl[lc - 1], "sha256_clean": sha(b.encode()), "sha256_defect": sha(a.encode())})
    return man


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "--src" and a[2] == "--out":
        here = os.path.dirname(os.path.abspath(__file__))
        man = build(a[1], a[3])
        man = add_sv_attack(man, os.path.join(here, "..", "cold_review_001", "inputs"), a[3])
        man["n_bases"] = len(man["bases"])
        with open(os.path.join(a[3], "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=1, sort_keys=True)
        print("bases", man["n_bases"], "(1 known + %d seeded mutations)" % man["n_mutation_bases"])
        for b in man["bases"]:
            print(f"  {b['id']:28s} {b['operator']:13s} line {b['line_defect']:4d}  {b['defect_line_text'].strip()[:70]}")
    else:
        print(__doc__)
        sys.exit(1)
