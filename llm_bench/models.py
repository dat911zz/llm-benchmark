"""Data models: Question and Result dataclasses."""

from dataclasses import dataclass, field


@dataclass
class Question:
    id: str
    category: str          # Logic | Math | Coding | Knowledge | Critical | Language | Common | Calibration
    lang: str              # "en" | "vi"
    difficulty: str        # "Easy" | "Medium" | "Hard"
    prompt: str
    reference: str         # human-readable correct answer (for display + judge)

    # Scoring config (at least one method must be set)
    keywords: list[str] = field(default_factory=list)       # must ALL appear (AND logic)
    any_keywords: list[str] = field(default_factory=list)   # at least N must appear
    any_min: int = 0                                         # min count for any_keywords
    exact_numbers: list[str] = field(default_factory=list)  # numeric answers to find
    code_to_exec: str = ""      # if set: extract code from response & execute; check stdout
    expected_output: str = ""   # expected stdout when code is run
    open_ended: bool = False    # True => LLM-as-Judge only (no keyword scoring)

    # Tool-use evaluation fields (only for ToolUse category)
    tools: list[dict] = field(default_factory=list)
    # OpenAI-format tool schemas sent to /chat/completions
    expected_tool_calls: list[dict] = field(default_factory=list)
    # [{"name": "func_name", "args": {"k": "v"}}] — empty + irrelevant_tools = irrelevant test
    irrelevant_tools: list[str] = field(default_factory=list)
    # Tool names model should NOT call

    base_points: int = 10
    max_tokens: int = 512
    temperature: float = 0.0    # deterministic for benchmarking


@dataclass
class Result:
    question: Question
    response: str
    raw_score: float      # 0.0 – 1.0
    weighted_score: float # raw_score * difficulty_weight * base_points
    max_weighted: float   # difficulty_weight * base_points
    method: str           # scoring method used
    latency: float
    notes: str = ""
    judge_reasoning: str = ""
    tool_calls_made: list = field(default_factory=list)
    # Parsed tool calls from API response: [{"name": str, "args": dict}]
