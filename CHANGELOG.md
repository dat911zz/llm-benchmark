# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-03-05

### Added
- **Modular package architecture**: Refactored monolithic `test_model.py` (~1500 lines) into `llm_bench/` package with 9 focused modules (`config`, `utils`, `models`, `questions`, `api`, `scoring`, `display`, `runner`, `report`)
- **New entry point**: `main.py` with interactive CLI menu and full argument parsing
- **Tool-use evaluation**: New `ToolUse` category with BFCL-style structural scoring (`score_tool_calls`, `_match_args`)
- **LLM-as-Judge**: `llm_judge()` function for open-ended question evaluation
- **Comparison mode**: `--compare` flag for A/B testing two models side-by-side
- **CI pipeline**: GitHub Actions workflow (`.github/workflows/ci.yml`) running on Python 3.10, 3.11, 3.12
- **Unit test suite**: 67 tests across `tests/test_utils.py`, `tests/test_scoring.py`, `tests/test_questions.py` — stdlib only, no API required
- **Interactive menu**: Step-by-step guided mode when launched without arguments
- **LaTeX normalization**: `strip_latex()` utility for fuzzy matching math answers
- **Vietnamese fuzzy matching**: `strip_vi()` utility for diacritic-insensitive keyword search

### Changed
- Question bank expanded from 45 to 53 questions (added `ToolUse` category)
- Category name `Critical Thinking` → `Critical` for consistency
- Default API timeout increased for reliability
- Report filenames now include model name and timestamp

### Kept for compatibility
- `test_model.py` retained as legacy entry point (deprecated, use `main.py`)

---

## [1.0.0] - 2025-01-01

### Added
- Initial release as single-file script (`test_model.py`, ~1500 lines)
- 45 benchmark questions across 8 categories: Logic, Math, Coding, Knowledge, Critical Thinking, Language, Common Sense, Calibration
- Bilingual support: English + Vietnamese questions
- OpenAI-compatible API client (works with LM Studio, Ollama, OpenAI, Dashscope)
- Multi-method scoring: keyword matching, exact match, code execution sandbox
- JSON report generation with per-category and per-language breakdown
- ANSI color output with difficulty badges and score bars
- `--quick` mode (1 question per difficulty tier)
- `--cat` filter for single-category runs
- `--judge` flag for LLM-as-Judge evaluation

[2.0.0]: https://github.com/dat911zz/llm-benchmark/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/dat911zz/llm-benchmark/releases/tag/v1.0.0
