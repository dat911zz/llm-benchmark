#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM Intelligence Test Suite v2.0
=================================
Entry point for CLI and interactive menu.

Usage:
  python main.py                            # interactive menu
  python main.py MODEL_ID --all -s          # all questions, save report
  python main.py MODEL_ID --all -v          # verbose: show full responses
  python main.py MODEL_ID -q               # quick: 1 per difficulty tier
  python main.py MODEL_ID --cat Math        # only Math category
  python main.py MODEL_ID --lang vi         # only Vietnamese
  python main.py MODEL_ID --judge JUDGE     # enable LLM-as-Judge scoring
  python main.py --compare A_ID B_ID --all  # compare two models
"""

import sys
import io
import time
from typing import Optional

# ── Fix Windows terminal UTF-8 ──────────────────────────────────────────────
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from llm_bench import config
from llm_bench.models import Question, Result
from llm_bench.utils import R, G, Y, M, C, DIM, RST, BLD
from llm_bench.questions import QUESTIONS
from llm_bench.api import list_models, ping_api
from llm_bench.runner import run_all
from llm_bench.display import print_summary, compare_summary
from llm_bench.report import save_report


# ── CLI Helpers ──────────────────────────────────────────────────────────────

def pick_model(hint: Optional[str]) -> str:
    if hint:
        return hint
    try:
        models = list_models()
    except Exception as e:
        print(f"{R}Cannot list models: {e}{RST}")
        return config.DEFAULT_MODEL

    print(f"\n{BLD}Available models:{RST}")
    for i, m in enumerate(models, 1):
        marker = f"  {G}<-- default{RST}" if m == config.DEFAULT_MODEL else ""
        print(f"  {i}. {m}{marker}")
    choice = input(f"\n{BLD}Select model (Enter = default):{RST} ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        return models[int(choice) - 1]
    return config.DEFAULT_MODEL


def filter_questions(qs: list[Question], args: list[str]) -> list[Question]:
    # --cat
    cats_arg = next((a for a in args if a.startswith("--cat=")), None)
    if not cats_arg:
        try:
            idx = args.index("--cat")
            cats_arg = f"--cat={args[idx+1]}"
        except (ValueError, IndexError):
            pass

    # --lang
    lang_arg = next((a for a in args if a.startswith("--lang=")), None)
    if not lang_arg:
        try:
            idx = args.index("--lang")
            lang_arg = f"--lang={args[idx+1]}"
        except (ValueError, IndexError):
            pass

    # --diff
    diff_arg = next((a for a in args if a.startswith("--diff=")), None)
    if not diff_arg:
        try:
            idx = args.index("--diff")
            diff_arg = f"--diff={args[idx+1]}"
        except (ValueError, IndexError):
            pass

    selected = qs

    if cats_arg:
        wanted = set(cats_arg.split("=", 1)[1].split(","))
        selected = [q for q in selected if q.category in wanted]

    if lang_arg:
        wanted_lang = lang_arg.split("=", 1)[1]
        selected = [q for q in selected if q.lang == wanted_lang]

    if diff_arg:
        wanted_diff = set(diff_arg.split("=", 1)[1].split(","))
        selected = [q for q in selected if q.difficulty in wanted_diff]

    return selected


def interactive_filter(qs: list[Question]) -> list[Question]:
    cats = sorted({q.category for q in qs})
    print(f"\n{BLD}Categories:{RST}")
    for i, c in enumerate(cats, 1):
        print(f"  {i}. {c}")
    cat_in = input("Filter by category numbers (e.g. 1,3) or Enter for all: ").strip()

    print(f"\n{BLD}Language:{RST}  1=English  2=Vietnamese  3=Both")
    lang_in = input("Choice (Enter for all): ").strip()

    print(f"\n{BLD}Difficulty:{RST}  1=Easy  2=Medium  3=Hard  4=All")
    diff_in = input("Choice (Enter for all): ").strip()

    selected = qs

    if cat_in:
        idxs = [int(x) - 1 for x in cat_in.split(",") if x.strip().isdigit()]
        chosen = {cats[i] for i in idxs if 0 <= i < len(cats)}
        selected = [q for q in selected if q.category in chosen]

    if lang_in == "1":
        selected = [q for q in selected if q.lang == "en"]
    elif lang_in == "2":
        selected = [q for q in selected if q.lang == "vi"]

    if diff_in == "1":
        selected = [q for q in selected if q.difficulty == "Easy"]
    elif diff_in == "2":
        selected = [q for q in selected if q.difficulty == "Medium"]
    elif diff_in == "3":
        selected = [q for q in selected if q.difficulty == "Hard"]

    return selected


def usage() -> None:
    print(f"""
{BLD}LLM Intelligence Test Suite v2.0{RST}

Usage:
  python main.py [MODEL_ID] [OPTIONS]

Endpoint & Auth Options:
  --ping             Test API connectivity and list models
  --base-url URL     Override API base URL (env: OPENAI_BASE_URL)
  --api-key KEY      API key for auth (env: OPENAI_API_KEY, empty=no auth)

Test Options:
  --all              Run all questions (skip interactive filter)
  --cat CATEGORY     Filter by category (comma-sep: Math,Logic)
  --lang LANG        Filter by language (en or vi)
  --diff DIFF        Filter by difficulty (Easy,Medium,Hard)
  -q / --quick       1 question per difficulty tier
  -v / --verbose     Show full responses
  -s / --save        Auto-save JSON report to REPORT_DIR
  --judge MODEL_ID   Enable LLM-as-Judge scoring with this model
  --compare A B      Compare two models side by side
  --list             List available models and exit

Info Options:
  -h / --help        Show this help

Examples:
  python main.py --ping                                # test connection
  python main.py                                       # interactive menu
  python main.py qwen3-4b@q4 --all -s                 # full test, save
  python main.py --base-url http://localhost:8888/v1 qwen3-4b --all
  python main.py --api-key sk-xxx qwen3-4b --all      # with auth
""")


# ── Interactive Menu ─────────────────────────────────────────────────────────

def interactive_menu() -> None:
    """Interactive menu mode when no arguments are provided."""
    while True:
        print(f"\n{BLD}{M}{'='*48}")
        print(f"   LLM Intelligence Test Suite v2.0")
        print(f"{'='*48}{RST}")
        print(f"  {G}1{RST}. Run Test (Full / Quick / Filtered)")
        print(f"  {G}2{RST}. Compare Models")
        print(f"  {G}3{RST}. Ping API")
        print(f"  {G}4{RST}. List Models")
        print(f"  {G}5{RST}. Help")
        print(f"  {R}0{RST}. Exit")
        print(f"{DIM}{'─'*48}{RST}")

        choice = input(f"{BLD}Select option:{RST} ").strip()

        if choice == "0":
            print(f"{DIM}Bye!{RST}")
            return

        elif choice == "1":
            _menu_run_test()

        elif choice == "2":
            _menu_compare()

        elif choice == "3":
            ping_api()

        elif choice == "4":
            try:
                models = list_models()
                print(f"\n{BLD}Available models:{RST}")
                for i, m in enumerate(models, 1):
                    marker = f"  {G}<-- default{RST}" if m == config.DEFAULT_MODEL else ""
                    print(f"  {i}. {m}{marker}")
            except Exception as e:
                print(f"{R}Error: {e}{RST}")

        elif choice == "5":
            usage()

        else:
            print(f"{Y}Invalid option. Try again.{RST}")


def _menu_run_test() -> None:
    """Interactive test run from menu."""
    model = pick_model(None)
    qs = interactive_filter(QUESTIONS)

    if not qs:
        print(f"{R}No questions selected.{RST}")
        return

    # Quick mode?
    print(f"\n{BLD}Mode:{RST}  1=All selected  2=Quick (1 per difficulty)")
    mode_in = input("Choice (Enter for all): ").strip()
    if mode_in == "2":
        seen_diff: set[str] = set()
        filtered = []
        for q in qs:
            if q.difficulty not in seen_diff:
                filtered.append(q)
                seen_diff.add(q.difficulty)
        qs = filtered
        print(f"{Y}Quick mode: {len(qs)} questions{RST}")

    # Verbose?
    verbose_in = input(f"{BLD}Verbose output? [y/N]:{RST} ").strip().lower()
    verbose = verbose_in == "y"

    # Judge?
    judge_in = input(f"{BLD}LLM-as-Judge model (Enter to skip):{RST} ").strip()
    judge_model = judge_in if judge_in else None

    print(f"\n  Model   : {BLD}{model}{RST}")
    print(f"  Judge   : {judge_model or 'disabled'}")
    print(f"  Verbose : {verbose}")
    print(f"  Questions selected: {len(qs)}")

    t0 = time.time()
    results = run_all(model, qs, verbose=verbose, judge_model=judge_model)
    total_time = time.time() - t0

    print_summary(results, model, total_time)

    save_in = input(f"\n{BLD}Save JSON report? [y/N]:{RST} ").strip().lower()
    if save_in == "y":
        save_report(results, model)


def _menu_compare() -> None:
    """Interactive compare mode from menu."""
    print(f"\n{BLD}Select Model A:{RST}")
    model_a = pick_model(None)
    print(f"\n{BLD}Select Model B:{RST}")
    model_b = pick_model(None)

    qs = QUESTIONS
    all_results: dict[str, list[Result]] = {}
    for m in [model_a, model_b]:
        t0 = time.time()
        res = run_all(m, qs, verbose=False, judge_model=None)
        total_time = time.time() - t0
        print_summary(res, m, total_time)
        all_results[m] = res
    compare_summary(all_results)


# ── Main CLI ─────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]

    # No args → interactive menu
    if not args:
        interactive_menu()
        return

    if "-h" in args or "--help" in args:
        usage()
        return

    # Parse endpoint & auth flags (can override env vars)
    if "--base-url" in args:
        try:
            idx = args.index("--base-url")
            config.API_BASE_URL = args[idx + 1]
        except (ValueError, IndexError):
            pass

    if "--api-key" in args:
        try:
            idx = args.index("--api-key")
            config.API_KEY = args[idx + 1]
        except (ValueError, IndexError):
            pass

    # --ping: test connectivity only
    if "--ping" in args:
        success = ping_api()
        sys.exit(0 if success else 1)

    if "--list" in args:
        try:
            for m in list_models():
                print(m)
        except Exception as e:
            print(f"{R}{e}{RST}")
        return

    # Banner
    print(f"\n{BLD}{M}{'='*72}")
    print("  LLM Intelligence Test Suite  v2.0")
    print(f"  {len(QUESTIONS)} questions | 8 categories | 3 difficulty tiers | EN + VI")
    print(f"  Scoring: keyword + exact-match + code-execution + optional LLM-judge")
    print(f"  Weighted: Easy=1x  Medium=2x  Hard=3x")
    print(f"{'='*72}{RST}")

    # Compare mode
    if "--compare" in args:
        idx = args.index("--compare")
        model_a = args[idx + 1] if idx + 1 < len(args) else pick_model(None)
        model_b = args[idx + 2] if idx + 2 < len(args) else pick_model(None)
        qs = QUESTIONS
        all_results: dict[str, list[Result]] = {}
        for m in [model_a, model_b]:
            t0 = time.time()
            res = run_all(m, qs, verbose=False, judge_model=None)
            total_time = time.time() - t0
            print_summary(res, m, total_time)
            all_results[m] = res
        compare_summary(all_results)
        return

    # Single model
    model_arg = next((a for a in args if not a.startswith("-")), None)
    model = pick_model(model_arg)

    verbose   = "-v" in args or "--verbose" in args
    quick     = "-q" in args or "--quick" in args
    save      = "-s" in args or "--save" in args
    no_filter = "--all" in args

    judge_model: Optional[str] = None
    if "--judge" in args:
        idx = args.index("--judge")
        if idx + 1 < len(args):
            judge_model = args[idx + 1]

    # Select questions
    if no_filter:
        qs = filter_questions(QUESTIONS, args)
    else:
        qs = interactive_filter(QUESTIONS)

    # Quick mode: 1 per difficulty
    if quick:
        seen_diff: set[str] = set()
        filtered = []
        for q in qs:
            if q.difficulty not in seen_diff:
                filtered.append(q)
                seen_diff.add(q.difficulty)
        qs = filtered
        print(f"{Y}Quick mode: {len(qs)} questions{RST}")

    if not qs:
        print(f"{R}No questions selected.{RST}")
        return

    if judge_model:
        print(f"{M}LLM-as-Judge enabled: {judge_model}{RST}")

    print(f"\n  Model   : {BLD}{model}{RST}")
    print(f"  Judge   : {judge_model or 'disabled'}")
    print(f"  Verbose : {verbose}  |  Save: {save}")
    print(f"  Questions selected: {len(qs)}")
    print()

    t0 = time.time()
    results = run_all(model, qs, verbose=verbose, judge_model=judge_model)
    total_time = time.time() - t0

    print_summary(results, model, total_time)

    if save:
        save_report(results, model)
    elif sys.stdin.isatty():
        ans = input(f"\n{BLD}Save JSON report? [y/N]:{RST} ").strip().lower()
        if ans == "y":
            save_report(results, model)


if __name__ == "__main__":
    main()
