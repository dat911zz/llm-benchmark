"""Unit tests for llm_bench/scoring.py — pure functions only (no API calls)."""

import unittest
from unittest.mock import patch
from llm_bench.models import Question
from llm_bench.scoring import extract_code_block, _match_args, score_tool_calls, score_question


class TestExtractCodeBlock(unittest.TestCase):
    """Tests for extract_code_block()."""

    def test_fenced_python_block(self):
        text = "Here is the code:\n```python\nprint('hello')\n```"
        result = extract_code_block(text)
        self.assertEqual(result, "print('hello')")

    def test_fenced_generic_block(self):
        text = "```\ndef add(a, b):\n    return a + b\n```"
        result = extract_code_block(text)
        self.assertIn("def add", result)

    def test_inline_code(self):
        text = "Use `x = 1` to set x."
        result = extract_code_block(text)
        self.assertEqual(result, "x = 1")

    def test_no_code_block_returns_something(self):
        text = "Just some plain text response."
        result = extract_code_block(text)
        self.assertIsInstance(result, str)

    def test_returns_stripped(self):
        text = "```python\n  print('hi')  \n```"
        result = extract_code_block(text)
        self.assertEqual(result, result.strip())

    def test_multiline_code_block(self):
        text = "```python\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n```"
        result = extract_code_block(text)
        self.assertIn("def fib", result)
        self.assertIn("return", result)


class TestMatchArgs(unittest.TestCase):
    """Tests for _match_args() — tool argument comparison."""

    def test_empty_expected_always_full_score(self):
        self.assertEqual(_match_args({}, {"any": "value"}), 1.0)
        self.assertEqual(_match_args({}, {}), 1.0)

    def test_exact_match(self):
        self.assertEqual(_match_args({"city": "hanoi"}, {"city": "hanoi"}), 1.0)

    def test_case_insensitive_match(self):
        self.assertEqual(_match_args({"city": "Hanoi"}, {"city": "hanoi"}), 1.0)

    def test_substring_partial_match(self):
        score = _match_args({"q": "weather"}, {"q": "the weather today"})
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_no_match(self):
        self.assertEqual(_match_args({"k": "abc"}, {"k": "xyz"}), 0.0)

    def test_missing_key_in_actual(self):
        score = _match_args({"k": "val"}, {})
        self.assertEqual(score, 0.0)

    def test_multiple_keys_all_match(self):
        self.assertEqual(
            _match_args({"a": "1", "b": "2"}, {"a": "1", "b": "2"}),
            1.0
        )

    def test_multiple_keys_partial_match(self):
        score = _match_args({"a": "1", "b": "2"}, {"a": "1", "b": "99"})
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_score_capped_at_1(self):
        score = _match_args({"k": "v"}, {"k": "v"})
        self.assertLessEqual(score, 1.0)


class TestScoreToolCalls(unittest.TestCase):
    """Tests for score_tool_calls()."""

    def _make_tool_question(self, expected=None, irrelevant=None, tools=None):
        return Question(
            id="T-1", category="ToolUse", lang="en", difficulty="Medium",
            prompt="Call the weather tool.",
            reference="weather(city=hanoi)",
            tools=tools or [{"name": "get_weather"}],
            expected_tool_calls=expected or [],
            irrelevant_tools=irrelevant or [],
        )

    def test_irrelevant_tools_no_call_is_correct(self):
        q = self._make_tool_question(expected=[], irrelevant=["bad_tool"], tools=[{"name": "bad_tool"}])
        score, method, _ = score_tool_calls(q, [])
        self.assertEqual(score, 1.0)
        self.assertIn("no_call_correct", method)

    def test_irrelevant_tools_called_is_wrong(self):
        q = self._make_tool_question(expected=[], irrelevant=["bad_tool"], tools=[{"name": "bad_tool"}])
        score, method, _ = score_tool_calls(q, [{"name": "bad_tool", "args": {}}])
        self.assertEqual(score, 0.0)

    def test_correct_tool_called_full_score(self):
        q = self._make_tool_question(
            expected=[{"name": "get_weather", "args": {"city": "hanoi"}}]
        )
        score, _, _ = score_tool_calls(q, [{"name": "get_weather", "args": {"city": "hanoi"}}])
        self.assertEqual(score, 1.0)

    def test_no_calls_made_zero_score(self):
        q = self._make_tool_question(
            expected=[{"name": "get_weather", "args": {}}]
        )
        score, method, _ = score_tool_calls(q, [])
        self.assertEqual(score, 0.0)
        self.assertIn("no_calls_made", method)

    def test_no_expected_defined_half_score(self):
        q = self._make_tool_question(expected=[], irrelevant=[])
        score, method, _ = score_tool_calls(q, [{"name": "some_tool", "args": {}}])
        self.assertEqual(score, 0.5)

    def test_score_range_valid(self):
        q = self._make_tool_question(
            expected=[{"name": "get_weather", "args": {"city": "hanoi"}}]
        )
        score, _, _ = score_tool_calls(q, [{"name": "get_weather", "args": {"city": "hcm"}}])
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestScoreQuestion(unittest.TestCase):
    """Tests for score_question() — keyword and exact number scoring."""

    def _kw_question(self, keywords=None, any_keywords=None, any_min=0, exact_numbers=None):
        return Question(
            id="TEST-1", category="Logic", lang="en", difficulty="Easy",
            prompt="Test prompt",
            reference="Test reference",
            keywords=keywords or [],
            any_keywords=any_keywords or [],
            any_min=any_min,
            exact_numbers=exact_numbers or [],
        )

    def test_all_keywords_match_full_score(self):
        q = self._kw_question(keywords=["yes", "correct"])
        score, method, _ = score_question(q, "Yes, that is correct.")
        self.assertEqual(score, 1.0)
        self.assertIn("kw_all", method)

    def test_missing_keyword_partial_score(self):
        q = self._kw_question(keywords=["yes", "correct"])
        score, _, _ = score_question(q, "Yes, maybe.")
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_no_keywords_present_zero(self):
        q = self._kw_question(keywords=["blue", "sky"])
        score, _, _ = score_question(q, "The answer is red ground.")
        self.assertEqual(score, 0.0)

    def test_any_keywords_meet_minimum(self):
        q = self._kw_question(any_keywords=["wing", "fly", "bird"], any_min=2)
        score, method, _ = score_question(q, "Penguins have wings and are birds.")
        self.assertEqual(score, 1.0)
        self.assertIn("kw_any", method)

    def test_any_keywords_below_minimum(self):
        q = self._kw_question(any_keywords=["wing", "fly", "bird"], any_min=3)
        score, _, _ = score_question(q, "They have wings.")
        self.assertLess(score, 1.0)

    def test_exact_number_match_full(self):
        q = self._kw_question(exact_numbers=["0.05", "5"])
        score, method, _ = score_question(q, "The ball costs $0.05 (5 cents).")
        self.assertEqual(score, 1.0)
        self.assertIn("exact_num", method)

    def test_exact_number_missing(self):
        q = self._kw_question(exact_numbers=["42"])
        score, _, _ = score_question(q, "The answer is 100.")
        self.assertEqual(score, 0.0)

    def test_no_scoring_method_returns_half(self):
        q = self._kw_question()  # no keywords, no numbers
        score, method, _ = score_question(q, "Some open response.")
        self.assertEqual(score, 0.5)
        self.assertIn("no_method", method)

    def test_score_always_in_range(self):
        q = self._kw_question(keywords=["x"], any_keywords=["a", "b"], any_min=1)
        for response in ["x a b", "x", "a b", "", "x a b and more text here"]:
            score, _, _ = score_question(q, response)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_case_insensitive_keyword(self):
        q = self._kw_question(keywords=["YES"])
        score, _, _ = score_question(q, "yes, that's right.")
        self.assertEqual(score, 1.0)

    @patch("llm_bench.scoring.run_code")
    def test_code_exec_pass(self, mock_run_code):
        mock_run_code.return_value = (True, "42", "")
        q = Question(
            id="C-1", category="Coding", lang="en", difficulty="Hard",
            prompt="Write code that prints 42.",
            reference="42",
            code_to_exec="RESPONSE_CODE\nprint(result)",
            expected_output="42",
        )
        score, method, _ = score_question(q, "```python\nresult = 42\n```")
        self.assertEqual(score, 1.0)
        self.assertIn("code_exec:PASS", method)

    @patch("llm_bench.scoring.run_code")
    def test_code_exec_fail_falls_through(self, mock_run_code):
        mock_run_code.return_value = (True, "99", "")
        q = Question(
            id="C-2", category="Coding", lang="en", difficulty="Hard",
            prompt="Write code that prints 42.",
            reference="42",
            code_to_exec="RESPONSE_CODE\nprint(result)",
            expected_output="42",
            keywords=["42"],
        )
        score, method, _ = score_question(q, "The answer is 42")
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()
