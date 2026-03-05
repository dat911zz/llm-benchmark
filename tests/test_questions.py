"""Unit tests for llm_bench/questions.py — question bank integrity checks."""

import unittest
from llm_bench.questions import QUESTIONS
from llm_bench.models import Question

VALID_CATEGORIES = {
    "Logic", "Math", "Coding", "Knowledge",
    "Critical", "Language", "Common Sense", "Calibration", "ToolUse"
}
VALID_DIFFICULTIES = {"Easy", "Medium", "Hard"}
VALID_LANGS = {"en", "vi"}


class TestQuestionBankIntegrity(unittest.TestCase):
    """Validate the QUESTIONS list is structurally correct."""

    def test_total_count(self):
        self.assertGreater(len(QUESTIONS), 0, "QUESTIONS list is empty")

    def test_all_are_question_instances(self):
        for q in QUESTIONS:
            self.assertIsInstance(q, Question, f"{q!r} is not a Question instance")

    def test_unique_ids(self):
        ids = [q.id for q in QUESTIONS]
        duplicates = [qid for qid in ids if ids.count(qid) > 1]
        self.assertEqual(duplicates, [], f"Duplicate IDs found: {set(duplicates)}")

    def test_valid_categories(self):
        for q in QUESTIONS:
            self.assertIn(
                q.category, VALID_CATEGORIES,
                f"Question {q.id} has invalid category: {q.category!r}"
            )

    def test_valid_difficulties(self):
        for q in QUESTIONS:
            self.assertIn(
                q.difficulty, VALID_DIFFICULTIES,
                f"Question {q.id} has invalid difficulty: {q.difficulty!r}"
            )

    def test_valid_languages(self):
        for q in QUESTIONS:
            self.assertIn(
                q.lang, VALID_LANGS,
                f"Question {q.id} has invalid lang: {q.lang!r}"
            )

    def test_all_have_prompt(self):
        for q in QUESTIONS:
            self.assertTrue(q.prompt.strip(), f"Question {q.id} has empty prompt")

    def test_all_have_reference(self):
        for q in QUESTIONS:
            self.assertTrue(q.reference.strip(), f"Question {q.id} has empty reference")

    def test_all_have_at_least_one_scoring_method(self):
        for q in QUESTIONS:
            has_method = (
                bool(q.keywords)
                or bool(q.any_keywords and q.any_min > 0)
                or bool(q.exact_numbers)
                or bool(q.code_to_exec)
                or bool(q.tools)
                or q.open_ended
            )
            self.assertTrue(
                has_method,
                f"Question {q.id} has no scoring method defined"
            )

    def test_all_categories_represented(self):
        present = {q.category for q in QUESTIONS}
        missing = VALID_CATEGORIES - present
        self.assertEqual(missing, set(), f"Missing categories: {missing}")

    def test_both_languages_represented(self):
        langs = {q.lang for q in QUESTIONS}
        self.assertIn("en", langs, "No English questions found")
        self.assertIn("vi", langs, "No Vietnamese questions found")

    def test_code_exec_questions_have_expected_output(self):
        for q in QUESTIONS:
            if q.code_to_exec:
                self.assertTrue(
                    q.expected_output.strip(),
                    f"Question {q.id} has code_to_exec but no expected_output"
                )

    def test_any_keywords_questions_have_any_min(self):
        for q in QUESTIONS:
            if q.any_keywords:
                self.assertGreater(
                    q.any_min, 0,
                    f"Question {q.id} has any_keywords but any_min=0"
                )

    def test_tool_use_questions_have_tools(self):
        for q in QUESTIONS:
            if q.expected_tool_calls:
                self.assertTrue(
                    q.tools,
                    f"Question {q.id} has expected_tool_calls but no tools schema"
                )

    def test_base_points_positive(self):
        for q in QUESTIONS:
            self.assertGreater(
                q.base_points, 0,
                f"Question {q.id} has non-positive base_points: {q.base_points}"
            )

    def test_max_tokens_positive(self):
        for q in QUESTIONS:
            self.assertGreater(
                q.max_tokens, 0,
                f"Question {q.id} has non-positive max_tokens: {q.max_tokens}"
            )

    def test_temperature_in_range(self):
        for q in QUESTIONS:
            self.assertGreaterEqual(q.temperature, 0.0, f"Question {q.id} temperature < 0")
            self.assertLessEqual(q.temperature, 2.0, f"Question {q.id} temperature > 2")


if __name__ == "__main__":
    unittest.main()
