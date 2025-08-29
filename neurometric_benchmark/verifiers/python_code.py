from typing import List, Dict, Any, Tuple


def verify_python(candidate_text: str, fn_name: str, tests: List[Dict[str, Any]]) -> Tuple[bool, float, dict]:
    """Execute candidate Python code and run unit tests."""
    env: Dict[str, Any] = {}
    try:
        exec(candidate_text, env)
    except Exception as e:
        return False, 0.0, {"error": "exec_error", "detail": str(e)}
    func = env.get(fn_name)
    if not callable(func):
        return False, 0.0, {"error": "function_not_found"}
    passed = 0
    diffs = []
    for t in tests:
        args = t.get("input", [])
        expected = t.get("output")
        try:
            result = func(*args)
        except Exception as e:
            return False, 0.0, {"error": "runtime_error", "detail": str(e)}
        if result == expected:
            passed += 1
        else:
            diffs.append({"input": args, "expected": expected, "got": result})
    is_ok = passed == len(tests)
    score = 1.0 if is_ok else passed / max(len(tests), 1)
    return is_ok, score, {"diffs": diffs}
