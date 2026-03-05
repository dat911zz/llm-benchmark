"""Scoring engine: code execution, keyword matching, exact match, LLM-as-Judge."""

import re
import subprocess
import sys

from llm_bench import config
from llm_bench.models import Question
from llm_bench.utils import strip_vi, strip_latex
from llm_bench.api import chat


def extract_code_block(text: str) -> str:
    """Extract the first Python code block from a response."""
    patterns = [
        r"```python\s*(.*?)```",
        r"```\s*(.*?)```",
        r"`([^`]+)`",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    # Fallback: lines that look like code
    lines = text.splitlines()
    code_lines = [l for l in lines if l.startswith("def ") or l.startswith("    ")
                  or l.startswith("return ") or "=" in l]
    return "\n".join(code_lines) if len(code_lines) >= 3 else text


def run_code(template: str, response: str) -> tuple[bool, str, str]:
    """
    Extract code from response, inject into template, execute in sandbox.
    Returns (passed, actual_output, error_message).
    """
    extracted = extract_code_block(response)
    source = template.replace("RESPONSE_CODE", extracted)
    try:
        result = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True, text=True,
            timeout=config.CODE_TIMEOUT,
            encoding="utf-8",
        )
        actual = result.stdout.strip()
        err = result.stderr.strip()
        return True, actual, err
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def _match_args(expected: dict, actual: dict) -> float:
    """Compare expected vs actual tool arguments. Returns 0.0-1.0."""
    if not expected:
        return 1.0
    matches = 0.0
    for key, exp_val in expected.items():
        act_val = actual.get(key)
        if act_val is None:
            continue
        exp_str = str(exp_val).lower().strip()
        act_str = str(act_val).lower().strip()
        if act_str == exp_str:
            matches += 1.0
        elif exp_str in act_str or act_str in exp_str:
            matches += 0.5
    return min(matches / len(expected), 1.0)


def score_tool_calls(q: "Question", tool_calls: list[dict]) -> tuple[float, str, str]:
    """
    Score tool-use questions (structural/BFCL-style — no execution).
    Returns (raw_score 0.0-1.0, method_str, notes).
    """
    # Irrelevant-tool test: no expected call, model should NOT call any tool
    if not q.expected_tool_calls and q.irrelevant_tools:
        if not tool_calls:
            return 1.0, "tool:no_call_correct", "ok"
        called = [tc["name"] for tc in tool_calls]
        return 0.0, "tool:irrelevant_called", f"should not call: {called}"

    if not q.expected_tool_calls:
        return 0.5, "no_method", "tool:no_expected_defined"

    if not tool_calls:
        return 0.0, "tool:no_calls_made", f"expected: {[e['name'] for e in q.expected_tool_calls]}"

    # Score each expected call against actual calls
    per_call: list[float] = []
    notes_parts: list[str] = []
    for exp in q.expected_tool_calls:
        exp_name = exp["name"]
        exp_args = exp.get("args", {})
        best = 0.0
        for act in tool_calls:
            if act["name"] == exp_name:
                best = max(best, _match_args(exp_args, act.get("args", {})))
        per_call.append(best)
        if best < 1.0:
            notes_parts.append(f"{exp_name}:{best:.0%}")

    raw = sum(per_call) / len(per_call)

    # Penalty: called a tool that should NOT be called
    irrelevant_called = [tc["name"] for tc in tool_calls if tc["name"] in q.irrelevant_tools]
    if irrelevant_called:
        raw *= 0.5
        notes_parts.append(f"irrelevant:{irrelevant_called}")

    method = f"tool_calls:{sum(1 for s in per_call if s > 0)}/{len(per_call)}"
    return min(raw, 1.0), method, "; ".join(notes_parts) if notes_parts else "ok"


def score_question(q: "Question", response: str,
                   tool_calls: list | None = None) -> tuple[float, str, str]:
    """
    Multi-method scoring.
    Returns (raw_score 0.0-1.0, method_used, notes).
    """
    # Method 0: Tool-call evaluation (highest priority for ToolUse questions)
    if q.tools:
        return score_tool_calls(q, tool_calls or [])

    resp_lower = response.lower()
    resp_norm = strip_vi(resp_lower)
    resp_plain = strip_latex(resp_lower)
    notes_parts: list[str] = []
    scores: list[float] = []
    methods: list[str] = []

    # Method 1: Code execution (highest priority for coding questions)
    if q.code_to_exec and q.expected_output:
        ok, actual, err = run_code(q.code_to_exec, response)
        if ok:
            expected_lines = q.expected_output.strip().splitlines()
            actual_lines = actual.strip().splitlines()
            if len(actual_lines) > len(expected_lines):
                actual = "\n".join(actual_lines[-len(expected_lines):])

            if actual == q.expected_output.strip():
                return 1.0, "code_exec:PASS", f"output={actual!r}"
            else:
                actual_nums = set(re.findall(r"-?\d+\.?\d*", actual))
                expected_nums = set(re.findall(r"-?\d+\.?\d*", q.expected_output))
                partial = len(actual_nums & expected_nums) / max(len(expected_nums), 1)
                scores.append(partial * 0.6)
                methods.append(f"code_exec:PARTIAL({partial:.0%})")
                notes_parts.append(f"expected={q.expected_output!r} got={actual!r}")
        else:
            notes_parts.append(f"exec_error: {err[:80]}")

    # Method 2: Exact numeric match
    if q.exact_numbers:
        hits = [n for n in q.exact_numbers if n in resp_lower or n in response or n in resp_plain]
        ratio = len(hits) / len(q.exact_numbers)
        scores.append(ratio)
        methods.append(f"exact_num:{len(hits)}/{len(q.exact_numbers)}")
        if ratio < 1.0:
            missing = [n for n in q.exact_numbers if n not in resp_lower and n not in response and n not in resp_plain]
            notes_parts.append(f"missing numbers: {missing}")

    # Method 3: Required keywords (ALL must match)
    if q.keywords:
        hits = [kw for kw in q.keywords if kw.lower() in resp_lower or strip_vi(kw.lower()) in resp_norm or kw.lower() in resp_plain]
        ratio = len(hits) / len(q.keywords)
        scores.append(ratio)
        methods.append(f"kw_all:{len(hits)}/{len(q.keywords)}")
        missing = [kw for kw in q.keywords if kw.lower() not in resp_lower and strip_vi(kw.lower()) not in resp_norm and kw.lower() not in resp_plain]
        if missing:
            notes_parts.append(f"missing required: {missing}")

    # Method 4: Any-keywords (at least any_min must match)
    if q.any_keywords and q.any_min > 0:
        hits = [kw for kw in q.any_keywords if kw.lower() in resp_lower or strip_vi(kw.lower()) in resp_norm or kw.lower() in resp_plain]
        n = len(hits)
        ratio = min(n / q.any_min, 1.0)
        scores.append(ratio)
        methods.append(f"kw_any:{n}/{q.any_min}")
        if n < q.any_min:
            notes_parts.append(f"any_kw hits={n} (need {q.any_min}): {hits}")

    # Aggregate
    if not scores:
        return 0.5, "no_method", "open_ended:needs_judge"

    raw = sum(scores) / len(scores)

    if q.open_ended and len(response.strip()) < 20:
        raw = max(0.0, raw - 0.4)
        notes_parts.append("response too short")

    method_str = " | ".join(methods)
    return min(raw, 1.0), method_str, "; ".join(notes_parts) if notes_parts else "ok"


def llm_judge(
    model_judge: str,
    question: Question,
    response: str,
) -> tuple[float, str]:
    """
    Use a second model as judge. Returns (raw_score 0.0-1.0, reasoning).
    """
    rubric = f"""
REFERENCE ANSWER: {question.reference}

SCORING RUBRIC (score 0-3):
3 = Completely correct, addresses all key points, no factual errors
2 = Mostly correct, minor omissions or imprecision
1 = Partially correct, major omission OR one factual error
0 = Incorrect, off-topic, or completely wrong

TASK: Evaluate the following AI response to the question.
First, write 1-2 sentences explaining your reasoning.
Then output SCORE: X (where X is 0, 1, 2, or 3).
"""
    prompt = (
        f"QUESTION: {question.prompt}\n\n"
        f"AI RESPONSE: {response}\n\n"
        f"{rubric}"
    )
    try:
        judge_response, _ = chat(
            model_judge, prompt,
            max_tokens=300, temperature=0.0,
            system="You are a strict but fair academic evaluator. Be concise.",
        )
        m = re.search(r"SCORE:\s*([0-3])", judge_response, re.IGNORECASE)
        if m:
            raw = int(m.group(1)) / 3.0
            return raw, judge_response.strip()
        return 0.5, f"could not parse score from: {judge_response[:100]}"
    except Exception as e:
        return 0.5, f"judge error: {e}"
