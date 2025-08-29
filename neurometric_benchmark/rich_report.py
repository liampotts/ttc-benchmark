import os
import json
import datetime
from typing import List, Dict, Any

import matplotlib.pyplot as plt

from .utils.logging import ensure_dir


def _load_summaries(runs_root: str) -> List[Dict[str, Any]]:
    runs = []
    for root, dirs, files in os.walk(runs_root):
        if 'summary.json' in files:
            try:
                with open(os.path.join(root, 'summary.json'), 'r', encoding='utf-8') as f:
                    s = json.load(f)
                    s['run_dir'] = root
                    runs.append(s)
            except Exception:
                continue
    return runs


def _plot_accuracy_vs_n(runs: List[Dict[str, Any]], out_path: str) -> None:
    fig, ax = plt.subplots()
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    for r in runs:
        by_model.setdefault(r['model_name'], []).append(r)
    for model, items in by_model.items():
        items = sorted(items, key=lambda x: x['n'])
        xs = [it['n'] for it in items]
        ys = [it['accuracy'] for it in items]
        ax.plot(xs, ys, marker='o', label=model)
    ax.set_xlabel('N')
    ax.set_ylabel('Accuracy')
    ax.set_title('Accuracy vs N')
    ax.legend()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)


def _plot_latency_vs_n(runs: List[Dict[str, Any]], out_path: str) -> None:
    fig, ax = plt.subplots()
    by_model: Dict[str, List[Dict[str, Any]]] = {}
    for r in runs:
        by_model.setdefault(r['model_name'], []).append(r)
    for model, items in by_model.items():
        items = sorted(items, key=lambda x: x['n'])
        xs = [it['n'] for it in items]
        ys = [it['duration_sec'] for it in items]
        ax.plot(xs, ys, marker='o', label=model)
    ax.set_xlabel('N')
    ax.set_ylabel('Duration (s)')
    ax.set_title('Latency vs N')
    ax.legend()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)


def _plot_cost_vs_accuracy(runs: List[Dict[str, Any]], out_path: str) -> None:
    fig, ax = plt.subplots()
    for r in runs:
        cost = r.get('total_cost_usd', 0.0)
        ax.scatter(cost, r['accuracy'], label=f"{r['model_name']} n={r['n']}")
    ax.set_xlabel('Cost (USD)')
    ax.set_ylabel('Accuracy')
    ax.set_title('Cost vs Accuracy')
    ax.legend(fontsize='small')
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)


def _plot_efficiency(runs: List[Dict[str, Any]], out_path: str) -> str:
    """Plot efficiency curve for 1B TTC vs 7B single-shot.

    Returns a human-readable string describing where the 1B curve crosses the 7B
    baseline, or an empty string if no intersection is found.
    """
    fig, ax = plt.subplots()
    oneb = [r for r in runs if '1b' in r['model_name'].lower()]
    sevenb = [r for r in runs if '7b' in r['model_name'].lower() and r.get('n', 1) == 1]
    if not oneb or not sevenb:
        fig.savefig(out_path, bbox_inches='tight')
        plt.close(fig)
        return ''
    seven = max(sevenb, key=lambda x: x['accuracy'])
    baseline_acc = seven['accuracy']
    ax.scatter([seven.get('total_cost_usd', 0.0)], [seven['accuracy']], marker='x', color='red', label='7B single-shot')
    ax.annotate('7B n=1', (seven.get('total_cost_usd', 0.0), seven['accuracy']))
    oneb = sorted(oneb, key=lambda x: x['n'])
    xs = [r.get('total_cost_usd', 0.0) for r in oneb]
    ys = [r['accuracy'] for r in oneb]
    ns = [r['n'] for r in oneb]
    ax.plot(xs, ys, marker='o', label='1B + TTC')
    cross_text = ''
    for x, y, n in zip(xs, ys, ns):
        if y >= baseline_acc:
            ax.axvline(x, color='gray', linestyle='--')
            ax.annotate(f'N={n}', (x, y), textcoords='offset points', xytext=(5, -5))
            cross_text = f"1B+TTC matches 7B single-shot accuracy at N={n} (cost ≈ ${x:.2f})."
            break
    ax.set_xlabel('Cost (USD)')
    ax.set_ylabel('Accuracy')
    ax.set_title('Efficiency Curve')
    ax.legend()
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)
    return cross_text


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; margin: 40px; }}
    h1, h2 {{ margin: 0.2em 0; }}
    img {{ max-width: 100%; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p><strong>Generated:</strong> {date}</p>
  <h2>Accuracy vs N</h2>
  <img src="{acc_img}" alt="Accuracy vs N">
  <h2>Latency vs N</h2>
  <img src="{lat_img}" alt="Latency vs N">
  <h2>Cost vs Accuracy</h2>
  <img src="{cost_img}" alt="Cost vs Accuracy">
  <h2>Efficiency Curve</h2>
  <img src="{eff_img}" alt="Efficiency Curve">
  <p>{cross_text}</p>
</body>
</html>
"""

MD_TEMPLATE = """
# {title}

Generated: {date}

## Accuracy vs N
![Accuracy vs N]({acc_img})

## Latency vs N
![Latency vs N]({lat_img})

## Cost vs Accuracy
![Cost vs Accuracy]({cost_img})

## Efficiency Curve
![Efficiency Curve]({eff_img})

{cross_text}
"""


def generate_report(runs_root: str, out_dir: str, title: str = 'Neurometric TTC Benchmark Report') -> Dict[str, str]:
    runs = _load_summaries(runs_root)
    if not runs:
        raise RuntimeError(f'No runs found under {runs_root}')
    ensure_dir(out_dir)
    figs_dir = os.path.join(out_dir, 'figs')
    ensure_dir(figs_dir)
    acc_path = os.path.join(figs_dir, 'accuracy_vs_n.png')
    lat_path = os.path.join(figs_dir, 'latency_vs_n.png')
    cost_path = os.path.join(figs_dir, 'cost_vs_accuracy.png')
    eff_path = os.path.join(figs_dir, 'efficiency_curve.png')

    _plot_accuracy_vs_n(runs, acc_path)
    _plot_latency_vs_n(runs, lat_path)
    _plot_cost_vs_accuracy(runs, cost_path)
    cross_text = _plot_efficiency(runs, eff_path)

    date = datetime.datetime.now().isoformat(timespec='seconds')
    html = HTML_TEMPLATE.format(
        title=title,
        date=date,
        acc_img=os.path.relpath(acc_path, out_dir),
        lat_img=os.path.relpath(lat_path, out_dir),
        cost_img=os.path.relpath(cost_path, out_dir),
        eff_img=os.path.relpath(eff_path, out_dir),
        cross_text=cross_text,
    )
    md = MD_TEMPLATE.format(
        title=title,
        date=date,
        acc_img=os.path.relpath(acc_path, out_dir),
        lat_img=os.path.relpath(lat_path, out_dir),
        cost_img=os.path.relpath(cost_path, out_dir),
        eff_img=os.path.relpath(eff_path, out_dir),
        cross_text=cross_text,
    )
    html_path = os.path.join(out_dir, 'rich_report.html')
    md_path = os.path.join(out_dir, 'rich_report.md')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md)
    return {'html': html_path, 'markdown': md_path}
