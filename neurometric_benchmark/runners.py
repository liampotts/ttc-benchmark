import os, json, time
from typing import Dict, Any, List, Tuple
from .utils.logging import ensure_dir, append_jsonl, save_json, new_run_dir
from .verifiers.numeric import verify_numeric
from .verifiers.json_schema import verify_json
from .verifiers.regex import verify_regex

def load_tasks(path: str) -> List[Dict[str, Any]]:
    tasks = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            tasks.append(json.loads(line))
    return tasks

def normalize_answer(task: Dict[str, Any], text: str) -> Tuple[bool, float, Dict[str, Any]]:
    # Support either legacy single-type tasks or new verifier chains
    if 'verifiers' in task:
        overall = {}
        for v in task['verifiers']:
            vtype = v.get('type')
            if vtype == 'numeric':
                ok, score, meta = verify_numeric(text, float(v['answer']), tol=float(v.get('tol', 1e-6)))
            elif vtype == 'json':
                ok, score, meta = verify_json(text, v['answer'], required_keys=v.get('required_keys'))
            elif vtype == 'regex':
                ok, score, meta = verify_regex(text, v['pattern'])
            else:
                ok, score, meta = False, 0.0, {'error': f'unknown_verifier_{vtype}'}
            overall[vtype] = meta
            if not ok:
                return False, 0.0, overall
        return True, 1.0, overall
    else:
        ttype = task.get('type')
        if ttype == 'numeric':
            return verify_numeric(text, float(task['answer']), tol=float(task.get('tol', 1e-6)))
        elif ttype == 'json':
            return verify_json(text, task['answer'], required_keys=task.get('required_keys'))
        else:
            ok = (text.strip() == str(task['answer']).strip())
            return ok, (1.0 if ok else 0.0), {}

def build_prompt(task: Dict[str, Any]) -> str:
    ttype = task.get('type')
    if ttype == 'numeric':
        return (
            "You are a careful math assistant. Solve the problem step by step.\n"
            "Then output ONLY the final numeric answer on its own line.\n\n"
            f"Problem: {task['prompt']}\n\nFinal answer: "
        )
    elif ttype == 'json':
        schema_hint = json.dumps(task.get('schema', {}), ensure_ascii=False)
        return (
            "Extract the requested fields and reply ONLY with a JSON object matching this schema.\n"
            f"Schema (keys and types): {schema_hint}\n\n"
            f"Text: {task['prompt']}\n\nJSON: "
        )
    else:
        return task['prompt']

def run_single(model_generate, model_name: str, task: Dict[str, Any], temperature: float) -> Dict[str, Any]:
    prompt = build_prompt(task)
    text = model_generate(model_name, prompt, temperature=temperature)
    ok, score, meta = normalize_answer(task, text)
    return {'text': text, 'ok': ok, 'score': score, 'meta': meta}

def run_best_of_n(model_generate, model_name: str, task: Dict[str, Any], temperature: float, n: int) -> Dict[str, Any]:
    prompt = build_prompt(task)
    cands = []
    for _ in range(n):
        text = model_generate(model_name, prompt, temperature=temperature)
        ok, score, meta = normalize_answer(task, text)
        if task.get('type') == 'numeric':
            dist = abs(meta.get('abs_error', 1e9)) if meta else 1e9
        else:
            dist = 1.0 - float(score)
        cands.append({'text': text, 'ok': ok, 'score': score, 'dist': dist, 'meta': meta})
    cands.sort(key=lambda x: (-x['score'], x['dist']))
    best = cands[0]
    best['all_candidates'] = cands
    return best

def _canonicalize(task: Dict[str, Any], text: str, meta: Dict[str, Any]) -> str:
    ttype = task.get('type')
    if ttype == 'numeric':
        return str(meta.get('parsed'))
    elif ttype == 'json':
        try:
            return json.dumps(meta.get('candidate'), sort_keys=True)
        except Exception:
            return None
    else:
        return text.strip()

def run_self_consistency(model_generate, model_name: str, task: Dict[str, Any], temperature: float, n: int) -> Dict[str, Any]:
    prompt = build_prompt(task)
    cands = []
    counts = {}
    for _ in range(n):
        text = model_generate(model_name, prompt, temperature=temperature)
        ok, score, meta = normalize_answer(task, text)
        canon = _canonicalize(task, text, meta)
        cands.append({'text': text, 'ok': ok, 'score': score, 'meta': meta, 'canon': canon})
        counts[canon] = counts.get(canon, 0) + 1
    if counts:
        majority = max(counts.items(), key=lambda x: x[1])[0]
        majority_cands = [c for c in cands if c['canon'] == majority]
        majority_cands.sort(key=lambda x: (-x['score']))
        best = majority_cands[0]
    else:
        best = cands[0]
    best['all_candidates'] = cands
    return best

def _resolve_model_generate(backend: str):
    if backend == 'ollama':
        from .models.ollama_client import generate as model_generate
    elif backend == 'openai':
        from .models.openai_client import generate as model_generate
    else:
        raise ValueError('Unknown model backend: ' + backend)
    return model_generate

def run_with_fallback(model_specs: List[Tuple[str, str]], task: Dict[str, Any], strategy: str, temperature: float, n: int) -> Dict[str, Any]:
    last_out = None
    for backend, name in model_specs:
        model_generate = _resolve_model_generate(backend)
        if strategy == 'self_consistency':
            out = run_self_consistency(model_generate, name, task, temperature, n)
        elif strategy == 'best_of_n':
            out = run_best_of_n(model_generate, name, task, temperature, n)
        else:
            out = run_single(model_generate, name, task, temperature)
        out['model_used'] = f'{backend}/{name}'
        last_out = out
        if out['ok']:
            return out
    return last_out

def evaluate(task_path: str, model_backend: str, model_name: str, strategy: str, temperature: float, n: int=1, run_root: str='runs', meta_notes: str='', fallback_models: List[Tuple[str, str]] = None) -> Dict[str, Any]:
    tasks = load_tasks(task_path)
    run_dir = new_run_dir(run_root)
    ensure_dir(run_dir)
    details_path = os.path.join(run_dir, 'details.jsonl')
    results = []
    start = time.time()
    base_spec = (model_backend, model_name)
    model_specs = [base_spec] + (fallback_models or [])

    if fallback_models:
        for idx, t in enumerate(tasks, 1):
            out = run_with_fallback(model_specs, t, strategy, temperature, n)
            rec = {
                'task_id': t.get('id', f'item_{idx}'),
                'type': t.get('type'),
                'ok': out['ok'],
                'score': out['score'],
                'meta': out.get('meta', {}),
                'text': out.get('text', ''),
                'strategy': strategy,
                'n': n,
                'model_used': out.get('model_used')
            }
            results.append(rec)
            append_jsonl(details_path, rec)
    else:
        if model_backend == 'ollama':
            from .models.ollama_client import generate as model_generate
        elif model_backend == 'openai':
            from .models.openai_client import generate as model_generate
        else:
            raise ValueError('Unknown model backend: ' + model_backend)
        for idx, t in enumerate(tasks, 1):
            if strategy == 'single':
                out = run_single(model_generate, model_name, t, temperature)
            elif strategy == 'best_of_n':
                out = run_best_of_n(model_generate, model_name, t, temperature, n)
            elif strategy == 'self_consistency':
                out = run_self_consistency(model_generate, model_name, t, temperature, n)
            else:
                raise ValueError('Unknown strategy: ' + strategy)
            rec = {
                'task_id': t.get('id', f'item_{idx}'),
                'type': t.get('type'),
                'ok': out['ok'],
                'score': out['score'],
                'meta': out.get('meta', {}),
                'text': out.get('text', ''),
                'strategy': strategy,
                'n': n,
                'model_used': f'{model_backend}/{model_name}'
            }
            results.append(rec)
            append_jsonl(details_path, rec)

    end = time.time()
    acc = sum(1 for r in results if r['ok']) / max(len(results), 1)
    summary = {
        'task_path': task_path,
        'num_tasks': len(results),
        'accuracy': acc,
        'strategy': strategy,
        'n': n,
        'temperature': temperature,
        'model_backend': model_backend,
        'model_name': model_name,
        'duration_sec': end - start,
        'meta_notes': meta_notes,
        'fallback_models': [f"{b}/{n}" for b, n in (fallback_models or [])]
    }
    save_json(os.path.join(run_dir, 'summary.json'), summary)
    save_json(os.path.join(run_dir, 'run_config.json'), {
        'task_path': task_path,
        'model_backend': model_backend,
        'model_name': model_name,
        'strategy': strategy,
        'n': n,
        'temperature': temperature,
        'meta_notes': meta_notes,
        'fallback_models': [f"{b}/{n}" for b, n in (fallback_models or [])]
    })
    return {'run_dir': run_dir, 'summary': summary}
