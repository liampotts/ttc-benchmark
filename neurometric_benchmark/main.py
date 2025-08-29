import argparse, os
from .runners import evaluate
from .report import render
from .rich_report import generate_report as generate_rich_report
from .utils.logging import ensure_dir

def main():
    p = argparse.ArgumentParser(description='Neurometric TTC Benchmark Harness')
    sub = p.add_subparsers(dest='cmd', required=True)

    runp = sub.add_parser('run', help='Run a benchmark')
    runp.add_argument('--task', required=True, help='Path to JSONL task file')
    runp.add_argument('--model', required=True, help='Model spec, e.g., ollama/llama3.2:1b-instruct or openai/gpt-4o')
    runp.add_argument('--strategy', choices=['single', 'best_of_n'], default='single')
    runp.add_argument('--n', type=int, default=1, help='Number of samples for best_of_n')
    runp.add_argument('--temperature', type=float, default=0.7)
    runp.add_argument('--meta-notes', default='', help='Notes to save in run config')
    runp.add_argument('--run-root', default='runs', help='Where to write run artifacts')

    rep = sub.add_parser('report', help='Render an HTML report for a given run dir')
    rep.add_argument('--run-dir', required=True, help='Path to a run directory containing details.jsonl and summary.json')
    rep.add_argument('--out', default=None, help='Output HTML path (defaults to reports/report_TIMESTAMP.html)')

    rich = sub.add_parser('rich_report', help='Generate charts and Markdown/HTML summary across runs')
    rich.add_argument('--runs-root', default='runs', help='Directory containing run_* subdirectories')
    rich.add_argument('--out-dir', default='reports', help='Where to write the rich report')
    rich.add_argument('--title', default='Neurometric TTC Benchmark Report')

    args = p.parse_args()
    if args.cmd == 'run':
        backend, name = args.model.split('/', 1)
        out = evaluate(
            task_path=args.task,
            model_backend=backend,
            model_name=name,
            strategy=args.strategy,
            temperature=args.temperature,
            n=args.n,
            run_root=args.run_root,
            meta_notes=args.meta_notes
        )
        run_dir = out['run_dir']
        print(f'Run complete: {run_dir}')
        ensure_dir('reports')
        out_html = os.path.join('reports', os.path.basename(run_dir).replace('run_', 'report_') + '.html')
        render(os.path.join(run_dir, 'details.jsonl'), os.path.join(run_dir, 'summary.json'), out_html)
        print(f'Report written: {out_html}')

    elif args.cmd == 'report':
        run_dir = args.run_dir
        out_html = args.out or os.path.join('reports', os.path.basename(run_dir).replace('run_', 'report_') + '.html')
        ensure_dir(os.path.dirname(out_html))
        render(os.path.join(run_dir, 'details.jsonl'), os.path.join(run_dir, 'summary.json'), out_html)
        print(f'Report written: {out_html}')

    elif args.cmd == 'rich_report':
        paths = generate_rich_report(args.runs_root, args.out_dir, args.title)
        print(f"Rich report written: {paths['html']} and {paths['markdown']}")

if __name__ == '__main__':
    main()
