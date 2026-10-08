"""VSC-003 SVG evidence visualizations. Independent replay is mandatory first.

Stdlib; no network, no models, no third-party code. Lines plot all preregistered
policies and report public toy findings, NOT claims of scientific validation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

VERIFY_FILE=Path(__file__).resolve().with_name("verify_vsc003.py")
spec=importlib.util.spec_from_file_location("vsc003_verification",VERIFY_FILE)
verifier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

COLORS=(
    "#42c9ad","#e0c475","#8d9cf4","#fca77b",
    "#f47cc3","#6db8ee","#d6a6f3","#bcf074",
    "#ffaa9b","#cbd0db","#9fb6ca",
)
PLOTS=(
    ("in_domain_macro_mse","In-domain generalization error","Lower MSE is better","vsc003_in_domain.svg"),
    ("shift_macro_mse","Shifted-domain generalization error","Out-of-range x values; lower MSE is better","vsc003_shifted.svg"),
    ("rare_band_mse","Rare-band generalization error","Rare band has only 5% natural prevalence","vsc003_rare.svg"),
    ("gold_cell_coverage","Gold-labeled training-cell coverage","True numeric oracle labels used for training only","vsc003_gold_coverage.svg"),
    ("accepted_cell_coverage","Accepted training-example coverage","Includes gold and imperfect synthetic labels","vsc003_accepted_coverage.svg"),
)


def sanitized(x):
    return escape(str(x), {'"':"&quot;","'":"&apos;"})


def generic_curve(data,key,name,subtitle):
    w,h=1600,900
    bx,by,bw,bh=148,225,1050,420
    summary=data["summary"]
    modes=data["arms"]
    ng=data["generations"]
    traces=[summary[policy]["curves"][key] for policy in modes]
    upper=max(max(v for v in trace) for trace in traces)*1.10
    if upper<=0: upper=1
    if "coverage" in key: upper=1
    def xp(i): return bx+bw*i/ng
    def yp(v): return by+bh*(1-v/upper)
    out=[
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{sanitized(name)} — VSC-003</title>',
        f'<desc id="desc">{sanitized(subtitle)} Eleven experimental policies, 24 public synthetic seeds. This is exploratory and not validated for actual language models.</desc>',
        '<rect width="1600" height="900" fill="#081724"/>',
        '<rect x="24" y="26" width="1552" height="848" rx="24" fill="#11263b" stroke="#38546e" stroke-width="2"/>',
        f'<text x="55" y="88" fill="#f0f8ff" font-family="Arial,sans-serif" font-size="40" font-weight="bold">{sanitized(name)}</text>',
        f'<text x="55" y="130" fill="#c1d5e8" font-family="Arial,sans-serif" font-size="23">{sanitized(subtitle)} · {data["n_seeds"]} public seeds · {ng} generations</text>',
        '<text x="55" y="175" fill="#ffc68a" font-family="Arial,sans-serif" font-size="21" font-weight="bold">EXPLORATORY TOY SIMULATION · NOT VALIDATED · NO LANGUAGE MODEL</text>',
    ]
    for j in range(5):
        val=upper*j/4
        y=yp(val)
        out.append(f'<line x1="{bx}" y1="{y:.2f}" x2="{bx+bw}" y2="{y:.2f}" stroke="#365571" stroke-width="1"/>')
        out.append(f'<text x="{bx-14}" y="{y+5:.2f}" fill="#d4e6f4" font-family="monospace" font-size="18" text-anchor="end">{val:.3f}</text>')
    for t in (0,ng//2,ng):
        out.append(f'<text x="{xp(t):.2f}" y="{by+bh+33}" fill="#c7deef" font-family="monospace" font-size="22" text-anchor="middle">{t}</text>')
    out.append(f'<text x="{bx+bw/2:.2f}" y="{by+bh+76}" fill="#c7deef" font-family="Arial,sans-serif" font-size="21" text-anchor="middle">Training generation</text>')
    for i,(arm,series,color) in enumerate(zip(modes,traces,COLORS)):
        points=" ".join(f"{xp(t):.2f},{yp(v):.2f}" for t,v in enumerate(series))
        out.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3.3"/>')
        y=by+7+i*41
        out.append(f'<line x1="1220" y1="{y+11}" x2="1258" y2="{y+11}" stroke="{color}" stroke-width="5"/>')
        out.append(f'<text x="1267" y="{y+17}" fill="#eff7fe" font-family="Arial,sans-serif" font-size="16.5">{sanitized(arm.replace("_"," "))}</text>')
    out.append('<text x="55" y="788" fill="#b7cfe4" font-family="Arial,sans-serif" font-size="20">Curves show arithmetic means. No error bars or statistical confirmation.</text>')
    out.append('<text x="55" y="830" fill="#91aec6" font-family="Arial,sans-serif" font-size="19">Source: VSC-003 GitHub evidence artifact and independently replayed SHA256 receipt; see report.</text>')
    out.append('</svg>')
    return "\n".join(out)+"\n"


def budget_chart(data):
    modes=data["arms"]
    summaries=data["summary"]
    w,h=1550,1090
    out=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1550" height="1090" viewBox="0 0 1550 1090" role="img" aria-labelledby="title desc">',
        '<title id="title">VSC-003 weak verification cost and error audit</title>',
        '<desc id="desc">All eleven policies compared on acquisition credits, costly gold-label queries, cheap Boolean checks, and imperfect verifier decisions. Synthetic exploratory evidence only.</desc>',
        '<rect width="1550" height="1090" fill="#071727"/>',
        '<rect x="25" y="25" width="1500" height="1040" rx="24" fill="#12293e" stroke="#395b74" stroke-width="2"/>',
        '<text x="55" y="85" font-family="Arial,sans-serif" font-size="41" fill="#f2faff" font-weight="bold">Weak verification: budget and failure audit</text>',
        '<text x="55" y="132" font-family="Arial,sans-serif" font-size="22" fill="#c0d6e8">Per-seed mean over public toy seeds · cost = 6 per gold label, 1 per Boolean check</text>',
        '<text x="55" y="175" font-family="Arial,sans-serif" font-size="21" fill="#ffc88d" font-weight="bold">EXPLORATORY / SIMULATED / NOT VALIDATED</text>',
        '<text x="450" y="222" font-family="Arial,sans-serif" font-size="21" fill="#e6f6ff">Acquisition credits</text>',
        '<text x="880" y="222" font-family="Arial,sans-serif" font-size="21" fill="#e6f6ff">Gold / weak queries</text>',
        '<text x="1220" y="222" font-family="Arial,sans-serif" font-size="21" fill="#e6f6ff">False accepts / rejects</text>',
    ]
    max_credit=data["generations"]*12
    for i,mode in enumerate(modes):
        y=250+i*65
        stats=summaries[mode]["mean_totals"]
        spent=stats["credits_spent"]
        strong=stats["strong_queries"]
        weak=stats["weak_queries"]
        fa=stats["false_accept"]
        fr=stats["false_reject"]
        out.extend([
            f'<text x="50" y="{y+25}" fill="#ecf7ff" font-family="Arial,sans-serif" font-size="20">{sanitized(mode)}</text>',
            f'<rect x="440" y="{y}" width="365" height="34" rx="8" fill="#2b465a"/>',
            f'<rect x="440" y="{y}" width="{365*spent/max_credit:.2f}" height="34" rx="8" fill="#50c9a9"/>',
            f'<text x="820" y="{y+24}" font-family="monospace" font-size="20" fill="#ecf7ff">{spent:.0f}</text>',
            f'<text x="902" y="{y+24}" font-family="monospace" font-size="20" fill="#ecf7ff">{strong:.0f}G / {weak:.0f}W</text>',
            f'<text x="1260" y="{y+24}" font-family="monospace" font-size="20" fill="#ecf7ff">{fa:.1f} / {fr:.1f}</text>',
        ])
    out.append('<text x="55" y="1031" font-family="Arial,sans-serif" font-size="20" fill="#afcadf">All nonrecursive arms spend equal total acquisition credits; oracle queries and model-update costs differ.</text>')
    out.append('</svg>')
    return "\n".join(out)+"\n"


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args(argv)
    try:
        content=a.evidence.read_bytes()
        result=verifier.verify(content,a.sha256)
        data=json.loads(content,object_pairs_hook=verifier.unique_keys,
                        parse_constant=verifier.nonfinite)
        a.output_dir.mkdir(parents=True,exist_ok=True)
        charts=[(filename,generic_curve(data,key,title,subtitle))
                for key,title,subtitle,filename in PLOTS]
        charts.append(("vsc003_budget_and_weak_errors.svg",budget_chart(data)))
        for name,graphic in charts:
            dest=a.output_dir/name
            with dest.open("x",encoding="utf-8") as out:
                out.write(graphic)
            print("FIGURE:",dest)
            print("FIGURE_SHA256:",hashlib.sha256(graphic.encode()).hexdigest())
        print("REPLAY_VERDICT:",result["verdict"])
        print("ANTI_VACUITY:",result["anti_vacuity"])
    except (ValueError,TypeError,KeyError,OSError,OverflowError) as err:
        print("PLOT_FAILED:",err,file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    sys.exit(main())
