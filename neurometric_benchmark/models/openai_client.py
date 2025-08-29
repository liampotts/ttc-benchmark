# Optional: remote large model baseline (disabled by default).
# Requires: pip install openai  (and set OPENAI_API_KEY)
from typing import Dict, Any
import os

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def generate(model: str, prompt: str, temperature: float=0.2, top_p: float=0.95) -> str:
    if OpenAI is None:
        raise RuntimeError('openai package not installed. Run: pip install openai')
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY not set')
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=temperature,
        top_p=top_p
    )
    return resp.choices[0].message.content
