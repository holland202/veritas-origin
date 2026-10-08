"""Independently verified, fully labeled SVG charts for VSC-002.

Read raw evidence only after independent SHA and semantic replay. No model,
network, subprocess, matplotlib, external assets, or source from QUASAR.
Charts are exploratory descriptions of a public toy simulation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "independent_vsc002_verifier", ROOT / "tools/verify_vsc002.py"
)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)

COLORS = (
    "#6fa8ff", "#d6b36d", "#ff866d", "#30d7af",
    "#e68af0", "#66d0e9", "#cfdaed", "#faa5b8",
)
CHARTS = (
    ("id_macro_mse", "Held-out in-domain macro MSE",
     "Lower is better. Final test labels never select the curriculum.",
     "vsc002_in_domain_mse.svg"),
    ("shift_macro_mse", "Held-out shifted-domain macro MSE",
     "Lower is better. Input values extend beyond the training range.",
     "vsc002_shifted_mse.svg"),
    ("rare_band_mse", "Rare-band (band 3) held-out MSE",
     "Lower is better. The rare band has only 5% natural prevalence.",
     "vsc002_rare_band_mse.svg"),
    ("gold_label_cell_coverage", "True gold-label training diversity",
     "Fraction of 32 band-by-x cells containing direct oracle labels.",
     "vsc002_gold_label_diversity.svg"),
    ("accepted_cell_coverage", "All accepted-label training diversity",
     "Includes gold and accepted synthetic pseudo-labels: not all ground truth.",
     "vsc002_accepted_label_diversity.svg"),
)


def document_title(label, n, generations):
    return f"{label} | n={n} public synthetic seeds | {generations} generations"


def safe(x):
    return escape(str(x), {"\"":"&quot;", "'":"&apos;"})


def svg_line_chart(doc, metric, title, description):
    """One chart. Eight line series represent all eight preregistered policies."""
    W, H = 1500, 850
    px, py, pw, ph = 145, 215, 1040, 410
    summary = doc["summary"]
    policies = doc["arms_order"]
    generations = doc["generations"]
    tracks = [summary[p]["curves"][metric] for p in policies]
    extrema = max(max(track) for track in tracks)
    upper = max(extrema*1.13, 1.0e-8)
    def xpoint(t): return px + pw*t/generations
    def ypoint(v): return py + ph*(1-v/upper)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{safe(document_title(title,doc["seeds"],generations))}</title>',
        f'<desc id="desc">{safe(description)} All eight policies appear. Data are from an exploratory public-seed mathematical simulation, not a language model or data-wall breakthrough.</desc>',
        f'<rect width="{W}" height="{H}" fill="#091827"/>',
        f'<rect x="22" y="24" width="{W-44}" height="{H-48}" rx="28" fill="#102238" stroke="#32546e" stroke-width="2"/>',
        f'<text x="65" y="86" font-family="Arial,sans-serif" font-size="36" font-weight="bold" fill="#eff7ff">{safe(title)}</text>',
        f'<text x="65" y="128" font-family="Arial,sans-serif" font-size="23" fill="#bbd3ed">{safe(description)}</text>',
        f'<text x="65" y="170" font-family="Arial,sans-serif" font-size="20" fill="#ffc683" font-weight="bold">EXPLORATORY · PUBLIC TOY SIMULATION · NOT VALIDATED · NO LANGUAGE MODEL</text>',
    ]
    for i in range(5):
        val = upper*i/4
        y = ypoint(val)
        parts += [
            f'<line x1="{px}" y1="{y:.2f}" x2="{px+pw}" y2="{y:.2f}" stroke="#31506b" stroke-width="1"/>',
            f'<text x="{px-15}" y="{y+6:.2f}" fill="#b3c9dc" font-family="monospace" font-size="19" text-anchor="end">{val:.4f}</text>',
        ]
    parts += [
        f'<line x1="{px}" y1="{py}" x2="{px}" y2="{py+ph}" stroke="#adc1d4"/>',
        f'<line x1="{px}" y1="{py+ph}" x2="{px+pw}" y2="{py+ph}" stroke="#adc1d4"/>',
    ]
    ticks = sorted({0, generations//4, generations//2, (3*generations)//4, generations})
    for t in ticks:
        x = xpoint(t)
        parts.append(f'<text x="{x:.2f}" y="{py+ph+33}" font-family="monospace" font-size="20" fill="#d7e7f6" text-anchor="middle">{t}</text>')
    parts.append(f'<text x="{px+pw/2:.2f}" y="{py+ph+72}" font-family="Arial,sans-serif" font-size="22" fill="#d7e7f6" text-anchor="middle">Training generation</text>')
    for index, (name, track, color) in enumerate(zip(policies,tracks,COLORS)):
        coords = " ".join(f"{xpoint(t):.2f},{ypoint(value):.2f}" for t,value in enumerate(track))
        parts.append(f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3.6" stroke-linejoin="round" stroke-linecap="round"/>')
        for t, value in enumerate(track):
            parts.append(f'<circle cx="{xpoint(t):.2f}" cy="{ypoint(value):.2f}" r="3.7" fill="{color}"/>')
        yy = py+12+index*48
        parts += [
            f'<line x1="1230" y1="{yy+11}" x2="1276" y2="{yy+11}" stroke="{color}" stroke-width="5"/>',
            f'<text x="1285" y="{yy+18}" font-family="Arial,sans-serif" font-size="17" fill="#f1f7ff">{safe(name.replace("_"," "))}</text>',
        ]
    parts += [
        f'<text x="65" y="753" font-family="Arial,sans-serif" font-size="19" fill="#c1d4e9">Each point is the mean over {doc["seeds"]} public seeds; error bands are not shown. Curves are descriptive, not confirmatory.</text>',
        f'<text x="65" y="795" font-family="Arial,sans-serif" font-size="18" fill="#90aec8">Source: VSC-002 · see run, SHA256 and artifact in reports/vsc002 · oracle calls and training updates differ by policy</text>',
        '</svg>',
    ]
    return "\n".join(parts)+"\n"


def svg_cost_chart(doc):
    W,H=1500,850
    policies=doc["arms_order"]
    summary=doc["summary"]
    counts=[(summary[mode]["mean_totals"]["new_oracle_queries"],
             summary[mode]["mean_totals"]["updates"]) for mode in policies]
    top=max(max(a,b) for a,b in counts)
    parts=[
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">',
        '<title id="title">VSC-002 new oracle queries versus model training updates</title>',
        '<desc id="desc">Gold and checked policies get identical new query budgets, but some policies perform extra replay or pseudo-label training updates. No hardware power measurement was performed.</desc>',
        '<rect width="1500" height="850" fill="#091827"/>',
        '<rect x="22" y="24" width="1456" height="802" rx="28" fill="#102238" stroke="#32546e" stroke-width="2"/>',
        '<text x="64" y="84" font-family="Arial,sans-serif" font-size="36" font-weight="bold" fill="#eff7ff">Oracle access versus training compute</text>',
        '<text x="64" y="122" font-family="Arial,sans-serif" font-size="23" fill="#bbd3ed">Mean per seed, cumulative over generations. Each group uses a shared numerical scale.</text>',
        '<text x="64" y="159" font-family="Arial,sans-serif" font-size="21" fill="#ffc683" font-weight="bold">PUBLIC SYNTHETIC FIXTURE · EXPLORATORY · NOT VALIDATED</text>',
        '<rect x="610" y="177" width="22" height="20" fill="#68a7ef"/><text x="642" y="193" font-family="Arial,sans-serif" font-size="20" fill="#dbeafa">New oracle label queries</text>',
        '<rect x="981" y="177" width="22" height="20" fill="#f0c97a"/><text x="1013" y="193" font-family="Arial,sans-serif" font-size="20" fill="#dbeafa">Model updates</text>',
    ]
    x0=395
    size=850
    for index,name in enumerate(policies):
        yy=223+index*65
        queries,updates=counts[index]
        wq=queries/top*size
        wu=updates/top*size
        parts += [
            f'<text x="64" y="{yy+21}" font-family="Arial,sans-serif" font-size="22" fill="#e4f2ff">{safe(name.replace("_"," "))}</text>',
            f'<rect x="{x0}" y="{yy}" width="{size}" height="17" rx="4" fill="#294059"/>',
            f'<rect x="{x0}" y="{yy}" width="{wq:.2f}" height="17" rx="4" fill="#68a7ef"/>',
            f'<rect x="{x0}" y="{yy+23}" width="{size}" height="17" rx="4" fill="#294059"/>',
            f'<rect x="{x0}" y="{yy+23}" width="{wu:.2f}" height="17" rx="4" fill="#f0c97a"/>',
            f'<text x="1270" y="{yy+15}" font-family="monospace" font-size="18" fill="#e4f2ff">{queries:.0f} Q</text>',
            f'<text x="1270" y="{yy+39}" font-family="monospace" font-size="18" fill="#e4f2ff">{updates:.0f} U</text>',
        ]
    parts += [
        '<text x="64" y="780" font-family="Arial,sans-serif" font-size="19" fill="#b8cde1">32 initial + 64 selection + 384 final-test truth labels are separately shared per seed, not included in blue bars.</text>',
        '</svg>',
    ]
    return "\n".join(parts)+"\n"


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args(argv)
    try:
        raw=args.evidence.read_bytes()
        replay=VERIFY.check(raw,args.sha256)
        doc=json.loads(raw,object_pairs_hook=VERIFY.unique,
                       parse_constant=VERIFY.nonfinite)
        args.output_dir.mkdir(parents=True,exist_ok=True)
        files=[(filename,svg_line_chart(doc,key,title,desc))
               for key,title,desc,filename in CHARTS]
        files.append(("vsc002_oracle_vs_compute.svg",svg_cost_chart(doc)))
        for filename,plot in files:
            target=args.output_dir/filename
            with target.open("x",encoding="utf-8") as f:
                f.write(plot)
            print("FIGURE:",target)
            print("FIGURE_SHA256:",hashlib.sha256(plot.encode()).hexdigest())
    except (ValueError,TypeError,OSError,KeyError,OverflowError) as e:
        print("PLOT_FAIL:",e,file=sys.stderr)
        return 1
    print("VERDICT:",replay["verdict"])
    print("LIMIT: SVG only charts public synthetic, verified-but-not-worldly evidence")
    return 0


if __name__=="__main__":
    sys.exit(main())
