# Optional: remote large model baseline (disabled by default).
# Requires: pip install openai  (and set OPENAI_API_KEY)
from typing import Dict, Any
import os

# Rough per-token pricing for a couple of common OpenAI models. Prices are in
# USD per token and are only used to provide a ballpark cost estimate in the
# generated reports. The values can be updated as OpenAI pricing changes.
MODEL_PRICES: Dict[str, Any] = {
    # (input_cost_per_token, output_cost_per_token)
    "gpt-4o": (5 / 1_000_000, 15 / 1_000_000),
    "gpt-4o-mini": (0.15 / 1_000_000, 0.60 / 1_000_000),
}

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def generate(model: str, prompt: str, temperature: float = 0.2, top_p: float = 0.95) -> Dict[str, Any]:
    """Generate text from an OpenAI chat model.

    Returns a dictionary containing the text and an estimated cost in USD so
    that downstream code can aggregate token spend. The cost is a best-effort
    estimate based on the rough model prices above. If pricing information for
    the requested model is unknown, cost will be reported as zero.
    """
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
        top_p=top_p,
    )

    text = resp.choices[0].message.content
    usage = getattr(resp, 'usage', None)
    cost = 0.0
    prompt_tokens = 0
    completion_tokens = 0
    if usage:
        prompt_tokens = getattr(usage, 'prompt_tokens', 0)
        completion_tokens = getattr(usage, 'completion_tokens', 0)
        in_cost, out_cost = MODEL_PRICES.get(model, (0.0, 0.0))
        cost = prompt_tokens * in_cost + completion_tokens * out_cost

    return {
        'text': text,
        'cost_usd': cost,
        'input_tokens': prompt_tokens,
        'output_tokens': completion_tokens,
    }
