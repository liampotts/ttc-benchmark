import re
from typing import Optional

NUM_REGEX = re.compile(r"-?\d+(?:\.\d+)?")

def extract_first_number(text: str) -> Optional[float]:
    if text is None:
        return None
    t = text.replace(',', '')
    m = NUM_REGEX.search(t)
    if not m:
        return None
    try:
        return float(m.group(0))
    except Exception:
        return None

def strip_json_markers(s: str) -> str:
    if s is None:
        return s
    s = s.strip()
    if s.startswith('```'):
        s = s.strip('`').strip()
        if s.lower().startswith('json'):
            s = s[4:].strip()
    return s
