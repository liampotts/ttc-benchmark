# Neurometric TTC Benchmark — 1B + Verifier vs. Scale (Starter)

Local‑first benchmark to test the thesis that small models + test‑time compute (TTC)
(e.g., best‑of‑N sampling + verifier‑based reranking) can rival much larger models on
the right tasks. Uses Ollama locally so you can run a ~1B model on your machine.

## Quick Start

1) Install Ollama (macOS/Win/Linux): https://ollama.com/download

2) Pull a small local model (choose one):

```bash
ollama pull llama3.2:1b
# or
ollama pull qwen2.5:1.5b-instruct
```

3) Run the math benchmark (best‑of‑5):

```bash
python3 -m neurometric_benchmark.main run \
  --task tasks/math/basic.jsonl \
  --model ollama/qwen2.5:1.5b-instruct \
  --strategy best_of_n --n 5 --temperature 0.8
```

4) Open the generated report (path is printed), or re‑render later:

```bash
python3 -m neurometric_benchmark.main report --run-dir runs/<your_run_dir>
```

5) Generate a rich report with charts across runs:

```bash
python3 -m neurometric_benchmark.main rich_report --runs-root runs --out-dir reports
```

Makefile shortcuts are available:

```bash
make pull-qwen          # pull qwen2.5:1.5b-instruct
make run-math-qwen      # run math best‑of‑5 with Qwen
make report-latest      # render a report for the most recent run
```

## What's Included

- Tasks:
  - `tasks/math/basic.jsonl` — numeric problems with programmatic verifier.
  - `tasks/math/gsm8k.jsonl` — grade-school math word problems.
  - `tasks/logic/basic.jsonl` — logic puzzles with exact answers.
  - `tasks/code/basic.jsonl` — tiny Python functions checked by unit tests.
  - `tasks/extraction/structured.jsonl` — JSON extraction with schema validation.
  - `tasks/extraction/messy.jsonl` — noisy real-world text (invoices, resumes, etc.).
- Strategies:
  - `single` — single‑shot baseline.
  - `best_of_n` — sample N candidates and choose with verifier (score + tie‑break).
- Model adapters:
  - `ollama` — local via HTTP with CLI fallback.
  - `openai` — optional stub for a remote baseline (not required).
- Artifacts:
  - `runs/run_*/run_config.json` — configuration & environment.
  - `runs/run_*/details.jsonl` — per‑task records.
  - `runs/run_*/summary.json` — metrics (incl. cost & latency).
  - `reports/report_*.html` — per‑run summary.
  - `reports/rich_report.*` — Markdown/HTML with charts across runs.

## Requirements

- Python 3.8+ (standard library only for core features).
- Ollama running locally for the `ollama/*` models.
- Optional: `openai` Python package and `OPENAI_API_KEY` for remote baseline.

## Usage Examples

- Run JSON extraction with verifier:

```bash
python3 -m neurometric_benchmark.main run \
  --task tasks/extraction/structured.jsonl \
  --model ollama/qwen2.5:1.5b-instruct \
  --strategy best_of_n --n 5 --temperature 0.6
```

- Re‑render a specific run into HTML:

```bash
python3 -m neurometric_benchmark.main report --run-dir runs/run_20240101_123456
```

## Notes

- Pure standard library; no external dependencies required for core features.
- Programmatic verifiers mean you don't need an LLM‑as‑judge locally.
- To try a remote "big model" baseline, fill `neurometric_benchmark/models/openai_client.py` and set `OPENAI_API_KEY`.

## Troubleshooting

- Ollama connection errors: ensure Ollama is running and the model is pulled.
  - Default base URL is `http://localhost:11434` (override with `OLLAMA_BASE_URL`).
- Empty/invalid JSON in extraction tasks: lower temperature or increase `--n`.

## Roadmap Ideas

- Self‑consistency aggregator (majority vote across normalized answers).
- Fallback policies and budget mode (optimize N under latency/token caps).
- Richer reports (latency distributions, per‑task breakdowns, charts).

---

MIT License
