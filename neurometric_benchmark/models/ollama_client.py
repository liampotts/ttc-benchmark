import json, os, subprocess, urllib.request
from typing import Dict, Any, Optional

DEFAULT_BASE = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

def _http_generate(model: str, prompt: str, options: Optional[Dict[str, Any]] = None, json_mode: bool=False) -> Optional[str]:
    url = f"{DEFAULT_BASE}/api/generate"
    payload = {'model': model, 'prompt': prompt, 'stream': False}
    if options:
        payload['options'] = options
    if json_mode:
        payload['format'] = 'json'
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = resp.read().decode('utf-8')
            obj = json.loads(body)
            return obj.get('response')
    except Exception:
        return None

def _cli_generate(model: str, prompt: str) -> Optional[str]:
    try:
        out = subprocess.check_output(['ollama', 'run', model, prompt], stderr=subprocess.STDOUT, timeout=600)
        return out.decode('utf-8', errors='ignore')
    except Exception:
        return None

def generate(model: str, prompt: str, temperature: float=0.7, top_p: float=0.95, json_mode: bool=False) -> str:
    opts = {'temperature': temperature, 'top_p': top_p}
    text = _http_generate(model, prompt, options=opts, json_mode=json_mode)
    if text is not None:
        return text
    text = _cli_generate(model, prompt)
    if text is not None:
        return text
    raise RuntimeError('Failed to generate with Ollama. Is it running and is the model pulled?')
