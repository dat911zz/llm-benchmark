"""Report generation: JSON serialization and saving."""

import json
import os
import time
from collections import defaultdict

from llm_bench import config
from llm_bench.models import Result
from llm_bench.utils import G, RST


def save_report(results: list[Result], model: str) -> str:
    os.makedirs(config.REPORT_DIR, exist_ok=True)

    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(config.REPORT_DIR, f"report_{ts}.json")
    total_got = sum(r.weighted_score for r in results)
    total_max = sum(r.max_weighted for r in results)
    data = {
        "version": "2.0",
        "model": model,
        "timestamp": ts,
        "summary": {
            "total_weighted_score": round(total_got, 1),
            "total_weighted_max": round(total_max, 1),
            "percentage": round(total_got / total_max * 100, 1) if total_max else 0,
            "questions": len(results),
            "avg_latency_s": round(sum(r.latency for r in results) / len(results), 2),
        },
        "by_category": {},
        "by_language": {},
        "by_difficulty": {},
        "results": [],
    }
    # Aggregates
    for dim, key_fn in [
        ("by_category", lambda r: r.question.category),
        ("by_language", lambda r: r.question.lang),
        ("by_difficulty", lambda r: r.question.difficulty),
    ]:
        groups: dict[str, list[Result]] = defaultdict(list)
        for r in results:
            groups[key_fn(r)].append(r)
        for k, rs in groups.items():
            got = sum(r.weighted_score for r in rs)
            mx  = sum(r.max_weighted for r in rs)
            data[dim][k] = {
                "score": round(got, 1),
                "max": round(mx, 1),
                "pct": round(got / mx * 100, 1) if mx else 0,
            }
    # Per-question
    for r in results:
        data["results"].append({
            "id": r.question.id,
            "category": r.question.category,
            "lang": r.question.lang,
            "difficulty": r.question.difficulty,
            "raw_score": round(r.raw_score, 3),
            "weighted_score": round(r.weighted_score, 1),
            "max_weighted": r.max_weighted,
            "method": r.method,
            "latency_s": round(r.latency, 2),
            "notes": r.notes,
            "judge_reasoning": r.judge_reasoning,
            "tool_calls_made": r.tool_calls_made,
            "prompt": r.question.prompt,
            "reference": r.question.reference,
            "response": r.response,
        })

    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{G}Report saved: {fname}{RST}")
    return fname
