import json
from typing import Dict, Any, Tuple
from ..utils.text import strip_json_markers

def verify_json(candidate_text: str, gold: Dict[str, Any], required_keys=None) -> Tuple[bool, float, dict]:
    """Check if candidate JSON matches gold on required_keys (or all keys if None)."""
    s = strip_json_markers(candidate_text)
    try:
        obj = json.loads(s)
    except Exception:
        start = s.find('{'); end = s.rfind('}')
        if start != -1 and end != -1 and start < end:
            try:
                obj = json.loads(s[start:end+1])
            except Exception:
                return False, 0.0, {'error': 'json_parse_error'}
        else:
            return False, 0.0, {'error': 'json_not_found'}
    keys = required_keys or list(gold.keys())
    correct = 0; total = len(keys)
    diffs = {}
    for k in keys:
        gv = gold.get(k, None)
        cv = obj.get(k, None)
        if cv == gv:
            correct += 1
        else:
            diffs[k] = {'gold': gv, 'cand': cv}
    is_ok = (correct == total)
    return is_ok, (1.0 if is_ok else correct / max(total,1)), {'diffs': diffs, 'candidate': obj}
