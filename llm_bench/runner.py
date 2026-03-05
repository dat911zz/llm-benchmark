"""Main evaluation runner."""

from typing import Optional

from llm_bench import config
from llm_bench.models import Question, Result
from llm_bench.utils import R, G, Y, C, DIM, RST, BLD
from llm_bench.api import chat, chat_with_tools
from llm_bench.scoring import score_question, llm_judge
from llm_bench.display import print_inline, print_verbose


def run_all(
    model: str,
    questions: list[Question],
    verbose: bool = False,
    judge_model: Optional[str] = None,
) -> list[Result]:
    results: list[Result] = []
    total = len(questions)
    system = (
        "You are an AI being rigorously tested for intelligence. "
        "Answer accurately and concisely. "
        "For Vietnamese questions, respond in Vietnamese. "
        "For English questions, respond in English. "
        "Show your reasoning when asked."
    )

    print(f"\n{BLD}{C}Running {total} questions on:{RST} {model}\n")

    for i, q in enumerate(questions, 1):
        cat_short = q.category[:7]
        print(f"\r{DIM}[{i:>2}/{total}]{RST} {q.id:<8} {Y}{cat_short:<8}{RST} → {DIM}sending...{RST}", end="", flush=True)

        try:
            if q.tools:
                response, tool_calls, latency = chat_with_tools(
                    model, q.prompt, q.tools, q.max_tokens, q.temperature, system=system
                )
            else:
                response, latency = chat(
                    model, q.prompt, q.max_tokens, q.temperature, system=system
                )
                tool_calls = []
        except Exception as e:
            print(f"{R}[{i}/{total}] {q.id} ERROR: {e}{RST}")
            w = config.DIFF_WEIGHT[q.difficulty] * q.base_points
            results.append(Result(
                question=q, response="", raw_score=0.0,
                weighted_score=0.0, max_weighted=float(w),
                method="error", latency=0.0, notes=str(e),
            ))
            continue

        raw, method, notes = score_question(q, response, tool_calls=tool_calls)

        # LLM-as-Judge for open-ended or when judge is available
        judge_reasoning = ""
        if judge_model and (q.open_ended or raw < 0.5):
            j_score, j_reason = llm_judge(judge_model, q, response)
            if q.open_ended:
                raw = j_score
                method = f"llm_judge | {method}"
            else:
                raw = 0.6 * raw + 0.4 * j_score
                method = f"blend | {method}"
            judge_reasoning = j_reason

        weight = config.DIFF_WEIGHT[q.difficulty]
        weighted = raw * weight * q.base_points
        max_w    = weight * q.base_points

        result = Result(
            question=q, response=response,
            raw_score=raw, weighted_score=weighted, max_weighted=float(max_w),
            method=method, latency=latency, notes=notes,
            judge_reasoning=judge_reasoning,
            tool_calls_made=tool_calls,
        )
        results.append(result)

        if verbose:
            print_verbose(result, i, total)
        else:
            print_inline(result, i, total)

    return results
