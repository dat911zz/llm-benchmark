# CLAUDE.md - Project Context & Development Guide

## Project Overview

**LLM Intelligence Test Suite v2.0**

A comprehensive LLM evaluation benchmark tool for assessing language model capabilities across multiple dimensions (logic, math, coding, knowledge, critical thinking, language fluency, common sense).

**Key characteristics:**
- Single Python file (`test_model.py`), ~1500 lines
- Zero external dependencies (stdlib only, Python 3.10+)
- Bilingual: English + Vietnamese questions
- OpenAI-compatible API (works with LM Studio, Ollama, OpenAI, Dashscope, etc.)
- Multi-method scoring: keyword matching, exact match, code execution, LLM-as-Judge
- Generates JSON reports with per-category and per-language breakdown
- Includes comparison mode for A/B testing models

---

## Repository Structure

```
llm-benchmark/
├── test_model.py           # Main script (~1500 lines)
├── README.md              # English documentation with language switcher
├── README.vi.md           # Vietnamese documentation
├── .env.example           # Template for configuration (copy to .env)
├── .gitignore             # Git ignore rules
└── reports/               # (ignored by git) Generated JSON reports
```

---

## Core Architecture

### Main Components (in test_model.py)

| Component | Lines | Purpose |
|-----------|-------|---------|
| Imports & Config | 1-61 | Environment variables, API endpoints, timeouts |
| ANSI Colors | 62-77 | Terminal color utilities |
| Text normalization | 79-112 | `strip_vi()`, `strip_latex()` for fuzzy matching |
| **Question** dataclass | 116-137 | Data model for each test question |
| **Result** dataclass | 139-149 | Stores per-question evaluation result |
| **QUESTIONS** list | 152-952 | 45 hardcoded questions (8 categories × difficulty tiers) |
| API client | 963-1037 | `api_post()`, `chat()`, `ping_api()` |
| **score_question()** | 1084-1165 | Core multi-method scoring engine |
| **llm_judge()** | 1168-1208 | Optional LLM-as-Judge rubric evaluator |
| Display functions | 1211-1382 | `print_summary()`, `compare_summary()`, etc. |
| **run_all()** | 1439-1508 | Main evaluation loop |
| **save_report()** | 1513-1576 | JSON report serializer |
| CLI / **main()** | 1579-end | Argument parsing, interactive mode, compare mode |

### Question Categories (8 total, 45 questions)

- **Logic** (6): Zebra puzzle, riddles, syllogisms
- **Math** (6): GSM8K-style word problems, algebra, geometry
- **Coding** (5): Python write/debug/explain, DP problems
- **Knowledge** (6): Science, history, geography (EN+VI)
- **Critical Thinking** (5): Bias detection, Fermi estimation, fallacies
- **Language** (5): Vietnamese proverbs, grammar, register shifts
- **Common Sense** (5): HellaSwag-style continuations, situational reasoning
- **Calibration** (1): Epistemic uncertainty, confidence self-assessment

Each question has:
- `id`: Unique identifier (e.g., "L-1", "M-2")
- `difficulty`: Easy (1x), Medium (2x), or Hard (3x) — affects scoring weight
- `question_en`, `question_vi`: Bilingual question text
- `expected_output`: Answer key (string, code output, or list of keywords)
- `scoring_type`: "code" | "exact_match" | "keywords" | "any_keywords"
- For keywords: `required_keywords`, `any_keywords`, `any_min`

### Scoring System

Priority order (first match wins):
1. **Code execution** (5s sandbox timeout)
   - Extracts Python from response, runs it, checks stdout
   - Used for coding questions

2. **Exact/numeric match**
   - Looks for specific expected numbers/strings anywhere in response
   - Used for math/knowledge questions

3. **Required keywords (ALL must match)**
   - All keywords in list must appear (case-insensitive, fuzzy)
   - Used for logic/critical thinking

4. **Optional keywords (N of M)**
   - At least `any_min` of `any_keywords` must appear
   - Used for flexible answer patterns

**Weighted score formula:**
```
raw_score × difficulty_weight × 10 = question_score
(Easy=1x, Medium=2x, Hard=3x, base=10 points)
```

**Max possible:** 450 points (45 questions × 10 points)

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

See `.env.example` for full template.

### API Compatibility

Works with any OpenAI-compatible API:
- **LM Studio** (local, recommended for testing)
- **Ollama** (local)
- **OpenAI** (cloud, requires API key)
- **Dashscope/Aliyun** (Qwen models)
- Custom OpenAI-compatible endpoints

---

## Key Functions

### `chat(model, messages, temperature=0.7) -> str`
**Lines 1000-1037**
- Makes API call to chat completions endpoint
- Returns assistant response text
- Handles API errors, timeouts, retries

### `score_question(question, response) -> (score, details)`
**Lines 1084-1165**
- Core scoring logic
- Tries all 4 scoring methods
- Returns normalized score (0.0-1.0)
- Includes debug details dict

### `llm_judge(model, question, response, judge_model) -> score`
**Lines 1168-1208**
- Optional second-pass scoring
- Uses another model to evaluate on 0-3 rubric
- Blends 60% llm_judge + 40% keyword score
- Called when `--judge` flag is used

### `run_all(model, questions, ...) -> (results, summary)`
**Lines 1439-1508**
- Main evaluation loop
- Iterates through questions, calls `chat()`, scores with `score_question()`
- Tracks latency, aggregates scores
- Returns Results objects + Summary dict

### `save_report(model, results, summary) -> filepath`
**Lines 1513-1576**
- Serializes results to JSON
- Computes per-category and per-language breakdowns
- Saves to `reports/report_TIMESTAMP.json`
- Returns filepath

---

## Common Development Tasks

### Adding a new question

Add to `QUESTIONS` list (lines 152-952):
```python
Question(
    id="L-7",
    category="Logic",
    difficulty="Medium",
    question_en="...",
    question_vi="...",
    expected_output="...",
    scoring_type="keywords",
    required_keywords=["key1", "key2"],
)
```

### Modifying scoring logic

Edit `score_question()` function (lines 1084-1165). Priority order is hardcoded:
1. Check if `scoring_type == "code"` → run code execution
2. Check if `scoring_type == "exact_match"` → look for exact match
3. Check `required_keywords` → all must match
4. Check `any_keywords` → N of M must match

### Adding new API provider

Edit `chat()` function (lines 1000-1037):
- Change `OPENAI_BASE_URL` or add provider detection
- Adjust request headers/format if needed (must be OpenAI-compatible)

### Extending with new scoring method

Add new condition in `score_question()`:
```python
if question.scoring_type == "new_type":
    score = my_new_scoring_logic(question, response)
```

---

## Testing

### Quick test (1 question per tier)
```bash
python test_model.py "your-model" --quick
```

### Full test (all 45 questions)
```bash
python test_model.py "your-model" --all -s
```

### Single category
```bash
python test_model.py "your-model" --cat Math
```

### Verbose output (show full responses)
```bash
python test_model.py "your-model" --all -v
```

### Compare two models
```bash
python test_model.py --compare model-a model-b --all
```

---

## Important Notes

### Hardcoded Values to Be Aware Of

- **Default timeouts:** `API_TIMEOUT=240s`, `CODE_TIMEOUT=5s`
- **Code sandbox:** Uses `subprocess.run()` with shell=False (safe)
- **Score weights:** Easy=1x, Medium=2x, Hard=3x (hardcoded in score calculation)
- **Max score per question:** 10 points

### Known Limitations

1. **Code execution only supports Python** — other languages not evaluated
2. **No persistent state** — each run is independent
3. **No caching** — all API calls made fresh (can be slow for large batches)
4. **Fuzzy matching uses simple text normalization** — may have false positives/negatives
5. **LLM-as-Judge is expensive** — requires 2x API calls per question

### Platform Notes

- **Windows UTF-8 fix:** Lines 48-50 redirect stdout/stderr to UTF-8 (handles Vietnamese characters)
- **Color output:** Uses ANSI escape codes (works in most modern terminals)
- **Subprocess safety:** `shell=False` prevents command injection in code execution

---

## Git Workflow

**Commit message convention:**
```
<type>: <description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Protected:** No auto-commits; user must explicitly request (`/commit` skill)

---

## Future Enhancement Ideas

- [ ] Cache API responses to avoid re-running same model
- [ ] Add more scoring methods (semantic similarity, regex patterns)
- [ ] Extend to other programming languages (JavaScript, Go, Rust)
- [ ] Add web UI for visualization of results
- [ ] Integrate with popular LLM leaderboards (LMSYS, OpenCompass)
- [ ] Support streaming responses for real-time evaluation
- [ ] Add benchmarking mode (measure latency, throughput)
- [ ] Multi-language support beyond EN/VI

---

## Quick Reference

| Command | What it does |
|---------|--------------|
| `python test_model.py` | Interactive mode |
| `python test_model.py MODEL --all -s` | Full test, save report |
| `python test_model.py MODEL --quick` | Quick test (12 questions) |
| `python test_model.py --compare A B --all` | Compare models A and B |
| `python test_model.py MODEL --judge JUDGE` | Enable LLM-as-Judge |

---

## Contact & License

- **License:** MIT
- **GitHub:** https://github.com/dat911zz/llm-benchmark
- **Author:** dat911zz
- **Co-contributed:** Claude

For issues or questions, open an issue on GitHub.

