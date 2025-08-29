import os, json, datetime
from typing import Dict, Any

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def new_run_dir(root: str = 'runs') -> str:
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    d = os.path.join(root, f'run_{ts}')
    ensure_dir(d)
    return d

def save_json(path: str, data: Dict[str, Any]):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_jsonl(path: str, record: Dict[str, Any]):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
