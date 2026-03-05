"""ANSI colors and text normalization utilities."""

import re
import unicodedata

# ── ANSI Colors ──────────────────────────────────────────────────────────────
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


# ── Vietnamese Diacritic Normalization ───────────────────────────────────────

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
