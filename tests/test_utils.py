"""Unit tests for llm_bench/utils.py — strip_vi() and strip_latex()."""

import unittest
from llm_bench.utils import strip_vi, strip_latex


class TestStripVi(unittest.TestCase):
    """Tests for Vietnamese diacritic normalization."""

    def test_basic_accented_vowels(self):
        self.assertEqual(strip_vi("á"), "a")
        self.assertEqual(strip_vi("à"), "a")
        self.assertEqual(strip_vi("ả"), "a")
        self.assertEqual(strip_vi("ã"), "a")
        self.assertEqual(strip_vi("ạ"), "a")

    def test_phrase_ca_hai(self):
        result = strip_vi("Cả hai")
        self.assertEqual(result.lower(), "ca hai")

    def test_phrase_tuong_quan(self):
        result = strip_vi("tương quan")
        self.assertIn("tuong", result)
        self.assertIn("quan", result)

    def test_phrase_ap_suat(self):
        result = strip_vi("áp suất")
        self.assertIn("ap", result)
        self.assertIn("suat", result)

    def test_unaccented_unchanged(self):
        self.assertEqual(strip_vi("hello world"), "hello world")
        self.assertEqual(strip_vi("123"), "123")

    def test_empty_string(self):
        self.assertEqual(strip_vi(""), "")

    def test_mixed_en_vi(self):
        result = strip_vi("Python là ngôn ngữ")
        self.assertIn("Python", result)
        self.assertIn("la", result)

    def test_returns_string(self):
        self.assertIsInstance(strip_vi("test"), str)


class TestStripLatex(unittest.TestCase):
    """Tests for LaTeX notation normalization."""

    def test_subscript_chemical(self):
        result = strip_latex("$CO_2$")
        self.assertIn("CO2", result)

    def test_subscript_h2o(self):
        result = strip_latex("$H_2O$")
        self.assertIn("H2O", result)

    def test_fraction_simple(self):
        result = strip_latex("\\frac{1}{6}")
        self.assertIn("1/6", result)

    def test_fraction_negative(self):
        result = strip_latex("$-\\frac{1}{2}$")
        self.assertIn("-1/2", result)

    def test_dollar_signs_removed(self):
        result = strip_latex("$x$")
        self.assertNotIn("$", result)

    def test_unicode_subscript_digits(self):
        result = strip_latex("CO₂")
        self.assertIn("CO2", result)

    def test_plain_text_unchanged(self):
        result = strip_latex("hello world")
        self.assertEqual(result, "hello world")

    def test_empty_string(self):
        self.assertEqual(strip_latex(""), "")

    def test_returns_string(self):
        self.assertIsInstance(strip_latex("test"), str)


if __name__ == "__main__":
    unittest.main()
