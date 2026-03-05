# CLAUDE.md - Project Context & Development Guide

## Project Overview

**LLM Intelligence Test Suite v2.0**

A comprehensive LLM evaluation benchmark tool for assessing language model capabilities across multiple dimensions (logic, math, coding, knowledge, critical thinking, language fluency, common sense).

**Key characteristics:**
- Modular Python package (`llm_bench/`) with `main.py` entry point
- Zero external dependencies (stdlib only, Python 3.10+)
- Bilingual: English + Vietnamese questions
- OpenAI-compatible API (works with LM Studio, Ollama, OpenAI, Dashscope, etc.)
- Multi-method scoring: keyword matching, exact match, code execution, LLM-as-Judge
- Generates JSON reports with per-category and per-language breakdown
- Includes comparison mode for A/B testing models
- Interactive CLI menu for easy CI/CD integration

---

## Repository Structure

```
llm-benchmark/
├── main.py                    # Entry point (CLI + interactive menu)
├── llm_bench/                 # Core package
│   ├── __init__.py            # Package init + version
│   ├── config.py              # Environment variables, API endpoints, timeouts
│   ├── utils.py               # ANSI colors, strip_vi(), strip_latex()
│   ├── models.py              # Question & Result dataclasses
│   ├── questions.py           # 45 hardcoded questions (8 categories)
│   ├── api.py                 # API client: api_post, chat, ping, list_models
│   ├── scoring.py             # score_question, extract_code, run_code, llm_judge
│   ├── display.py             # bar, badges, print_summary, compare_summary
│   ├── runner.py              # run_all - main evaluation loop
│   └── report.py              # save_report - JSON serialization
├── test_model.py              # Legacy entry point (kept for compatibility)
├── README.md                  # English documentation
├── CLAUDE.md                  # AI assistant context (this file)
├── .env.example               # Template for configuration (copy to .env)
├── .gitignore                 # Git ignore rules
├── docs/
│   ├── README.vi.md           # Vietnamese documentation
│   └── assets/
│       └── output-example.png # Example output screenshot
└── reports/                   # (ignored by git) Generated JSON reports
```

---

## Core Architecture

### Module Breakdown

| Module | Purpose |
|--------|---------|
| `config.py` | Global config from env vars: API_BASE_URL, API_KEY, DEFAULT_MODEL, timeouts, DIFF_WEIGHT |
| `utils.py` | ANSI color constants, DIFF_COLOR mapping, `strip_vi()`, `strip_latex()` |
| `models.py` | `Question` and `Result` dataclasses |
| `questions.py` | `QUESTIONS` list (45 questions across 8 categories), deduplication |
| `api.py` | `api_post()`, `list_models()`, `ping_api()`, `chat()` |
| `scoring.py` | `extract_code_block()`, `run_code()`, `score_question()`, `llm_judge()` |
| `display.py` | `bar()`, badges, `print_inline()`, `print_verbose()`, `print_summary()`, `compare_summary()` |
| `runner.py` | `run_all()` - main evaluation loop |
| `report.py` | `save_report()` - JSON serialization |
| `main.py` | CLI argument parsing, interactive menu, `pick_model()`, filters |

### Module Dependencies

```
config.py ──┐
utils.py  ──┤
models.py ──┼── api.py ──┐
            │            ├── scoring.py ──┐
            │            │                ├── runner.py ──┐
            ├── display.py ───────────────┘               │
            │                                             ├── main.py
            ├── questions.py ─────────────────────────────┘
            └── report.py ────────────────────────────────┘
```

### Question Categories (8 total, 45 questions)

- **Logic** (7): Zebra puzzle, riddles, syllogisms
- **Math** (7): GSM8K-style word problems, algebra, geometry
- **Coding** (7): Python write/debug/explain, DP problems
- **Knowledge** (6): Science, history, geography (EN+VI)
- **Critical Thinking** (6): Bias detection, Fermi estimation, fallacies
- **Language** (5): Vietnamese proverbs, grammar, register shifts
- **Common Sense** (4): HellaSwag-style continuations, situational reasoning
- **Calibration** (3): Epistemic uncertainty, confidence self-assessment

### Scoring System

Priority order (first match wins):
1. **Code execution** (5s sandbox timeout) - extracts Python, runs it, checks stdout
2. **Exact/numeric match** - specific numbers/strings in response
3. **Required keywords (ALL must match)** - case-insensitive, fuzzy Vietnamese
4. **Optional keywords (N of M)** - at least `any_min` must appear

**Weighted score formula:**
```
raw_score × difficulty_weight × 10 = question_score
(Easy=1x, Medium=2x, Hard=3x, base=10 points)
```

---

## Configuration

### Environment Variables (set in `.env` or export)

```bash
OPENAI_BASE_URL    # API endpoint (default: http://localhost:1234/v1)
OPENAI_API_KEY     # API key (optional, leave empty for local)
OPENAI_MODEL       # Model ID (default: your-model-id)
API_TIMEOUT        # Seconds per request (default: 240)
REPORT_DIR         # Output folder for JSON reports (default: reports)
```

---

## Key Functions

### `chat(model, prompt, max_tokens, temperature, system)` → `(str, float)`
**File: `llm_bench/api.py`** - Makes API call, returns (response_text, latency)

### `score_question(q, response)` → `(float, str, str)`
**File: `llm_bench/scoring.py`** - Multi-method scoring, returns (raw_score, method, notes)

### `llm_judge(model_judge, question, response)` → `(float, str)`
**File: `llm_bench/scoring.py`** - LLM-as-Judge with 0-3 rubric

### `run_all(model, questions, verbose, judge_model)` → `list[Result]`
**File: `llm_bench/runner.py`** - Main evaluation loop

### `save_report(results, model)` → `str`
**File: `llm_bench/report.py`** - JSON report serialization

---

## Common Development Tasks

### Adding a new question

Add to `QUESTIONS` list in `llm_bench/questions.py`:
```python
Question(
    id="L-7", category="Logic", lang="en", difficulty="Medium",
    prompt="...", reference="...",
    keywords=["key1", "key2"],
)
```

### Modifying scoring logic

Edit `score_question()` in `llm_bench/scoring.py`.

### Adding new API provider

Edit `chat()` in `llm_bench/api.py`.

### Extending with new scoring method

Add new condition in `score_question()` in `llm_bench/scoring.py`.

---

## Testing

### Interactive menu (no args)
```bash
python main.py
```

### Quick test (1 question per tier)
```bash
python main.py "your-model" --quick
```

### Full test (all 45 questions)
```bash
python main.py "your-model" --all -s
```

### Single category
```bash
python main.py "your-model" --cat Math
```

### Compare two models
```bash
python main.py --compare model-a model-b --all
```

---

## Important Notes

### Hardcoded Values
- **Default timeouts:** `API_TIMEOUT=240s`, `CODE_TIMEOUT=5s`
- **Code sandbox:** `subprocess.run()` with `shell=False` (safe)
- **Score weights:** Easy=1x, Medium=2x, Hard=3x
- **Max score per question:** 10 points

### Known Limitations
1. Code execution only supports Python
2. No persistent state — each run is independent
3. No caching — all API calls made fresh
4. Fuzzy matching uses simple text normalization
5. LLM-as-Judge requires 2x API calls per question

### Platform Notes
- **Windows UTF-8 fix:** in `main.py` (handles Vietnamese characters)
- **ANSI colors:** works in most modern terminals
- **Subprocess safety:** `shell=False` prevents command injection

---

## Git Workflow

**Commit message convention:**
```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## Quick Reference

| Command | What it does |
|---------|--------------|
| `python main.py` | Interactive menu |
| `python main.py MODEL --all -s` | Full test, save report |
| `python main.py MODEL --quick` | Quick test |
| `python main.py --compare A B --all` | Compare models A and B |
| `python main.py MODEL --judge JUDGE` | Enable LLM-as-Judge |
| `python main.py --ping` | Test API connectivity |
| `python main.py --list` | List available models |

---

## Contact & License

- **License:** MIT
- **GitHub:** https://github.com/dat911zz/llm-benchmark
- **Author:** dat911zz
- **Co-contributed:** Claude

For issues or questions, open an issue on GitHub.
