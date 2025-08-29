from typing import Tuple
from ..utils.text import extract_first_number

def verify_numeric(candidate_text: str, gold: float, tol: float = 1e-6) -> Tuple[bool, float, dict]:
    """Return (is_correct, score, meta). score=1 for correct, else 0. meta includes parsed value and abs error."""
    val = extract_first_number(candidate_text)
    if val is None:
        return False, 0.0, {'parsed': None, 'abs_error': None}
    err = abs(val - gold)
    ok = err <= tol
    return ok, (1.0 if ok else 0.0), {'parsed': val, 'abs_error': err}
