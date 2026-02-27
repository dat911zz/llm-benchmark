#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LM Studio Model Intelligence Test Suite  v2.0
==============================================
Inspired by: MMLU, GSM8K, HumanEval, BIG-Bench Hard, BBH, TruthfulQA

Features
--------
- 40 questions across 8 categories, 3 difficulty tiers (Easy/Medium/Hard)
- Bilingual: English + Vietnamese
- Multi-method scoring:
    * Keyword match  (fast, deterministic)
    * Exact / numeric match  (math, code output)
    * Code execution  (runs generated Python and checks output)
    * LLM-as-Judge  (optional, uses a second model to score)
- Difficulty-weighted scoring (Easy=1x, Medium=2x, Hard=3x)
- JSON report with per-category & per-language breakdown
- Comparison mode: run multiple models and diff results

Usage
-----
  python test_model.py                        # interactive
  python test_model.py MODEL_ID --all -s      # all questions, save report
  python test_model.py MODEL_ID --all -v      # verbose: show full responses
  python test_model.py MODEL_ID --all -q      # quick: 1 per difficulty tier
  python test_model.py MODEL_ID --cat Math    # only Math category
  python test_model.py MODEL_ID --lang vi     # only Vietnamese
  python test_model.py MODEL_ID --judge JUDGE # enable LLM-as-Judge scoring
  python test_model.py --compare A_ID B_ID    # compare two models
"""

import json
import os
import re
import subprocess
import sys
import io
import time
import textwrap
import unicodedata
import urllib.request
import urllib.error
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# ── Fix Windows terminal UTF-8 ───────────────────────────────────────────────
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Config: Endpoint & Auth ───────────────────────────────────────────────────
# Support OpenAI-compatible APIs: local (LM Studio, Ollama) or cloud (Dashscope, OpenAI)
# Env vars: OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL, API_TIMEOUT, REPORT_DIR
API_BASE_URL  = os.environ.get("OPENAI_BASE_URL", "http://localhost:1234/v1")
API_KEY       = os.environ.get("OPENAI_API_KEY", "your-api-key-here")          # empty = no auth (local)
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "your-model-id")            # empty = interactive pick
API_TIMEOUT   = int(os.environ.get("API_TIMEOUT", "240"))     # seconds per request
CODE_TIMEOUT  = 5                                              # seconds for code execution sandbox
REPORT_DIR    = os.environ.get("REPORT_DIR", "reports")       # folder to save reports

# ── ANSI Colors ───────────────────────────────────────────────────────────────
R   = "\033[91m"
G   = "\033[92m"
Y   = "\033[93m"
B   = "\033[94m"
M   = "\033[95m"
C   = "\033[96m"
W   = "\033[97m"
DIM = "\033[2m"
RST = "\033[0m"
BLD = "\033[1m"

# Difficulty colors
DIFF_COLOR = {"Easy": G, "Medium": Y, "Hard": R}
DIFF_WEIGHT = {"Easy": 1, "Medium": 2, "Hard": 3}

# ── Vietnamese Diacritic Normalization ─────────────────────────────────────────
def strip_vi(text: str) -> str:
    """Strip Vietnamese diacritics for fuzzy keyword matching.

    Converts accented Vietnamese to unaccented form:
      'Cả hai' → 'ca hai'
      'tương quan' → 'tuong quan'
      'áp suất' → 'ap suat'

    Uses Unicode NFD normalization to decompose diacritics, then removes
    combining marks (category Mn).
    """
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def strip_latex(text: str) -> str:
    """Strip LaTeX notation for fuzzy keyword matching.

    Converts LaTeX math notation to plain text:
      '$CO_2$' → 'co2'
      '\\frac{1}{6}' → '1/6'
      '$-\\frac{1}{2}$' → '-1/2'
    """
    # Normalize Unicode subscript digits (₀₁₂...₉) to ASCII (0123...9)
    unicode_subs = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    text = text.translate(unicode_subs)

    # Convert fractions: \frac{a}{b} → a/b
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1/\2", text)
    # Collapse subscripts: CO_2 → CO2, H_2O → H2O
    text = re.sub(r"([A-Za-z])_(\d+)([A-Za-z]?)", r"\1\2\3", text)
    # Remove LaTeX delimiters: $, {, }
    text = re.sub(r"[\$\{\}]", "", text)
    return text

# ── Data Model ────────────────────────────────────────────────────────────────

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


# ── Question Bank ─────────────────────────────────────────────────────────────
# 40 questions: 8 categories × (2 Easy + 3 Medium + 2 Hard) ≈ balanced
# EN / VI roughly 50/50

QUESTIONS: list[Question] = [

    # ════════════════════════════════════════════════════════
    # CATEGORY 1: LOGIC & DEDUCTIVE REASONING
    # ════════════════════════════════════════════════════════

    Question(
        id="L-E1", category="Logic", lang="en", difficulty="Easy",
        prompt=(
            "All birds have wings. Penguins are birds. "
            "Do penguins have wings? Answer YES or NO, then explain in one sentence."
        ),
        reference="Yes, penguins have wings (even though they cannot fly).",
        keywords=["yes"],
        any_keywords=["wing", "penguin", "bird"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="L-E2", category="Logic", lang="vi", difficulty="Easy",
        prompt=(
            "Tat ca nguoi Viet Nam deu song o Trai Dat. "
            "Nam la nguoi Viet Nam. "
            "Nam co song o Trai Dat khong? Tra loi CO hoac KHONG va giai thich mot cau."
        ),
        reference="Co, Nam song o Trai Dat (syllogism don gian).",
        keywords=["co"],
        any_keywords=["trai dat", "viet nam", "nam"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="L-M1", category="Logic", lang="en", difficulty="Medium",
        prompt=(
            "A bat and a ball cost $1.10 in total. "
            "The bat costs $1.00 more than the ball. "
            "How much does the ball cost? Show your working step by step."
        ),
        reference="Ball = $0.05 (5 cents). Let ball=x, bat=x+1.00; x+(x+1.00)=1.10 → 2x=0.10 → x=0.05.",
        exact_numbers=["0.05", "5"],
        any_keywords=["cent", "dollar", "ball"],
        any_min=1,
        max_tokens=300,
    ),

    Question(
        id="L-M2", category="Logic", lang="vi", difficulty="Medium",
        prompt=(
            "Co 3 hop: mot hop chi co tao, mot hop chi co cam, mot hop co ca hai. "
            "TAT CA nhan dan tren hop deu SAI. "
            "Ban chi duoc lay 1 qua tu 1 hop. Ban chon hop nao de dat lai nhan dung cho ca 3 hop? "
            "Giai thich buoc buoc."
        ),
        reference=(
            "Chon hop co nhan 'Ca hai'. Vi nhan sai, hop do phai la chi tao hoac chi cam. "
            "Qua ban lay se xac dinh hop do. Tu do suy ra 2 hop con lai."
        ),
        keywords=["ca hai"],
        any_keywords=["sai", "nhan", "xac dinh", "suy ra"],
        any_min=2,
        max_tokens=400,
    ),

    Question(
        id="L-M3", category="Logic", lang="en", difficulty="Medium",
        prompt=(
            "You are in a room with two doors. One door leads to freedom, "
            "one to a tiger. There are two guards: one always lies, one always tells the truth. "
            "You don't know which is which. You may ask ONE guard ONE yes/no question. "
            "What question do you ask to guarantee finding the freedom door?"
        ),
        reference=(
            "Ask either guard: 'If I asked the OTHER guard which door leads to freedom, "
            "what would he say?' Then take the OPPOSITE door."
        ),
        any_keywords=["other", "opposite", "would say", "liar", "truth"],
        any_min=2,
        open_ended=False,
        max_tokens=350,
    ),

    Question(
        id="L-H1", category="Logic", lang="en", difficulty="Hard",
        prompt=(
            "Five houses in a row. Each house has a different color, "
            "owner of different nationality, different pet, drink, and sport.\n"
            "Clues:\n"
            "1. The Brit lives in the red house.\n"
            "2. The Swede keeps dogs.\n"
            "3. The Dane drinks tea.\n"
            "4. The green house is immediately to the left of the white house.\n"
            "5. The green house owner drinks coffee.\n"
            "6. The person who plays polo keeps birds.\n"
            "7. The owner of the yellow house plays hockey.\n"
            "8. The man in the center house drinks milk.\n"
            "9. The Norwegian lives in the first house.\n"
            "10. The man who plays baseball lives next to the cat owner.\n"
            "11. The horse owner lives next to the hockey player.\n"
            "12. The person who plays billiards drinks beer.\n"
            "13. The German plays soccer.\n"
            "14. The Norwegian lives next to the blue house.\n"
            "15. The baseball player lives next to the water drinker.\n"
            "WHO OWNS THE FISH?"
        ),
        reference="The German owns the fish.",
        any_keywords=["german", "fish"],
        any_min=2,
        max_tokens=600,
    ),

    Question(
        id="L-H2", category="Logic", lang="vi", difficulty="Hard",
        prompt=(
            "Co 4 nguoi: An, Binh, Chi, Dung. "
            "Moi nguoi mac mot mau ao khac nhau: do, xanh, vang, trang.\n"
            "- An khong mac do va khong mac xanh.\n"
            "- Binh mac vang.\n"
            "- Chi khong mac trang.\n"
            "Ai mac ao mau gi? Liet ke day du ca 4 nguoi."
        ),
        reference="An=trang, Binh=vang, Chi=xanh, Dung=do.",
        any_keywords=["an", "binh", "chi", "dung", "vang", "xanh", "trang", "do"],
        any_min=6,
        exact_numbers=[],
        max_tokens=350,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 2: MATHEMATICS (GSM8K / MATH style)
    # ════════════════════════════════════════════════════════

    Question(
        id="M-E1", category="Math", lang="en", difficulty="Easy",
        prompt=(
            "A store sells apples for $0.50 each. "
            "Maria buys 12 apples and pays with a $10 bill. "
            "How much change does she get?"
        ),
        reference="$4.00 change. 12 × $0.50 = $6.00; $10 - $6 = $4.",
        exact_numbers=["4", "4.00"],
        max_tokens=200,
    ),

    Question(
        id="M-E2", category="Math", lang="vi", difficulty="Easy",
        prompt=(
            "Mot to hop sach chia deu cho 6 ke. Moi ke nhan duoc 8 quyen. "
            "Neu chia cho 12 ke, moi ke nhan duoc bao nhieu quyen?"
        ),
        reference="Tong = 6*8 = 48 quyen. Chia cho 12 ke: 48/12 = 4 quyen/ke.",
        exact_numbers=["4", "48"],
        max_tokens=200,
    ),

    Question(
        id="M-M1", category="Math", lang="en", difficulty="Medium",
        prompt=(
            "A train travels at 60 mph for 2 hours, then at 80 mph for 3 hours. "
            "What is the average speed for the entire trip? "
            "Important: do NOT just average 60 and 80. Show full working."
        ),
        reference="Total distance = 120+240 = 360 miles. Total time = 5 hours. Avg speed = 72 mph.",
        exact_numbers=["72"],
        any_keywords=["360", "5 hour", "total distance", "total time"],
        any_min=2,
        max_tokens=300,
    ),

    Question(
        id="M-M2", category="Math", lang="vi", difficulty="Medium",
        prompt=(
            "Voi A mot minh day day be trong 6 gio. "
            "Voi B mot minh day day be trong 3 gio. "
            "Mo ca hai voi cung luc thi bao lau day day be? "
            "Trinh bay cach tinh chi tiet."
        ),
        reference="Toc do: A=1/6 be/gio, B=1/3 be/gio. Tong=1/6+2/6=3/6=1/2 be/gio. Thoi gian=2 gio.",
        exact_numbers=["2"],
        any_keywords=["1/6", "1/3", "1/2"],
        any_min=2,
        max_tokens=350,
    ),

    Question(
        id="M-M3", category="Math", lang="en", difficulty="Medium",
        prompt=(
            "Solve for x: 2x^2 - 5x - 3 = 0. "
            "Use any method (factoring, quadratic formula, or completing the square). "
            "Show all steps."
        ),
        reference="x = 3 or x = -0.5 (discriminant=49, roots via quadratic formula).",
        exact_numbers=["3", "-1/2"],  # -1/2 covers -0.5 after strip_latex conversion
        max_tokens=400,
    ),

    Question(
        id="M-H1", category="Math", lang="en", difficulty="Hard",
        prompt=(
            "A merchant sells an item at 20% profit. "
            "If he had bought it for 25% less and sold it for $10.50 less, "
            "he would have made 30% profit. "
            "Find the original cost price of the item."
        ),
        reference=(
            "Let CP=x. SP=1.2x. New CP=0.75x. New SP=1.2x-10.50=1.3*0.75x=0.975x. "
            "=> 1.2x-10.50=0.975x => 0.225x=10.50 => x=$46.67."
        ),
        exact_numbers=["46.67", "46.6", "140/3"],  # 140/3 is simplified form of 280/6
        any_keywords=["0.225", "0.975", "46"],
        any_min=1,
        max_tokens=500,
    ),

    Question(
        id="M-H2", category="Math", lang="vi", difficulty="Hard",
        prompt=(
            "Mot hinh thang co day lon hon day nho 8 cm. "
            "Chieu cao bang trung binh cong cua hai day. "
            "Dien tich hinh thang la 90 cm2. "
            "Tinh do dai cac canh day."
        ),
        reference=(
            "Goi day nho=a, day lon=a+8, chieu cao=(2a+8)/2=a+4. "
            "DT=(a+a+8)/2*(a+4)=(2a+8)/2*(a+4)=(a+4)^2=90. "
            "a+4=sqrt(90)~9.49. a~5.49, a+8~13.49. "
            "Hoac: (a+4)^2=90 => a=sqrt(90)-4."
        ),
        any_keywords=["90", "sqrt", "a+4", "9.49", "5.49"],
        any_min=2,
        max_tokens=500,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 3: CODING  (HumanEval / MBPP style)
    # ════════════════════════════════════════════════════════

    Question(
        id="C-E1", category="Coding", lang="en", difficulty="Easy",
        prompt=(
            "Write a Python function `sum_evens(lst)` that returns the sum of all "
            "even numbers in a list. Example: sum_evens([1,2,3,4,5,6]) should return 12."
        ),
        reference="def sum_evens(lst): return sum(x for x in lst if x % 2 == 0)",
        keywords=["def sum_evens"],
        any_keywords=["% 2", "% 2 == 0", "even", "sum"],
        any_min=2,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(sum_evens([1,2,3,4,5,6]))\n"
            "print(sum_evens([]))\n"
            "print(sum_evens([1,3,5]))\n"
        ),
        expected_output="12\n0\n0",
        max_tokens=300,
    ),

    Question(
        id="C-E2", category="Coding", lang="en", difficulty="Easy",
        prompt=(
            "What is the output of this Python code?\n\n"
            "x = [1, 2, 3]\n"
            "y = x\n"
            "y.append(4)\n"
            "print(x)\n\n"
            "Explain WHY in one sentence."
        ),
        reference="[1, 2, 3, 4] because y = x makes both point to the same list object in memory.",
        any_keywords=["[1, 2, 3, 4]", "reference", "same", "object", "memory"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="C-M1", category="Coding", lang="en", difficulty="Medium",
        prompt=(
            "Write a Python function `is_prime(n)` that returns True if n is prime, "
            "False otherwise. Handle edge cases: n<2, n=2, even numbers. "
            "Optimize to check divisors only up to sqrt(n)."
        ),
        reference="Efficient primality test with sqrt optimization and edge case handling.",
        keywords=["def is_prime"],
        any_keywords=["return False", "return True", "** 0.5", "sqrt", "% 2"],
        any_min=3,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "results = [is_prime(n) for n in [-1, 0, 1, 2, 3, 4, 17, 100]]\n"
            "print(results)\n"
        ),
        expected_output="[False, False, False, True, True, False, True, False]",
        max_tokens=400,
    ),

    Question(
        id="C-M2", category="Coding", lang="vi", difficulty="Medium",
        prompt=(
            "Viet ham Python `dem_tu(chuoi)` dem so tu trong mot chuoi. "
            "Tu duoc ngan cach bang khoang trang (co the co nhieu khoang trang lien tiep). "
            "Chuoi rong tra ve 0. "
            "Vi du: dem_tu('  xin   chao  ') = 2."
        ),
        reference="def dem_tu(chuoi): return len(chuoi.split()) if chuoi.strip() else 0",
        keywords=["def dem_tu"],
        any_keywords=["split", "len", "strip"],
        any_min=2,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(dem_tu('  xin   chao  '))\n"
            "print(dem_tu(''))\n"
            "print(dem_tu('hello world python'))\n"
        ),
        expected_output="2\n0\n3",
        max_tokens=300,
    ),

    Question(
        id="C-M3", category="Coding", lang="en", difficulty="Medium",
        prompt=(
            "Debug this Python function — it has a bug. Find and fix it:\n\n"
            "def factorial(n):\n"
            "    if n == 0:\n"
            "        return 0\n"
            "    return n * factorial(n - 1)\n\n"
            "Show the corrected function and explain what was wrong."
        ),
        reference="Bug: base case returns 0 instead of 1. Fix: return 1 when n==0.",
        any_keywords=["return 1", "base case", "0", "wrong", "bug", "fix"],
        any_min=3,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(factorial(0))\n"
            "print(factorial(5))\n"
            "print(factorial(1))\n"
        ),
        expected_output="1\n120\n1",
        max_tokens=350,
    ),

    Question(
        id="C-H1", category="Coding", lang="en", difficulty="Hard",
        prompt=(
            "Implement a Python function `lcs(s1, s2)` that returns the length of "
            "the Longest Common Subsequence of two strings using dynamic programming.\n"
            "Example: lcs('ABCBDAB', 'BDCAB') should return 4."
        ),
        reference="DP table approach, O(m*n) time. lcs('ABCBDAB','BDCAB')=4.",
        keywords=["def lcs"],
        any_keywords=["dp", "table", "range", "max", "for"],
        any_min=3,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "print(lcs('ABCBDAB', 'BDCAB'))\n"
            "print(lcs('', 'ABC'))\n"
            "print(lcs('ABC', 'ABC'))\n"
        ),
        expected_output="4\n0\n3",
        max_tokens=600,
    ),

    Question(
        id="C-H2", category="Coding", lang="vi", difficulty="Hard",
        prompt=(
            "Viet ham Python `tim_tat_ca_hoan_vi(lst)` tra ve danh sach tat ca hoan vi "
            "cua mot danh sach khong dung ham co san (khong dung itertools). "
            "Vi du: tim_tat_ca_hoan_vi([1,2,3]) tra ve tat ca 6 hoan vi.\n"
            "Chi can tra ve so luong hoan vi la dung."
        ),
        reference="Backtracking recursion. 3! = 6 permutations.",
        keywords=["def tim_tat_ca_hoan_vi"],
        any_keywords=["for", "recursive", "append", "swap", "backtrack"],
        any_min=2,
        code_to_exec=(
            "RESPONSE_CODE\n"
            "result = tim_tat_ca_hoan_vi([1,2,3])\n"
            "print(len(result))\n"
            "result2 = tim_tat_ca_hoan_vi([1])\n"
            "print(len(result2))\n"
        ),
        expected_output="6\n1",
        max_tokens=600,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 4: GENERAL KNOWLEDGE  (MMLU style)
    # ════════════════════════════════════════════════════════

    Question(
        id="G-E1", category="Knowledge", lang="en", difficulty="Easy",
        prompt=(
            "What causes seasons on Earth? "
            "Answer in 2 sentences. Hint: it is NOT because Earth is closer to the Sun."
        ),
        reference="Earth's axial tilt (~23.5 degrees) causes seasons, not distance from the Sun.",
        keywords=["tilt"],
        any_keywords=["axis", "axial", "23.5", "hemisphere", "angle"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="G-E2", category="Knowledge", lang="vi", difficulty="Easy",
        prompt=(
            "Nuoc soi o nhiet do bao nhieu do C o ap suat khi quyen binh thuong? "
            "Va tai sao tren nui cao nuoc soi o nhiet do thap hon?"
        ),
        reference="100 do C. Tren nui cao ap suat khi quyen thap hon, nen nuoc soi o nhiet do thap hon.",
        exact_numbers=["100"],
        any_keywords=["ap suat", "nui", "thap hon", "100"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="G-M1", category="Knowledge", lang="en", difficulty="Medium",
        prompt=(
            "Name THREE structural or chemical differences between DNA and RNA. "
            "Be specific and accurate."
        ),
        reference=(
            "1) Sugar: DNA has deoxyribose, RNA has ribose. "
            "2) Base: DNA uses thymine (T), RNA uses uracil (U). "
            "3) Strands: DNA is double-stranded, RNA is typically single-stranded."
        ),
        any_keywords=["deoxyribose", "ribose", "thymine", "uracil", "double", "single"],
        any_min=4,
        max_tokens=300,
    ),

    Question(
        id="G-M2", category="Knowledge", lang="vi", difficulty="Medium",
        prompt=(
            "Giai thich nguyen ly quang hop (photosynthesis). "
            "Viet phuong trinh hoa hoc tong quat va giai thich y nghia tung thanh phan. "
            "Phan ung xay ra o dau trong te bao?"
        ),
        reference=(
            "6CO2 + 6H2O + anh sang -> C6H12O6 + 6O2. "
            "Xay ra trong luc lap (chloroplast). "
            "CO2 tu khi quyen, H2O tu re cay, nang luong tu anh sang, "
            "san pham la glucose va O2."
        ),
        any_keywords=["co2", "h2o", "glucose", "o2", "luc lap", "chloroplast", "anh sang"],
        any_min=4,
        max_tokens=350,
    ),

    Question(
        id="G-H1", category="Knowledge", lang="en", difficulty="Hard",
        prompt=(
            "Explain the key differences between Type I and Type II errors in statistics. "
            "Give a real-world medical example illustrating each type, "
            "and explain which is typically more dangerous in medical testing and why."
        ),
        reference=(
            "Type I (false positive): reject H0 when true. "
            "Type II (false negative): fail to reject H0 when false. "
            "Medical: Type II (missing disease) usually more dangerous."
        ),
        any_keywords=["false positive", "false negative", "type i", "type ii", "alpha", "beta", "miss"],
        any_min=3,
        max_tokens=450,
    ),

    Question(
        id="G-H2", category="Knowledge", lang="vi", difficulty="Hard",
        prompt=(
            "So sanh co che hoat dong cua vaccine mRNA (nhu Pfizer COVID-19) "
            "voi vaccine truyen thong (nhu vaccine cum). "
            "Neu ro: each loai kich hoat mien dich nhu the nao, "
            "uu nhuoc diem chinh cua moi loai."
        ),
        reference=(
            "mRNA: dua vao te bao dich ma protein gai, kich mien dich, mRNA khong vao nhan. "
            "Truyen thong: virus bat hoat/song yeu/protein. "
            "mRNA: nhanh san xuat, de bien the; truyen thong: chung minh an toan lau dai."
        ),
        any_keywords=["mrna", "protein", "mien dich", "virus", "bat hoat", "kich hoat"],
        any_min=3,
        max_tokens=500,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 5: CRITICAL THINKING & FALLACIES
    # ════════════════════════════════════════════════════════

    Question(
        id="T-E1", category="Critical", lang="en", difficulty="Easy",
        prompt=(
            "Identify the logical fallacy in this argument:\n"
            "'My grandfather smoked all his life and lived to 95. "
            "Therefore, smoking is not harmful.'"
        ),
        reference="Anecdotal evidence / hasty generalization. One case cannot generalize to all.",
        any_keywords=["anecdot", "hasty", "generali", "sample", "one case", "fallacy"],
        any_min=2,
        max_tokens=200,
    ),

    Question(
        id="T-E2", category="Critical", lang="vi", difficulty="Easy",
        prompt=(
            "Phan tich loi tu duy trong cau sau:\n"
            "'Toi uong nuoc chanh moi sang va chua bao gio bi ung thu. "
            "Vay nuoc chanh ngan ngua ung thu.'"
        ),
        reference="Loi tuong quan nhan qua (correlation != causation). Mot mau don le khong du chung minh.",
        any_keywords=["tuong quan", "nhan qua", "correlation", "causation", "mau", "chung minh"],
        any_min=3,
        max_tokens=250,
    ),

    Question(
        id="T-M1", category="Critical", lang="en", difficulty="Medium",
        prompt=(
            "A study claims: 'Students who eat breakfast score higher on exams.' "
            "List THREE alternative explanations (confounders) that could explain "
            "this correlation WITHOUT breakfast causing better scores."
        ),
        reference=(
            "Confounders: socioeconomic status, sleep quality, parental involvement, "
            "general health habits, school type."
        ),
        any_keywords=["confounder", "correlation", "socioeconomic", "habit", "alternative", "cause"],
        any_min=3,
        max_tokens=300,
    ),

    Question(
        id="T-M2", category="Critical", lang="vi", difficulty="Medium",
        prompt=(
            "Spot the logical fallacy and name it:\n"
            "'Tat ca lanh dao vi dai deu la nguoi dam mao hiem. "
            "Elon Musk la nguoi dam mao hiem. "
            "Vay Elon Musk la lanh dao vi dai.'"
        ),
        reference="Affirming the consequent (khang dinh hau qua). Dam mao hiem la dieu kien can nhung khong du.",
        any_keywords=["consequent", "hau qua", "can", "du", "fallacy", "khong du"],
        any_min=2,
        max_tokens=300,
    ),

    Question(
        id="T-H1", category="Critical", lang="en", difficulty="Hard",
        prompt=(
            "A pharmaceutical company releases a study showing their new drug reduces "
            "heart attacks by 50% (relative risk reduction). "
            "However, the absolute risk went from 2% to 1%. "
            "Explain: (a) the difference between relative and absolute risk reduction, "
            "(b) why the 50% claim is misleading, "
            "(c) what number-needed-to-treat (NNT) means here."
        ),
        reference=(
            "RRR=50% (1%/2%), ARR=1% (2%-1%). "
            "NNT=1/ARR=100 (treat 100 patients to prevent 1 heart attack). "
            "50% sounds dramatic but absolute benefit is small."
        ),
        any_keywords=["absolute", "relative", "nnt", "number needed", "1%", "mislead", "100"],
        any_min=4,
        max_tokens=500,
    ),

    Question(
        id="T-H2", category="Critical", lang="vi", difficulty="Hard",
        prompt=(
            "Phan tich tranh luan sau va chi ra tat ca cac loi lap luan:\n\n"
            "'Chinh sach mo cua hang ban le 24/7 se gay hai cho xa hoi. "
            "Nhung nguoi phan doi la nhung ke luoi bieng khong muon lam viec. "
            "Tat ca cac nuoc van minh deu co cua hang mo 24/7. "
            "Neu ban khong dong y, ban dang ung ho nen kinh te lac hau.'"
        ),
        reference=(
            "Cac loi: Ad hominem (tan cong nguoi phan doi), "
            "Appeal to majority/civilization (fallacy of appeal to authority/bandwagon), "
            "False dilemma (chi co 2 lua chon), "
            "Non sequitur (ket luan khong theo sau tien de)."
        ),
        any_keywords=["ad hominem", "straw man", "false dilemma", "bandwagon", "appeal", "loi"],
        any_min=3,
        open_ended=True,
        max_tokens=500,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 6: LANGUAGE & COMPREHENSION
    # ════════════════════════════════════════════════════════

    Question(
        id="LA-E1", category="Language", lang="en", difficulty="Easy",
        prompt=(
            "Rewrite this sentence to fix the grammatical error:\n"
            "'The team have decided to cancelled their plans due to the weathers.'"
        ),
        reference="'The team has decided to cancel their plans due to the weather.'",
        any_keywords=["has decided", "cancel", "weather"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="LA-E2", category="Language", lang="vi", difficulty="Easy",
        prompt=(
            "Viet lai cau sau theo gong van trang trong hon, "
            "giu nguyen y nghia:\n"
            "'May tinh cua tao bi hu roi, buon qua.'"
        ),
        reference="'May tinh cua toi da bi hong, toi cam thay rat buon long.'",
        any_keywords=["may tinh", "hong", "buon"],
        any_min=2,
        max_tokens=150,
    ),

    Question(
        id="LA-M1", category="Language", lang="en", difficulty="Medium",
        prompt=(
            "Read this paragraph and answer: What is the author's main argument, "
            "and what evidence do they provide?\n\n"
            "'Remote work has transformed modern employment. Studies show that remote "
            "workers report 22% higher productivity and 40% less stress. Companies "
            "like GitLab and Automattic have operated fully remotely for years with "
            "record profits. Critics argue that collaboration suffers, but data from "
            "Stanford shows creative problem-solving actually improves with async communication.'"
        ),
        reference=(
            "Main argument: remote work is beneficial. "
            "Evidence: 22% productivity increase, 40% less stress, GitLab/Automattic success, Stanford data."
        ),
        any_keywords=["remote", "productivity", "22%", "stanford", "argument", "evidence"],
        any_min=3,
        max_tokens=300,
    ),

    Question(
        id="LA-M2", category="Language", lang="vi", difficulty="Medium",
        prompt=(
            "Tom tat doan van sau trong khong qua 3 cau, "
            "giu lai cac y chinh:\n\n"
            "'Bien doi khi hau dang anh huong nghiem trong den nong nghiep Viet Nam. "
            "Han han keo dai o mien Trung, lu lut o dong bang song Cuu Long, "
            "va nhiet do tang lam giam nang suat lua. "
            "Chinh phu dang thuc hien cac bien phap thich ung nhu trong cac giong lua "
            "chiu nhiet va xay dung he thong tuoi tieu hien dai. "
            "Tuy nhien, cac chuyen gia canh bao rang neu khong co hanh dong quoc te, "
            "Viet Nam co the mat di 12% dien tich dat canh tac vao nam 2050.'"
        ),
        reference=(
            "Bien doi khi hau gay tac dong nghiem trong den nong nghiep Viet Nam (han han, lu lut, nang suat giam). "
            "Chinh phu dang co bien phap thich ung. "
            "Khong hanh dong quoc te, Viet Nam co the mat 12% dat canh tac vao 2050."
        ),
        any_keywords=["bien doi", "nong nghiep", "han han", "12%", "2050", "thich ung"],
        any_min=3,
        max_tokens=250,
    ),

    Question(
        id="LA-H1", category="Language", lang="en", difficulty="Hard",
        prompt=(
            "Translate this Vietnamese proverb to English and explain its cultural meaning:\n"
            "'Mot cay lam chang nen non, ba cay chum lai nen hon nui cao.'"
        ),
        reference=(
            "Literal: 'One tree cannot make a mountain; three trees together make a high mountain.' "
            "Meaning: Unity and collective effort achieve what individuals cannot alone. "
            "Cultural: emphasizes community over individualism in Vietnamese culture."
        ),
        any_keywords=["unity", "together", "collective", "mountain", "tree", "alone", "community"],
        any_min=3,
        max_tokens=300,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 7: COMMON SENSE & WORLD KNOWLEDGE (HellaSwag)
    # ════════════════════════════════════════════════════════

    Question(
        id="CS-E1", category="Common Sense", lang="en", difficulty="Easy",
        prompt=(
            "Which continuation makes most sense?\n"
            "A person is cooking pasta. They boil water, add salt, and put in the pasta.\n"
            "A) They immediately serve the raw pasta to guests.\n"
            "B) They wait 8-10 minutes, then drain and serve.\n"
            "C) They add ice cubes to stop the water from boiling.\n"
            "D) They put the pot in the refrigerator.\n"
            "Answer with the letter and briefly explain."
        ),
        reference="B - wait 8-10 minutes then drain and serve (standard pasta cooking).",
        keywords=["b"],
        max_tokens=150,
    ),

    Question(
        id="CS-E2", category="Common Sense", lang="vi", difficulty="Easy",
        prompt=(
            "Tiep theo hop ly nhat la gi?\n"
            "Mot nguoi dang o trong nha va nghe thay tieng sam set lon o ben ngoai.\n"
            "A) Ho chay ra ngoai de nhin troi.\n"
            "B) Ho tat tat ca thiet bi dien va tram that an toan trong nha.\n"
            "C) Ho bat tat ca den de nhin duoc ro hon.\n"
            "D) Ho mo cua so de nghe sam trot ro hon.\n"
            "Chon dap an va giai thich."
        ),
        reference="B - tat thiet bi dien va tram an toan la hanh dong an toan nhat khi co bao.",
        keywords=["b"],
        max_tokens=150,
    ),

    Question(
        id="CS-M1", category="Common Sense", lang="en", difficulty="Medium",
        prompt=(
            "A doctor prescribes medication and tells a patient to take it "
            "'three times a day with food.' The patient has breakfast at 7am, "
            "lunch at 12pm, and dinner at 6pm. "
            "The patient wakes up at 3am feeling unwell and realizes they forgot the evening dose. "
            "What should the patient most likely do, and why?"
        ),
        reference=(
            "Skip the missed dose and take the next one as scheduled at breakfast. "
            "Do not double dose. General medical advice is never to catch up with double doses."
        ),
        any_keywords=["skip", "next dose", "do not double", "morning", "breakfast"],
        any_min=2,
        max_tokens=250,
    ),

    Question(
        id="CS-M2", category="Common Sense", lang="vi", difficulty="Medium",
        prompt=(
            "Ban dang o mot thanh pho la la. Ban het tien va pin dien thoai sap het. "
            "Ban can tim nha hang can nhat. Sap xep thu tu uu tien cac hanh dong sau:\n"
            "A) Tim wifi cong cong de dung ban do\n"
            "B) Hoi nguoi di duong\n"
            "C) Tim noi sac dien thoai truoc\n"
            "D) Di bo theo ngu giac tim nha hang\n"
            "Giai thich lua chon cua ban."
        ),
        reference=(
            "Uu tien: B (hoi nguoi di duong - nhanh nhat, khong can pin), "
            "sau do A (neu con pin), sau C neu can ban do lau dai, D la phoi lieu."
        ),
        any_keywords=["hoi", "nguoi", "nhanh", "pin", "wifi"],
        any_min=2,
        open_ended=True,
        max_tokens=300,
    ),

    # ════════════════════════════════════════════════════════
    # CATEGORY 8: CALIBRATION & SELF-AWARENESS
    # ════════════════════════════════════════════════════════

    Question(
        id="CA-E1", category="Calibration", lang="en", difficulty="Easy",
        prompt=(
            "What is 2 + 2? Answer with just the number, then rate your confidence "
            "as a percentage (0-100%)."
        ),
        reference="4. Confidence should be 100%.",
        exact_numbers=["4"],
        any_keywords=["100", "certain", "sure", "confident"],
        any_min=1,
        max_tokens=100,
    ),

    Question(
        id="CA-M1", category="Calibration", lang="en", difficulty="Medium",
        prompt=(
            "I will ask you about the exact population of Ho Chi Minh City as of today. "
            "Before answering: state clearly if you are CERTAIN or UNCERTAIN, "
            "give your best estimate with a range, "
            "and explain why you may not be perfectly accurate."
        ),
        reference=(
            "~9-13 million (metro area). Should express uncertainty about exact current figures, "
            "mention knowledge cutoff, and give a reasonable range."
        ),
        any_keywords=["million", "uncertain", "estimate", "range", "cutoff", "approximate"],
        any_min=3,
        max_tokens=300,
    ),

    Question(
        id="CA-H1", category="Calibration", lang="en", difficulty="Hard",
        prompt=(
            "Answer this question, but BEFORE answering, assess your confidence (0-100%) "
            "and explain your uncertainty sources:\n\n"
            "What was the exact GDP of Vietnam in Q3 2024, in USD?"
        ),
        reference=(
            "Should express uncertainty (exact quarterly GDP is hard to recall precisely), "
            "give approximate range (~100-120B USD for Q3 estimate), cite knowledge cutoff limitation."
        ),
        any_keywords=["uncertain", "estimate", "billion", "gdp", "range", "cutoff", "exact"],
        any_min=4,
        open_ended=True,
        max_tokens=350,
    ),
]

# Deduplicate by id (keep last occurrence)
_seen: dict[str, Question] = {}
for q in QUESTIONS:
    _seen[q.id] = q
QUESTIONS = list(_seen.values())


# ── API ───────────────────────────────────────────────────────────────────────

def api_post(endpoint: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib.request.Request(
        f"{API_BASE_URL}/{endpoint}",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        raise ConnectionError(f"API unreachable ({API_BASE_URL}): {e}") from e


def list_models() -> list[str]:
    headers = {}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    req = urllib.request.Request(f"{API_BASE_URL}/models", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return [m["id"] for m in data.get("data", [])]


def ping_api() -> bool:
    """
    Test kết nối API và hiển thị danh sách models.
    Return True nếu kết nối thành công.
    """
    print(f"\n{BLD}{C}Pinging API:{RST} {API_BASE_URL}")
    print(f"  Auth: {'Bearer ***' if API_KEY else 'None (local mode)'}\n")
    try:
        models = list_models()
        if not models:
            print(f"{Y}⚠ Connected but no models found!{RST}")
            return False

        print(f"{G}✓ Connected! {len(models)} model(s) available:{RST}")
        for m in models:
            marker = f"  {G}<-- default{RST}" if m == DEFAULT_MODEL else ""
            print(f"  • {m}{marker}")

        # Test chat message với model đầu tiên
        test_model = models[0]
        print(f"\n{DIM}Testing chat with: {test_model}...{RST}")
        t0 = time.time()
        resp, latency = chat(test_model, "Say 'OK' in one word.", 10, 0.0)
        print(f"{G}✓ Chat OK ({latency:.1f}s): {resp.strip()[:60]!r}{RST}")
        return True
    except Exception as e:
        print(f"{R}✗ Connection failed: {e}{RST}")
        print(f"{Y}  Hint: Check OPENAI_BASE_URL and OPENAI_API_KEY settings{RST}")
        return False


def chat(model: str, prompt: str, max_tokens: int, temperature: float,
         system: str = "") -> tuple[str, float]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.time()
    resp = api_post("chat/completions", {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    })
    latency = time.time() - t0
    return resp["choices"][0]["message"]["content"], latency


# ── Scoring Engine ────────────────────────────────────────────────────────────

def extract_code_block(text: str) -> str:
    """Extract the first Python code block from a response."""
    # Try fenced code block first
    patterns = [
        r"```python\s*(.*?)```",
        r"```\s*(.*?)```",
        r"`([^`]+)`",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    # Fallback: lines that look like code
    lines = text.splitlines()
    code_lines = [l for l in lines if l.startswith("def ") or l.startswith("    ")
                  or l.startswith("return ") or "=" in l]
    return "\n".join(code_lines) if len(code_lines) >= 3 else text


def run_code(template: str, response: str) -> tuple[bool, str, str]:
    """
    Extract code from response, inject into template, execute in sandbox.
    Returns (passed, actual_output, error_message).
    """
    extracted = extract_code_block(response)
    source = template.replace("RESPONSE_CODE", extracted)
    try:
        result = subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True, text=True,
            timeout=CODE_TIMEOUT,
            encoding="utf-8",
        )
        actual = result.stdout.strip()
        err = result.stderr.strip()
        return True, actual, err
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def score_question(q: Question, response: str) -> tuple[float, str, str]:
    """
    Multi-method scoring.
    Returns (raw_score 0.0-1.0, method_used, notes).
    """
    resp_lower = response.lower()
    resp_norm = strip_vi(resp_lower)  # for Vietnamese diacritic matching
    resp_plain = strip_latex(resp_lower)  # for LaTeX notation matching
    notes_parts: list[str] = []
    scores: list[float] = []
    methods: list[str] = []

    # Method 1: Code execution (highest priority for coding questions)
    if q.code_to_exec and q.expected_output:
        ok, actual, err = run_code(q.code_to_exec, response)
        if ok:
            # Trim extra prefix lines if actual has more lines than expected
            # (handles cases where model includes example print() calls)
            expected_lines = q.expected_output.strip().splitlines()
            actual_lines = actual.strip().splitlines()
            if len(actual_lines) > len(expected_lines):
                actual = "\n".join(actual_lines[-len(expected_lines):])

            if actual == q.expected_output.strip():
                return 1.0, "code_exec:PASS", f"output={actual!r}"
            else:
                # Partial: check if numbers match even if formatting differs
                actual_nums = set(re.findall(r"-?\d+\.?\d*", actual))
                expected_nums = set(re.findall(r"-?\d+\.?\d*", q.expected_output))
                partial = len(actual_nums & expected_nums) / max(len(expected_nums), 1)
                scores.append(partial * 0.6)  # partial credit, capped at 60%
                methods.append(f"code_exec:PARTIAL({partial:.0%})")
                notes_parts.append(f"expected={q.expected_output!r} got={actual!r}")
        else:
            notes_parts.append(f"exec_error: {err[:80]}")
            # Fall through to keyword scoring

    # Method 2: Exact numeric match
    if q.exact_numbers:
        hits = [n for n in q.exact_numbers if n in resp_lower or n in response or n in resp_plain]
        ratio = len(hits) / len(q.exact_numbers)
        scores.append(ratio)
        methods.append(f"exact_num:{len(hits)}/{len(q.exact_numbers)}")
        if ratio < 1.0:
            missing = [n for n in q.exact_numbers if n not in resp_lower and n not in response and n not in resp_plain]
            notes_parts.append(f"missing numbers: {missing}")

    # Method 3: Required keywords (ALL must match)
    if q.keywords:
        hits = [kw for kw in q.keywords if kw.lower() in resp_lower or strip_vi(kw.lower()) in resp_norm or kw.lower() in resp_plain]
        ratio = len(hits) / len(q.keywords)
        scores.append(ratio)
        methods.append(f"kw_all:{len(hits)}/{len(q.keywords)}")
        missing = [kw for kw in q.keywords if kw.lower() not in resp_lower and strip_vi(kw.lower()) not in resp_norm and kw.lower() not in resp_plain]
        if missing:
            notes_parts.append(f"missing required: {missing}")

    # Method 4: Any-keywords (at least any_min must match)
    if q.any_keywords and q.any_min > 0:
        hits = [kw for kw in q.any_keywords if kw.lower() in resp_lower or strip_vi(kw.lower()) in resp_norm or kw.lower() in resp_plain]
        n = len(hits)
        ratio = min(n / q.any_min, 1.0)  # capped at 1.0
        scores.append(ratio)
        methods.append(f"kw_any:{n}/{q.any_min}")
        if n < q.any_min:
            notes_parts.append(f"any_kw hits={n} (need {q.any_min}): {hits}")

    # Aggregate
    if not scores:
        # No scoring method configured → mark for manual review
        return 0.5, "no_method", "open_ended:needs_judge"

    raw = sum(scores) / len(scores)

    # Penalty: response too short (only for open_ended questions)
    # For keyword/number/code questions, response length doesn't matter
    if q.open_ended and len(response.strip()) < 20:
        raw = max(0.0, raw - 0.4)
        notes_parts.append("response too short")

    method_str = " | ".join(methods)
    return min(raw, 1.0), method_str, "; ".join(notes_parts) if notes_parts else "ok"


def llm_judge(
    model_judge: str,
    question: Question,
    response: str,
) -> tuple[float, str]:
    """
    Use a second model as judge. Returns (raw_score 0.0-1.0, reasoning).
    Implements rubric-based scoring with chain-of-thought.
    """
    rubric = f"""
REFERENCE ANSWER: {question.reference}

SCORING RUBRIC (score 0-3):
3 = Completely correct, addresses all key points, no factual errors
2 = Mostly correct, minor omissions or imprecision
1 = Partially correct, major omission OR one factual error
0 = Incorrect, off-topic, or completely wrong

TASK: Evaluate the following AI response to the question.
First, write 1-2 sentences explaining your reasoning.
Then output SCORE: X (where X is 0, 1, 2, or 3).
"""
    prompt = (
        f"QUESTION: {question.prompt}\n\n"
        f"AI RESPONSE: {response}\n\n"
        f"{rubric}"
    )
    try:
        judge_response, _ = chat(
            model_judge, prompt,
            max_tokens=300, temperature=0.0,
            system="You are a strict but fair academic evaluator. Be concise.",
        )
        # Extract score
        m = re.search(r"SCORE:\s*([0-3])", judge_response, re.IGNORECASE)
        if m:
            raw = int(m.group(1)) / 3.0
            return raw, judge_response.strip()
        return 0.5, f"could not parse score from: {judge_response[:100]}"
    except Exception as e:
        return 0.5, f"judge error: {e}"


# ── Display ───────────────────────────────────────────────────────────────────

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
    # Use \r to overwrite the "sending..." indicator; pad to 100 to clear any trailing chars
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


# ── Runner ────────────────────────────────────────────────────────────────────

def run_all(
    model: str,
    questions: list[Question],
    verbose: bool = False,
    judge_model: Optional[str] = None,
) -> list[Result]:
    results: list[Result] = []
    total = len(questions)
    system = (
        "You are an AI being rigorously tested for intelligence. "
        "Answer accurately and concisely. "
        "For Vietnamese questions, respond in Vietnamese. "
        "For English questions, respond in English. "
        "Show your reasoning when asked."
    )

    print(f"\n{BLD}{C}Running {total} questions on:{RST} {model}\n")

    for i, q in enumerate(questions, 1):
        # Show pending indicator before sending (will be overwritten by print_inline after response)
        cat_short = q.category[:7]
        print(f"\r{DIM}[{i:>2}/{total}]{RST} {q.id:<8} {Y}{cat_short:<8}{RST} → {DIM}sending...{RST}", end="", flush=True)

        try:
            response, latency = chat(
                model, q.prompt, q.max_tokens, q.temperature, system=system
            )
        except Exception as e:
            print(f"{R}[{i}/{total}] {q.id} ERROR: {e}{RST}")
            w = DIFF_WEIGHT[q.difficulty] * q.base_points
            results.append(Result(
                question=q, response="", raw_score=0.0,
                weighted_score=0.0, max_weighted=float(w),
                method="error", latency=0.0, notes=str(e),
            ))
            continue

        raw, method, notes = score_question(q, response)

        # LLM-as-Judge for open-ended or when judge is available
        judge_reasoning = ""
        if judge_model and (q.open_ended or raw < 0.5):
            j_score, j_reason = llm_judge(judge_model, q, response)
            if q.open_ended:
                raw = j_score
                method = f"llm_judge | {method}"
            else:
                # Blend: 60% keyword, 40% judge
                raw = 0.6 * raw + 0.4 * j_score
                method = f"blend | {method}"
            judge_reasoning = j_reason

        weight = DIFF_WEIGHT[q.difficulty]
        weighted = raw * weight * q.base_points
        max_w    = weight * q.base_points

        result = Result(
            question=q, response=response,
            raw_score=raw, weighted_score=weighted, max_weighted=float(max_w),
            method=method, latency=latency, notes=notes,
            judge_reasoning=judge_reasoning,
        )
        results.append(result)

        if verbose:
            print_verbose(result, i, total)
        else:
            print_inline(result, i, total)

    return results


# ── Report ────────────────────────────────────────────────────────────────────

def save_report(results: list[Result], model: str) -> str:
    # Create report directory if not exists
    os.makedirs(REPORT_DIR, exist_ok=True)

    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(REPORT_DIR, f"report_{ts}.json")
    total_got = sum(r.weighted_score for r in results)
    total_max = sum(r.max_weighted for r in results)
    data = {
        "version": "2.0",
        "model": model,
        "timestamp": ts,
        "summary": {
            "total_weighted_score": round(total_got, 1),
            "total_weighted_max": round(total_max, 1),
            "percentage": round(total_got / total_max * 100, 1) if total_max else 0,
            "questions": len(results),
            "avg_latency_s": round(sum(r.latency for r in results) / len(results), 2),
        },
        "by_category": {},
        "by_language": {},
        "by_difficulty": {},
        "results": [],
    }
    # Aggregates
    for dim, key_fn in [
        ("by_category", lambda r: r.question.category),
        ("by_language", lambda r: r.question.lang),
        ("by_difficulty", lambda r: r.question.difficulty),
    ]:
        groups: dict[str, list[Result]] = defaultdict(list)
        for r in results:
            groups[key_fn(r)].append(r)
        for k, rs in groups.items():
            got = sum(r.weighted_score for r in rs)
            mx  = sum(r.max_weighted for r in rs)
            data[dim][k] = {
                "score": round(got, 1),
                "max": round(mx, 1),
                "pct": round(got / mx * 100, 1) if mx else 0,
            }
    # Per-question
    for r in results:
        data["results"].append({
            "id": r.question.id,
            "category": r.question.category,
            "lang": r.question.lang,
            "difficulty": r.question.difficulty,
            "raw_score": round(r.raw_score, 3),
            "weighted_score": round(r.weighted_score, 1),
            "max_weighted": r.max_weighted,
            "method": r.method,
            "latency_s": round(r.latency, 2),
            "notes": r.notes,
            "judge_reasoning": r.judge_reasoning,
            "prompt": r.question.prompt,
            "reference": r.question.reference,
            "response": r.response,
        })

    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{G}Report saved: {fname}{RST}")
    return fname


# ── CLI ───────────────────────────────────────────────────────────────────────

def pick_model(hint: Optional[str]) -> str:
    if hint:
        return hint
    try:
        models = list_models()
    except Exception as e:
        print(f"{R}Cannot list models: {e}{RST}")
        return DEFAULT_MODEL

    print(f"\n{BLD}Available models:{RST}")
    for i, m in enumerate(models, 1):
        marker = f"  {G}<-- default{RST}" if m == DEFAULT_MODEL else ""
        print(f"  {i}. {m}{marker}")
    choice = input(f"\n{BLD}Select model (Enter = default):{RST} ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(models):
        return models[int(choice) - 1]
    return DEFAULT_MODEL


def filter_questions(qs: list[Question], args: list[str]) -> list[Question]:
    # --cat
    cats_arg = next((a for a in args if a.startswith("--cat=")), None)
    if not cats_arg:
        # check --cat X form
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
{BLD}LM Studio Intelligence Test Suite v2.0{RST}

Usage:
  python test_model.py [MODEL_ID] [OPTIONS]

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
  python test_model.py --ping                                # test connection
  python test_model.py                                       # interactive
  python test_model.py qwen3-4b@q4 --all -s                 # full test, save
  python test_model.py --base-url http://localhost:8888/v1 qwen3-4b --all
  python test_model.py --api-key sk-xxx qwen3-4b --all      # with auth
  OPENAI_BASE_URL=http://... python test_model.py --all     # via env var
""")


def main() -> None:
    global API_BASE_URL, API_KEY, DEFAULT_MODEL

    args = sys.argv[1:]

    if not args or "-h" in args or "--help" in args:
        usage()
        return

    # Parse endpoint & auth flags (can override env vars)
    if "--base-url" in args:
        try:
            idx = args.index("--base-url")
            API_BASE_URL = args[idx + 1]
        except (ValueError, IndexError):
            pass

    if "--api-key" in args:
        try:
            idx = args.index("--api-key")
            API_KEY = args[idx + 1]
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
    print("  LM Studio Intelligence Test Suite  v2.0")
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
