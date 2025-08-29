# Neurometric TTC Benchmark — 1B + Verifier vs. Scale (Starter)

Local‑first benchmark to test the thesis that **small models + test‑time compute (TTC)**
(e.g., best‑of‑N sampling + verifier‑based reranking) can rival much larger models on
the *right* tasks. Uses **Ollama** locally so you can run a ~1B model on your machine.

## Quick Start

1) Install **Ollama** (macOS/Win/Linux): https://ollama.com/download

2) Pull a small local model (choose one):
```bash
ollama pull llama3.2:1b-instruct
# or
ollama pull qwen2.5:1.5b-instruct
1. Run the math benchmark (best‑of‑5):
python -m neurometric_benchmark.main run \
  --task tasks/math/basic.jsonl \
  --model ollama/llama3.2:1b-instruct \
 --strategy best_of_n --n 5 --temperature 0.8
1. Open the report printed by the command, or re‑render later:
python -m neurometric_benchmark.main report --run-dir runs/<your_run_dir>
1. Generate a rich report with charts across runs:
python -m neurometric_benchmark.main rich_report --runs-root runs --out-dir reports
What’s Included
* Task sets:
    * tasks/math/basic.jsonl — numeric problems with programmatic verifiers
    * tasks/extraction/structured.jsonl — JSON extraction with schema validation
* Strategies:
    * single: single‑shot baseline
    * best_of_n: sample N candidates and choose by verifier (score + tie‑break)
* Model adapters:
    * ollama: local via HTTP with CLI fallback
    * openai: optional stub for remote baseline (not required)
* Artifacts:
    * runs/run_*/run_config.json — configuration & environment
    * runs/run_*/details.jsonl — per‑task records
    * runs/run_*/summary.json — metrics (incl. cost & latency)
    * reports/report_*.html — per‑run summary
    * reports/rich_report.* — Markdown/HTML with charts across runs
Notes
* Pure standard library; no external deps for core features.
* Programmatic verifiers mean you don’t need an LLM‑as‑judge locally.
* To try a remote “big model” baseline, fill models/openai_client.py and set OPENAI_API_KEY.
Roadmap Ideas
* Self‑consistency aggregator (majority vote across normalized answers).
* Fallback policies and budget mode (optimize N under latency/token caps).
* Richer reports (latency distributions, per‑task breakdowns, charts).
MIT License.
