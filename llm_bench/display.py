"""Display functions: progress bars, badges, summaries, comparisons."""

import textwrap
import time
from collections import defaultdict

from llm_bench.models import Result
from llm_bench.utils import R, G, Y, B, W, M, C, DIM, RST, BLD, DIFF_COLOR


def bar(ratio: float, width: int = 20) -> str:
    filled = round(ratio * width)
    color = G if ratio >= 0.8 else Y if ratio >= 0.5 else R
    return f"{color}{'#' * filled}{'.' * (width - filled)}{RST}"


def diff_badge(d: str) -> str:
    return f"{DIFF_COLOR[d]}[{d}]{RST}"


def lang_badge(lang: str) -> str:
    return f"{B}[EN]{RST}" if lang == "en" else f"{Y}[VI]{RST}"


def cat_badge(cat: str) -> str:
    colors = {
        "Logic": C, "Math": M, "Coding": G,
        "Knowledge": B, "Critical": Y,
        "Language": W, "Common Sense": R, "Calibration": DIM,
        "ToolUse": C,
    }
    return f"{colors.get(cat, W)}{cat}{RST}"


def print_inline(result: Result, idx: int, total: int) -> None:
    q = result.question
    pct = result.raw_score
    color = G if pct >= 0.8 else Y if pct >= 0.5 else R
    wp = result.weighted_score
    wm = result.max_weighted
    line = (
        f"{DIM}[{idx:>2}/{total}]{RST} "
        f"{q.id:<8} "
        f"{cat_badge(q.category):<22} "
        f"{lang_badge(q.lang)} "
        f"{diff_badge(q.difficulty):<14}  "
        f"{color}{wp:.0f}/{wm:.0f}{RST}  "
        f"({result.latency:.1f}s)"
        + (f"  {DIM}{result.notes[:60]}{RST}" if result.notes and result.notes != "ok" else "")
    )
    print(f"\r{line:<100}")


def print_verbose(result: Result, idx: int, total: int) -> None:
    q = result.question
    pct = result.raw_score
    color = G if pct >= 0.8 else Y if pct >= 0.5 else R

    print(f"\n{DIM}{'-'*72}{RST}")
    print(f"{BLD}[{idx}/{total}] {q.id}  {cat_badge(q.category)}  "
          f"{lang_badge(q.lang)}  {diff_badge(q.difficulty)}{RST}")
    print(f"{DIM}Q:{RST} {textwrap.shorten(q.prompt, 110)}")
    print(f"{DIM}Expected:{RST} {q.reference[:100]}")
    print()

    resp = result.response.strip()
    if len(resp) > 600:
        resp = resp[:600] + f"\n{DIM}...(truncated){RST}"
    print(f"{DIM}Response:{RST}\n{resp}")
    print()

    b = bar(pct)
    print(
        f"Score: {color}{BLD}{result.weighted_score:.0f}/{result.max_weighted:.0f}{RST}  "
        f"({pct:.0%})  {b}  "
        f"{DIM}method={result.method}  {result.latency:.1f}s{RST}"
    )
    if result.notes and result.notes != "ok":
        print(f"{DIM}Notes: {result.notes}{RST}")
    if result.judge_reasoning:
        print(f"{DIM}Judge: {result.judge_reasoning[:120]}{RST}")
    if result.tool_calls_made:
        print(f"{DIM}Tool calls made:{RST}")
        for tc in result.tool_calls_made:
            print(f"  {DIM}→ {tc['name']}({tc.get('args', {})}){RST}")


def print_summary(results: list[Result], model: str, total_time: float) -> None:
    print(f"\n\n{'='*72}")
    print(f"{BLD}{W}  INTELLIGENCE TEST REPORT{RST}")
    print(f"  Model  : {BLD}{model}{RST}")
    print(f"  Date   : {time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*72}")

    by_cat: dict[str, list[Result]] = defaultdict(list)
    by_lang: dict[str, list[Result]] = defaultdict(list)
    by_diff: dict[str, list[Result]] = defaultdict(list)

    for r in results:
        by_cat[r.question.category].append(r)
        by_lang[r.question.lang].append(r)
        by_diff[r.question.difficulty].append(r)

    # By Category
    print(f"\n{BLD}  By Category:{RST}")
    print(f"  {'Category':<18} {'Score':>10}  {'Bar':22}  {'%':>5}")
    print(f"  {'-'*60}")
    for cat in ["Logic", "Math", "Coding", "Knowledge", "Critical",
                "Language", "Common Sense", "Calibration"]:
        rs = by_cat.get(cat, [])
        if not rs:
            continue
        got = sum(r.weighted_score for r in rs)
        mx  = sum(r.max_weighted for r in rs)
        pct = got / mx if mx else 0
        col = G if pct >= 0.8 else Y if pct >= 0.5 else R
        print(f"  {cat:<18} {col}{got:>5.0f}/{mx:<4.0f}{RST}  "
              f"{bar(pct)}  {col}{pct:>4.0%}{RST}")

    # By Difficulty
    print(f"\n{BLD}  By Difficulty:{RST}")
    for d in ["Easy", "Medium", "Hard"]:
        rs = by_diff.get(d, [])
        if not rs:
            continue
        got = sum(r.weighted_score for r in rs)
        mx  = sum(r.max_weighted for r in rs)
        pct = got / mx if mx else 0
        col = G if pct >= 0.8 else Y if pct >= 0.5 else R
        print(f"  {DIFF_COLOR[d]}{d:<8}{RST}  {col}{got:>5.0f}/{mx:<4.0f}{RST}  "
              f"{bar(pct)}  {col}{pct:>4.0%}{RST}")

    # By Language
    print(f"\n{BLD}  By Language:{RST}")
    for lang_code, label in [("en", "English"), ("vi", "Vietnamese")]:
        rs = [r for r in results if r.question.lang == lang_code]
        if not rs:
            continue
        got = sum(r.weighted_score for r in rs)
        mx  = sum(r.max_weighted for r in rs)
        pct = got / mx if mx else 0
        col = G if pct >= 0.8 else Y if pct >= 0.5 else R
        print(f"  {label:<14}  {col}{got:>5.0f}/{mx:<4.0f}{RST}  "
              f"{bar(pct)}  {col}{pct:>4.0%}{RST}")

    # Overall
    total_got = sum(r.weighted_score for r in results)
    total_max = sum(r.max_weighted for r in results)
    pct_overall = total_got / total_max if total_max else 0

    grade = (
        "A+" if pct_overall >= 0.95 else
        "A"  if pct_overall >= 0.90 else
        "B+" if pct_overall >= 0.85 else
        "B"  if pct_overall >= 0.80 else
        "C+" if pct_overall >= 0.75 else
        "C"  if pct_overall >= 0.70 else
        "D"  if pct_overall >= 0.60 else "F"
    )
    col = G if pct_overall >= 0.80 else Y if pct_overall >= 0.60 else R

    avg_lat = sum(r.latency for r in results) / len(results)
    print(f"\n{'-'*72}")
    print(f"  Questions : {len(results)}  |  Time: {total_time:.0f}s  |  Avg: {avg_lat:.1f}s/q")
    print()
    print(f"  {BLD}TOTAL (weighted)  {col}{total_got:.0f} / {total_max:.0f}  "
          f"({pct_overall:.1%})   Grade: {grade}{RST}")
    print(f"  {BLD}  {bar(pct_overall, 44)}{RST}")
    print(f"{'='*72}\n")

    # Top 3 weakest
    weak = sorted(results, key=lambda r: r.raw_score)[:3]
    print(f"{BLD}  Weakest questions:{RST}")
    for r in weak:
        print(f"  {R}{r.question.id:<8}{RST}  {cat_badge(r.question.category):<22}"
              f"  {r.raw_score:.0%}  {DIM}{textwrap.shorten(r.question.prompt, 55)}{RST}")

    # Top 3 strongest
    strong = sorted(results, key=lambda r: r.raw_score, reverse=True)[:3]
    print(f"\n{BLD}  Strongest questions:{RST}")
    for r in strong:
        print(f"  {G}{r.question.id:<8}{RST}  {cat_badge(r.question.category):<22}"
              f"  {r.raw_score:.0%}  {DIM}{textwrap.shorten(r.question.prompt, 55)}{RST}")


def compare_summary(all_results: dict[str, list[Result]]) -> None:
    """Print side-by-side comparison of multiple models."""
    models = list(all_results.keys())
    print(f"\n{'='*72}")
    print(f"{BLD}{W}  MODEL COMPARISON{RST}")
    print(f"{'='*72}")

    # Gather all question IDs
    all_ids = []
    for rs in all_results.values():
        for r in rs:
            if r.question.id not in all_ids:
                all_ids.append(r.question.id)

    # Header
    header = f"  {'ID':<8}"
    for m in models:
        short = m[:18]
        header += f"  {short:<18}"
    print(header)
    print(f"  {'-'*60}")

    # Per-question
    idx_map: dict[str, dict[str, Result]] = defaultdict(dict)
    for model, rs in all_results.items():
        for r in rs:
            idx_map[r.question.id][model] = r

    for qid in all_ids:
        row = f"  {qid:<8}"
        for m in models:
            r = idx_map[qid].get(m)
            if r:
                pct = r.raw_score
                col = G if pct >= 0.8 else Y if pct >= 0.5 else R
                row += f"  {col}{pct:>6.0%}{'':12}{RST}"
            else:
                row += f"  {'N/A':>18}"
        print(row)

    # Totals
    print(f"  {'-'*60}")
    row = f"  {'TOTAL':<8}"
    for m in models:
        rs = all_results[m]
        got = sum(r.weighted_score for r in rs)
        mx  = sum(r.max_weighted for r in rs)
        pct = got / mx if mx else 0
        col = G if pct >= 0.8 else Y if pct >= 0.5 else R
        row += f"  {col}{pct:>6.0%}{'':12}{RST}"
    print(row)
