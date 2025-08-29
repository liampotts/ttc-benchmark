import re
from typing import Tuple

def verify_regex(candidate_text: str, pattern: str) -> Tuple[bool, float, dict]:
    """Check if the candidate text matches the provided regex pattern."""
    match = re.search(pattern, candidate_text or '')
    ok = bool(match)
    meta = {'match': match.group(0) if match else None}
    return ok, (1.0 if ok else 0.0), meta
