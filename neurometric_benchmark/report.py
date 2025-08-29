import os, json, datetime
from typing import Dict, Any

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Neurometric TTC Benchmark Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; margin: 40px; }}
    h1, h2, h3 {{ margin: 0.2em 0; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1em; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background: #f7f7f7; }}
    code {{ background: #f2f2f2; padding: 2px 4px; border-radius: 3px; }}
    .ok {{ color: #0a7d00; font-weight: 600; }}
    .bad {{ color: #b00020; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Neurometric TTC Benchmark Report</h1>
  <p><strong>Generated:</strong> {date}</p>
  <h2>Summary</h2>
  <table>
    <tr><th>Task File</th><td>{task_path}</td></tr>
    <tr><th>Model</th><td>{model_backend} / {model_name}</td></tr>
    <tr><th>Strategy</th><td>{strategy}</td></tr>
    <tr><th>N</th><td>{n}</td></tr>
    <tr><th>Temperature</th><td>{temperature}</td></tr>
    <tr><th>Num Tasks</th><td>{num_tasks}</td></tr>
    <tr><th>Accuracy</th><td>{accuracy:.2%}</td></tr>
    <tr><th>Duration (s)</th><td>{duration:.1f}</td></tr>
    <tr><th>Cost (USD)</th><td>{cost:.4f}</td></tr>
  </table>
  <h2>Details</h2>
  <table>
    <tr><th>#</th><th>Task ID</th><th>Type</th><th>OK?</th><th>Score</th><th>Meta</th></tr>
    {rows}
  </table>
</body>
</html>
"""

def render(details_path: str, summary_path: str, out_html: str):
    with open(summary_path, 'r', encoding='utf-8') as f:
        s = json.load(f)
    rows = []
    with open(details_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            rec = json.loads(line)
            cls = 'ok' if rec.get('ok') else 'bad'
            meta = rec.get('meta', {})
            rows.append(
                f"<tr><td>{i}</td><td>{rec.get('task_id')}</td><td>{rec.get('type')}</td>"
                f"<td class='{cls}'>{rec.get('ok')}</td><td>{rec.get('score'):.2f}</td>"
                f"<td><code>{json.dumps(meta)[:200]}</code></td></tr>"
            )
    html = TEMPLATE.format(
        date=datetime.datetime.now().isoformat(timespec='seconds'),
        task_path=s.get('task_path'),
        model_backend=s.get('model_backend'),
        model_name=s.get('model_name'),
        strategy=s.get('strategy'),
        n=s.get('n'),
        temperature=s.get('temperature'),
        num_tasks=s.get('num_tasks'),
        accuracy=s.get('accuracy', 0.0),
        duration=s.get('duration_sec', 0.0),
        cost=s.get('total_cost_usd', 0.0),
        rows='\n'.join(rows)
    )
    with open(out_html, 'w', encoding='utf-8') as f:
        f.write(html)
