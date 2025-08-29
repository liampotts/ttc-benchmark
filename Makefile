.PHONY: pull-llama pull-qwen run-math-llama run-math-qwen report-latest

pull-llama:
	ollama pull llama3.2:1b-instruct

pull-qwen:
	ollama pull qwen2.5:1.5b-instruct

run-math-llama:
	python3 -m neurometric_benchmark.main run \
	  --task tasks/math/basic.jsonl \
	  --model ollama/llama3.2:1b-instruct \
	  --strategy best_of_n --n 5 --temperature 0.8

run-math-qwen:
	python3 -m neurometric_benchmark.main run \
	  --task tasks/math/basic.jsonl \
	  --model ollama/qwen2.5:1.5b-instruct \
	  --strategy best_of_n --n 5 --temperature 0.8

report-latest:
	LATEST=$$(ls -dt runs/run_* | head -1) && \
	python3 -m neurometric_benchmark.main report --run-dir "$$LATEST"
	@echo "Report written under reports/. Open the newest HTML file."
