"""Render transparent ASP-001 SVGs only after independent semantic replay.

No chart alone constitutes proof of improved plasticity or biology.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
from xml.sax.saxutils import escape

PATH=Path(__file__).resolve().parent/"verify_asp001.py"
spec=importlib.util.spec_from_file_location("asp001_chart_replay",PATH)
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
COLORS=("#84b6f4","#90d9c0","#f6c48c","#cca3ef","#f38c96","#58d0b1")

def esc(s):return escape(str(s),{'"':"&quot;"})
def svg_bar(data):
    meta=data["summary"]["by_arm"]
    arms=data["arms"]
    maxima=max(x["joint_B_mean"] for x in meta.values())*1.10
    out=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="920" viewBox="0 0 1500 920" role="img" aria-labelledby="title desc">',
        '<title id="title">ASP-001 actual neural-network joint held-out A/B error after B phase</title>',
        '<desc id="desc">Six 1-16-1 neural network training policies compared on identical public 24 seeds with 128 updates each at the B checkpoint. This is exploratory and not validated for larger AI systems.</desc>',
        '<rect width="1500" height="920" fill="#091b2b"/>',
        '<rect x="25" y="25" width="1450" height="870" rx="27" fill="#112941" stroke="#3c5873" stroke-width="2"/>',
        '<text x="56" y="84" fill="#f2faff" font-family="Arial,sans-serif" font-size="38" font-weight="bold">ASP-001 · Does internal regulation help learning?</text>',
        f'<text x="56" y="130" fill="#d1e1ef" font-family="Arial,sans-serif" font-size="23">Mean joint held-out MSE after B · {len(data["seeds"])} paired seeds · lower is better</text>',
        '<text x="56" y="170" fill="#ffc68c" font-family="Arial,sans-serif" font-size="22" font-weight="bold">ACTUAL SMALL NEURAL NETWORK · EXPLORATORY · NOT VALIDATED</text>',
    ]
    for i,(name,color) in enumerate(zip(arms,COLORS)):
        y=235+85*i
        m=meta[name]["joint_B_mean"]
        w=780*m/maxima
        out.extend([
            f'<text x="57" y="{y+34}" fill="#eaf5ff" font-family="Arial,sans-serif" font-size="26">{esc(name)}</text>',
            f'<rect x="350" y="{y+4}" width="780" height="43" rx="8" fill="#244259"/>',
            f'<rect x="350" y="{y+4}" width="{w:.2f}" height="43" rx="8" fill="{color}"/>',
            f'<text x="1165" y="{y+37}" fill="#eaf5ff" font-family="monospace" font-size="25">{m:.6f}</text>',
        ])
    out.extend([
        '<line x1="56" y1="781" x2="1435" y2="781" stroke="#3c5671"/>',
        f'<text x="56" y="821" fill="#dceefa" font-family="Arial,sans-serif" font-size="23">Registered H1: {esc(data["summary"]["H1"])}</text>',
        '<text x="56" y="857" fill="#9fbdd5" font-family="Arial,sans-serif" font-size="19">Data: independently replayed ASP-001 JSON. No external-model or biological mechanism validated.</text>',
        '</svg>',
    ])
    return "\n".join(out)+"\n"

def svg_regulator(data):
    rows=data["runs"]
    regulator=[next(a for a in row["arms"] if a["arm"]=="regulated_sgd") for row in rows]
    count=data["steps_per_phase"]*3
    average=[sum(arm["steps"][step]["modulator"] for arm in regulator)/len(regulator)
             for step in range(count)]
    left,top,width,height=130,210,1180,425
    def xloc(i):return left+width*i/(count-1)
    def yloc(val):return top+height*(1.45-val)/1.2
    path=" ".join(f"{xloc(i):.2f},{yloc(a):.2f}" for i,a in enumerate(average))
    out=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="875" viewBox="0 0 1500 875" role="img" aria-labelledby="title desc">',
        '<title id="title">ASP-001 self-generated modulator values across sequential neural network learning</title>',
        '<desc id="desc">Mean regulator scalar, bounded 0.35 to 1.40, evolves over 192 training updates on task sequence A, B, A. It is computed from gradient alignment and training loss surprise; no biological neurotransmitter is involved.</desc>',
        '<rect width="1500" height="875" fill="#081a29"/>',
        '<rect x="25" y="26" width="1450" height="824" rx="27" fill="#13283e" stroke="#365a76" stroke-width="2"/>',
        '<text x="55" y="88" fill="#f3faff" font-size="39" font-family="Arial,sans-serif" font-weight="bold">Internally generated learning modulation</text>',
        '<text x="55" y="131" fill="#bbd4e8" font-size="23" font-family="Arial,sans-serif">Mean rate multiplier over all public paired seeds · A → B → A</text>',
        '<text x="55" y="174" fill="#ffc68b" font-size="22" font-family="Arial,sans-serif" font-weight="bold">NUMERICAL LEARNING CONTROLLER · NOT ARTIFICIAL CHEMISTRY</text>',
    ]
    for val in (.35,.6,.9,1.2,1.4):
        yy=yloc(val)
        out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left+width}" y2="{yy:.1f}" stroke="#385d79"/>')
        out.append(f'<text x="{left-16}" y="{yy+7:.1f}" font-size="20" text-anchor="end" fill="#d0e6f5" font-family="monospace">{val:.2f}</text>')
    for step in (data["steps_per_phase"],2*data["steps_per_phase"]):
        xpos=left+width*(step-.5)/(count-1)
        out.append(f'<line x1="{xpos:.2f}" y1="{top}" x2="{xpos:.2f}" y2="{top+height}" stroke="#efb777" stroke-width="2" stroke-dasharray="9,9"/>')
    for i,text in enumerate(("First task A","Noisy task B","Return to A")):
        start=i*data["steps_per_phase"]
        midpoint=start+data["steps_per_phase"]//2
        out.append(f'<text x="{xloc(min(midpoint,count-1)):.1f}" y="680" fill="#e7f5ff" font-size="23" text-anchor="middle" font-family="Arial,sans-serif">{text}</text>')
    out.append(f'<polyline points="{path}" fill="none" stroke="#4dd1ac" stroke-width="4"/>')
    out.append('<text x="55" y="785" fill="#b4cee3" font-size="21" font-family="Arial,sans-serif">This curve establishes nonconstant modulation, not improved accuracy or adaptive intelligence.</text>')
    out.append('</svg>')
    return "\n".join(out)+"\n"

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--output-dir",required=True,type=Path)
    args=p.parse_args(argv)
    try:
        raw=args.evidence.read_bytes()
        v.verify(raw,args.sha256)
        data=json.loads(raw,object_pairs_hook=v.unique,parse_constant=v.no_nonfinite)
        args.output_dir.mkdir(parents=True,exist_ok=True)
        for name,svg in (
            ("asp001_joint_mse.svg",svg_bar(data)),
            ("asp001_modulation.svg",svg_regulator(data)),
        ):
            output=args.output_dir/name
            with output.open("x",encoding="utf-8") as file:file.write(svg)
            print("FIGURE:",output)
            print("SHA256:",hashlib.sha256(svg.encode()).hexdigest())
    except (ValueError,TypeError,KeyError,OSError,OverflowError) as error:
        print("CHART_FAILED:",error,file=sys.stderr)
        return 1
    return 0
if __name__=="__main__":sys.exit(main())
