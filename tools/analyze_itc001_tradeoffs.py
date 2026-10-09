"""ITC-001 after-observation descriptive statistical/computational frontier.

Computes ACCURACY against RECURRENT STATE-UPDATE COUNT. This does not
estimate formal statistical or computational thresholds; model/task families
are fixed and the test data were already observed. Records all policies.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
from xml.sax.saxutils import escape
import numpy as np

POLICIES=("fixed1","fixed2","fixed3","fixed5",
          "adaptive","shuffle_task","shuffle_global")
COLORS={
    "fixed1":"#84b6f4","fixed2":"#8fc9e5","fixed3":"#55cbad",
    "fixed5":"#e8c17e","adaptive":"#d894ee",
    "shuffle_task":"#f29c9c","shuffle_global":"#c6a9a0",
}

def plot_svg(points,frontier):
    x0,x1,y0,y1=1.0,5.2,.84,.94
    def xy(x,y):
        return (180+1140*(x-x0)/(x1-x0),
                800-550*(y-y0)/(y1-y0))
    lines=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="1580" height="1030" viewBox="0 0 1580 1030" role="img" aria-labelledby="title desc">',
        '<title id="title">ITC-001 empirical accuracy versus recurrent-step cost frontier</title>',
        '<desc id="desc">Seven policies evaluated using a single shared six-seed, 1153-weight recurrent model. Fixed3 achieved higher mean accuracy with fewer steps than fixed5. Adaptive used 2.98 passes but did not reliably beat shuffled depth allocation. Post-hoc exploratory frontier, not a formal statistical-computational threshold.</desc>',
        '<rect width="1580" height="1030" fill="#071a2a"/>',
        '<rect x="24" y="25" width="1532" height="983" rx="30" fill="#11283d" stroke="#3a5a76" stroke-width="2"/>',
        '<text x="58" y="87" fill="#eefaff" font-size="39" font-weight="bold" font-family="Arial,sans-serif">Accuracy versus internal computation</text>',
        '<text x="58" y="132" fill="#c2d8eb" font-size="24" font-family="Arial,sans-serif">ITC-001 · six public model seeds · 3072 held-out bit patterns per seed</text>',
        '<text x="58" y="173" fill="#ffc68d" font-size="22" font-weight="bold" font-family="Arial,sans-serif">POST-HOC DESCRIPTIVE FRONTIER · NOT A COMPLEXITY THRESHOLD</text>',
    ]
    for y in (.85,.87,.89,.91,.93):
        a,b=xy(1,y)
        lines.extend([
            f'<line x1="180" y1="{b:.2f}" x2="1330" y2="{b:.2f}" stroke="#32516a" stroke-dasharray="6 8"/>',
            f'<text x="160" y="{b+7:.2f}" fill="#d9ebf9" text-anchor="end" font-size="21" font-family="monospace">{y*100:.0f}%</text>',
        ])
    for x in (1,2,3,4,5):
        a,b=xy(x,.84)
        lines.append(f'<text x="{a:.2f}" y="837" fill="#d7ecfa" text-anchor="middle" font-size="22" font-family="monospace">{x}</text>')
    lines.extend([
        '<text x="660" y="881" fill="#e6f4ff" font-size="26" font-family="Arial,sans-serif">Mean hidden recurrent passes / instance →</text>',
        '<text x="73" y="236" fill="#cfe5f6" font-size="21" font-family="Arial,sans-serif">Held-out macro accuracy ↑</text>',
    ])
    frontier_points=sorted((points[k] for k in frontier),key=lambda p:p["mean_passes"])
    poly=" ".join(f'{xy(p["mean_passes"],p["macro_accuracy"])[0]:.1f},{xy(p["mean_passes"],p["macro_accuracy"])[1]:.1f}'
                  for p in frontier_points)
    lines.append(f'<polyline points="{poly}" fill="none" stroke="#61cbb0" stroke-width="4" stroke-dasharray="10,7"/>')
    for name in POLICIES:
        p=points[name]
        x,y=xy(p["mean_passes"],p["macro_accuracy"])
        color=COLORS[name]
        lines.extend([
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="10" fill="{color}" stroke="#f4fbff" stroke-width="2"/>',
            f'<text x="{x+14:.1f}" y="{y-15:.1f}" fill="{color}" font-size="20" font-family="Arial,sans-serif">{escape(name)}</text>',
        ])
    lines.extend([
        '<line x1="55" y1="930" x2="1518" y2="930" stroke="#355975"/>',
        '<text x="58" y="970" font-size="20" font-family="Arial,sans-serif" fill="#c5deee">Dashed line: observed non-dominated means, not confidence-adjusted or a theoretical limit.</text>',
        '</svg>',
    ])
    return "\n".join(lines)+"\n"

def analyze(data):
    if data.get("protocol")!="ITC-001" or data.get("status")!=(
        "PUBLIC_EXPLORATORY_INTERNAL_COMPUTATION_NOT_VALIDATED"):
        raise ValueError("invalid or overpromoted research status")
    records=data["seed_records"]
    if len(records)!=6 or [r["seed"] for r in records]!=list(range(20261161,20261167)):
        raise ValueError("registered seed inventory incomplete")
    summary=data["aggregate"]
    points={}
    for name in POLICIES:
        values=[r["policy_results"][name] for r in records]
        accuracies=[v["macro_accuracy"] for v in values]
        passes=[v["mean_passes"] for v in values]
        points[name]={
            "policy":name,
            "mean_passes":float(np.mean(passes)),
            "macro_accuracy":float(np.mean(accuracies)),
            "seed_accuracies":accuracies,
            "seed_passes":passes,
        }
    frontier=[]
    dominated={}
    for name,p in points.items():
        others=[q for other,q in points.items() if other!=name and
                q["mean_passes"]<=p["mean_passes"] and
                q["macro_accuracy"]>=p["macro_accuracy"] and
                (q["mean_passes"]<p["mean_passes"] or
                 q["macro_accuracy"]>p["macro_accuracy"])]
        dominated[name]=[other["policy"] for other in others]
        if not others:frontier.append(name)
    task_stats={}
    for task in range(6):
        task_stats[str(task)]={
            "adaptive_accuracy":float(np.mean([
                r["policy_results"]["adaptive"]["task_accuracy"][task]
                for r in records])),
            "fixed5_accuracy":float(np.mean([
                r["policy_results"]["fixed5"]["task_accuracy"][task]
                for r in records])),
            "shuffled_task_accuracy":float(np.mean([
                r["policy_results"]["shuffle_task"]["task_accuracy"][task]
                for r in records])),
            "adaptive_mean_passes":float(np.mean([
                r["policy_results"]["adaptive"]["passes_by_task"][task]/512
                for r in records])),
        }
    return {
        "protocol":"ITC-001-POSTHOC-EMPIRICAL-FRONTIER",
        "status":"EXPLORATORY_POST_HOC_NOT_VALIDATED",
        "formal_information_threshold":"NOT_ESTABLISHED",
        "formal_computational_threshold":"NOT_ESTABLISHED",
        "formal_statistical_computational_gap":"NOT_ESTABLISHED",
        "cost_proxy":"mean recurrent-state updates per instance, not measured joules",
        "actual_runtime":"NOT_IN_THIS_ARCHIVED_EXPERIMENT",
        "points":points,"non_dominated_mean_points":frontier,
        "dominated_by":dominated,"task_diagnostics":task_stats,
        "H1":summary["H1"],"H2":summary["H2"],
        "limitations":[
            "Post-hoc exploratory analysis of already-observed fixed tasks/seeds",
            "Means-based Pareto relations may reverse under resampling or new hardware",
            "Full-depth probabilities were precomputed in original trial",
            "Model training compute was held identical, not minimized",
            "An empirical accuracy-versus-step frontier is not a complexity-theory threshold",
        ],
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    p.add_argument("--sha256",required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args(argv)
    raw=a.evidence.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=a.sha256:
        p.error("source evidence SHA256 does not match")
    original=json.loads(raw)
    result=analyze(original)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    outputs=[
        ("itc001_posthoc_frontier.json",json.dumps(result,sort_keys=True,indent=2)+"\n"),
        ("itc001_empirical_frontier.svg",plot_svg(result["points"],
                                                  result["non_dominated_mean_points"])),
    ]
    for name,body in outputs:
        path=a.output_dir/name
        with path.open("x",encoding="utf-8") as f:f.write(body)
        print("OUTPUT:",path)
        print("SHA256:",hashlib.sha256(body.encode()).hexdigest())
    for name,p in result["points"].items():
        print("POLICY:",name,"ACCURACY:",p["macro_accuracy"],
              "MEAN_PASSES:",p["mean_passes"],
              "DOMINATED_BY:",result["dominated_by"][name])
    print("STATUS: EXPLORATORY_POST_HOC_NOT_VALIDATED")
    return 0

if __name__=="__main__":sys.exit(main())
