"""Configuration: environment variables, API endpoints, timeouts."""

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env file from cwd or parent dirs (stdlib only, no overwrite of existing env vars)."""
    here = Path.cwd()
    for directory in [here, *here.parents]:
        env_file = directory / ".env"
        if env_file.is_file():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            break


_load_dotenv()

# ── Config: Endpoint & Auth ──────────────────────────────────────────────────
# Support OpenAI-compatible APIs: local (LM Studio, Ollama) or cloud (Dashscope, OpenAI)
# Env vars: OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL, API_TIMEOUT, REPORT_DIR
API_BASE_URL  = os.environ.get("OPENAI_BASE_URL", "http://localhost:1234/v1")
API_KEY       = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "your-model-id")
API_TIMEOUT   = int(os.environ.get("API_TIMEOUT", "240"))
CODE_TIMEOUT  = 5
REPORT_DIR    = os.environ.get("REPORT_DIR", "reports")

# Difficulty weight mapping
DIFF_WEIGHT = {"Easy": 1, "Medium": 2, "Hard": 3}
