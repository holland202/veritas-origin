"""EBA-001 honest visual summaries after independent evidence replay.

Creates two standalone SVG files, never an image of 'validated' external
security. Entirely stdlib, no network access or third-party libraries.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/"tools/verify_eba001.py"
spec=importlib.util.spec_from_file_location("eba_checker_for_figures",path)
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
COLORS={
    "CLEAN_WITHIN_DECLARED_FIXTURE":"#48cdb0",
    "INVALID_OBSERVED_ORACLE_LEAK":"#ed756f",
    "INVALID_PROPOSER_CONTEXT":"#ed756f",
    "INVALID_EVALUATOR_IDENTITY":"#ed756f",
    "UNOBSERVABLE_ACCESS_PROVENANCE":"#edbb70",
    "NOT_ESTABLISHED_SELF_ATTESTED_INTEGRITY":"#edbb70",
    "EXPLORATORY_ONLY":"#6b95ce",
}


def ent(x):
    return escape(str(x),{'"':"&quot;"})


def scenarios_svg(data):
    cases=data["scenarios"]
    header=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1580" height="1090" viewBox="0 0 1580 1090" role="img" aria-labelledby="title desc">',
        '<title id="title">EBA-001: internally consistent evaluation versus methodological provenance</title>',
        '<desc id="desc">Ten synthetic scenarios all pass a mathematical-consistency baseline, but access-log and context contamination produce different methodological dispositions. E9 falsely appears clean because its self-attested access log is forged.</desc>',
        '<rect width="1580" height="1090" fill="#081a2b"/>',
        '<rect x="23" y="24" width="1534" height="1040" rx="30" fill="#12263c" stroke="#345b77" stroke-width="2"/>',
        '<text x="55" y="87" fill="#eff9ff" font-size="38" font-family="Arial,sans-serif" font-weight="bold">Evaluator boundary: consistency is not clean provenance</text>',
        '<text x="55" y="130" fill="#b8d3e8" font-size="23" font-family="Arial,sans-serif">EXP003-P0 external-policy toy transcripts · registered E0–E9 control scenarios</text>',
        '<text x="55" y="170" fill="#ffc68c" font-size="22" font-family="Arial,sans-serif" font-weight="bold">EXPLORATORY SYNTHETIC / NOT VALIDATED / NO OS ISOLATION</text>',
        '<text x="55" y="221" fill="#d9ebf8" font-size="22" font-family="Arial,sans-serif">Case</text>',
        '<text x="170" y="221" fill="#d9ebf8" font-size="22" font-family="Arial,sans-serif">Original P0 math replay</text>',
        '<text x="670" y="221" fill="#d9ebf8" font-size="22" font-family="Arial,sans-serif">Declared methodological status</text>',
    ]
    for i,row in enumerate(cases):
        y=239+i*74
        state=row["methodology_disposition"]
        color=COLORS.get(state,"#b7bec9")
        if row["id"]=="E9": color="#f4a4d3"
        header += [
            f'<text x="58" y="{y+31}" fill="#f1faff" font-size="26" font-family="monospace">{ent(row["id"])}</text>',
            f'<rect x="171" y="{y+6}" width="433" height="37" rx="11" fill="#225440"/>',
            f'<text x="184" y="{y+32}" fill="#c9ffe9" font-family="Arial,sans-serif" font-size="18">CONSISTENT (specified mathematics)</text>',
            f'<rect x="670" y="{y+6}" width="845" height="37" rx="11" fill="{color}" opacity=".22"/>',
            f'<text x="687" y="{y+32}" fill="{color}" font-size="20" font-family="Arial,sans-serif">{ent(state)}</text>',
        ]
        if row["id"]=="E9":
            header.append(f'<text x="1248" y="{y+32}" font-size="19" fill="#ffe2ee" font-family="Arial,sans-serif">FALSE CLEAN</text>')
    header += [
        '<line x1="55" y1="1004" x2="1520" y2="1004" stroke="#365771"/>',
        '<text x="55" y="1038" font-size="19" fill="#b9cde3" font-family="Arial,sans-serif">E9: a forged self-attested clean access log is not a trustworthy independence proof.</text>',
        '</svg>',
    ]
    return "\n".join(header)+"\n"


def comparisons_svg(data):
    clean=data["outcome_summary"]["honest_probes"]
    impure=data["outcome_summary"]["oracle_informed_probes"]
    out=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1570" height="860" viewBox="0 0 1570 860" role="img" aria-labelledby="title desc">',
        '<title id="title">EBA-001 probe counts on 12 public P0 toy tasks</title>',
        '<desc id="desc">Honest context-only greedy versus synthetic illicit oracle-informed test selection. Results only illustrate a potential evaluation contamination mechanism; no model intelligence or actual attack was tested.</desc>',
        '<rect width="1570" height="860" fill="#08192a"/>',
        '<rect x="24" y="24" width="1522" height="812" rx="27" fill="#12253b" stroke="#3a5670" stroke-width="2"/>',
        '<text x="55" y="88" font-size="39" font-family="Arial,sans-serif" fill="#ecf8ff" font-weight="bold">Would hidden oracle knowledge change probe efficiency?</text>',
        '<text x="55" y="129" font-size="24" font-family="Arial,sans-serif" fill="#b9d5e8">Both policies produce mathematically valid external transcripts, but one violates blinding.</text>',
        '<text x="55" y="169" font-size="21" font-family="Arial,sans-serif" fill="#ffc588" font-weight="bold">EXPLORATORY / PUBLIC 12-SEED TOY / NOT A MODEL OR SECURE SANDBOX</text>',
        '<rect x="280" y="202" width="20" height="20" fill="#50cba8"/>',
        '<text x="310" y="219" font-size="20" font-family="Arial,sans-serif" fill="#eff9ff">Context-only greedy</text>',
        '<rect x="780" y="202" width="20" height="20" fill="#f497a2"/>',
        '<text x="810" y="219" font-size="20" font-family="Arial,sans-serif" fill="#eff9ff">Oracle-informed (inadmissible)</text>',
    ]
    for seed,(g,o) in enumerate(zip(clean,impure)):
        y=243+seed*43
        out += [
            f'<text x="65" y="{y+21}" fill="#edf9ff" font-size="21" font-family="monospace">seed {seed:02d}</text>',
            f'<rect x="280" y="{y}" width="{g*55}" height="20" rx="4" fill="#50cba8"/>',
            f'<text x="{290+g*55}" y="{y+18}" fill="#effaff" font-family="monospace" font-size="18">{g}</text>',
            f'<rect x="780" y="{y}" width="{o*55}" height="20" rx="4" fill="#f497a2"/>',
            f'<text x="{790+o*55}" y="{y+18}" fill="#effaff" font-family="monospace" font-size="18">{o}</text>',
        ]
    out += [
        f'<text x="55" y="796" fill="#c4dfed" font-size="21" font-family="Arial,sans-serif">Total probes: honest {sum(clean)} · oracle-informed {sum(impure)} · descriptive, no confirmation.</text>',
        '</svg>',
    ]
    return "\n".join(out)+"\n"


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        raw=args.evidence.read_bytes()
        verifier.verify(raw,args.sha256)
        data=verifier.parse(raw)
        args.output_dir.mkdir(parents=True,exist_ok=True)
        for filename,body in (
            ("eba001_boundary_matrix.svg",scenarios_svg(data)),
            ("eba001_probe_efficiency.svg",comparisons_svg(data)),
        ):
            out=args.output_dir/filename
            with out.open("x",encoding="utf-8") as f:
                f.write(body)
            print("FIGURE:",out)
            print("SHA256:",hashlib.sha256(body.encode()).hexdigest())
    except (ValueError,KeyError,IndexError,OSError,TypeError) as e:
        print("CHART_FAILED:",e,file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    sys.exit(main())
