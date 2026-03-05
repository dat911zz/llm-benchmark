🌐 [English](README.md) | [Tiếng Việt](docs/README.vi.md)

---

# LLM Intelligence Test Suite

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)

A comprehensive LLM evaluation benchmark inspired by industry-standard tests (MMLU, GSM8K, HumanEval, BIG-Bench Hard, TruthfulQA). Designed to assess language models across multiple dimensions: logic, mathematics, coding, knowledge, critical thinking, language fluency, and common sense.

**Bilingual support**: English + Vietnamese

---

## Features

- **40+ questions** across 8 categories with 3 difficulty tiers (Easy/Medium/Hard)
- **Bilingual**: English and Vietnamese question sets
- **Multi-method scoring**:
  - Keyword matching (fast, deterministic)
  - Exact/numeric matching (math, code output)
  - Code execution (runs generated Python, checks output)
  - LLM-as-Judge (optional, uses a second model to score)
- **Difficulty-weighted scoring** (Easy=1x, Medium=2x, Hard=3x)
- **Structured JSON reports** with per-category and per-language breakdown
- **Comparison mode**: Run multiple models and compare results
- **Zero external dependencies** (Python stdlib only)
- **OpenAI-compatible API** (works with LM Studio, Ollama, OpenAI, Dashscope, etc.)

---

## Requirements

- **Python 3.10+** (uses modern syntax with `list[...]` type hints)
- No pip dependencies required

---

## Installation

```bash
git clone https://github.com/yourusername/llm-benchmark.git
cd llm-benchmark
python main.py --help
```

---

## Quick Start

### Interactive menu (guided step-by-step)
```bash
python main.py
```

### Run all questions against a specific model
```bash
python main.py "your-model-id" --all -s
```

### Run all questions with detailed output
```bash
python main.py "your-model-id" --all -v
```

### Run quick version (1 question per difficulty tier)
```bash
python main.py "your-model-id" --quick
```

### Test only Math category
```bash
python main.py "your-model-id" --cat Math
```

### Test only Vietnamese questions
```bash
python main.py "your-model-id" --lang vi
```

### Enable LLM-as-Judge scoring (use a second model to rate responses)
```bash
python main.py "your-model-id" --all --judge "judge-model-id"
```

### Compare two models
```bash
python main.py --compare "model-a" "model-b" --all
```

---

## Example Output

Here's what the test results look like:

![Output Example](docs/assets/output-example.png)

The report shows:
- **Score breakdown** by category and difficulty level
- **Visual progress bars** for quick assessment
- **Weighted scores** with percentage accuracy
- **Language-specific results** (English vs Vietnamese)

---

## Configuration

Set environment variables to customize API endpoint and models:

```bash
export OPENAI_BASE_URL="http://localhost:1234/v1"           # API endpoint (default: localhost)
export OPENAI_API_KEY="your-api-key-here"                  # API key (optional, leave empty for local)
export OPENAI_MODEL="your-model-id"                        # Default model to use
export API_TIMEOUT="240"                                   # Seconds per API request (default: 240)
export REPORT_DIR="reports"                                # Folder to save JSON reports (default: reports)
```

Or override on the command line:
```bash
python main.py --api-key sk-xxx --base-url http://... "model-id" --all
```

---

## Question Categories

| Category | Count | Example |
|----------|-------|---------|
| **Logic** | 6 | Zebra puzzle, two-guards riddle, syllogisms |
| **Math** | 6 | GSM8K-style word problems, algebra, geometry |
| **Coding** | 5 | Write/debug Python, explain output, dynamic programming |
| **Knowledge** | 6 | Science, history, geography (EN + VI) |
| **Critical Thinking** | 5 | Bias detection, Fermi estimation, fallacy ID |
| **Language** | 5 | Vietnamese proverbs, grammar, register shifts |
| **Common Sense** | 5 | HellaSwag continuations, situational reasoning |
| **Calibration** | 1 | Epistemic uncertainty, confidence self-assessment |

---

## Scoring Methods

Results are computed using up to 4 scoring methods (in order of priority):

1. **Code Execution**: Extract Python code from response, run in sandbox (5s timeout), check stdout
2. **Exact/Numeric Match**: Look for specific expected numbers anywhere in response
3. **Required Keywords (AND)**: All keywords must appear
4. **Optional Keywords (OR)**: At least N of M keywords must appear

Weighted score = `raw_score × difficulty_weight × base_points` (10 points max per question)

Final weighted max = 450 (45 questions × 10 points, before difficulty scaling)

---

## Output Format

Each run generates a JSON report in the `reports/` directory:

```json
{
  "version": "2.0",
  "model": "your-model-id",
  "timestamp": "2024-01-15T14:30:00Z",
  "summary": {
    "total_weighted_score": 430.5,
    "total_weighted_max": 450.0,
    "percentage": 95.7,
    "questions_asked": 45,
    "avg_latency_s": 8.2
  },
  "by_category": {
    "Logic": {"score": 60.0, "max": 60.0, "pct": 100.0},
    "Math": {"score": 60.0, "max": 60.0, "pct": 100.0},
    ...
  },
  "by_language": {
    "en": {"score": 220.0, "max": 225.0, "pct": 97.8},
    "vi": {"score": 210.5, "max": 225.0, "pct": 93.6}
  }
}
```

---

## Supported API Providers

- **LM Studio** (local, OpenAI-compatible)
- **Ollama** (local, OpenAI-compatible)
- **OpenAI** (GPT-4, GPT-3.5, etc.)
- **Dashscope/Aliyun** (Qwen models)
- **Any OpenAI-compatible API endpoint**

---

## Example: Using with LM Studio

1. Install [LM Studio](https://lmstudio.ai) and download a model
2. Start LM Studio local server (default: `http://localhost:1234/v1`)
3. Run:
   ```bash
   python main.py "your-local-model" --all -s
   ```

---

## Troubleshooting

**API connection failed?**
- Check `OPENAI_BASE_URL` is correct
- Ensure API server is running
- Increase `API_TIMEOUT` for slow connections

**Code execution sandbox errors?**
- Some models may generate invalid Python
- Set `CODE_TIMEOUT` to 5+ seconds if needed

**Low accuracy scores?**
- Try smaller, specialized models for specific categories
- Enable `--judge` mode for subjective questions

---

## License

MIT

---

## References

Inspired by:
- **MMLU**: Massive Multitask Language Understanding
- **GSM8K**: Grade School Math 8K
- **HumanEval**: Code generation benchmark
- **BIG-Bench Hard**: Challenges for large language models
- **TruthfulQA**: Evaluating language model hallucinations
- **HellaSwag**: Common sense understanding via continuations

---

## Contributing

Issues, suggestions, and pull requests welcome!

