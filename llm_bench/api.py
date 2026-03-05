"""API client: OpenAI-compatible HTTP calls."""

import json
import time
import urllib.request
import urllib.error

from llm_bench import config
from llm_bench.utils import G, Y, R, C, DIM, RST, BLD


def api_post(endpoint: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if config.API_KEY:
        headers["Authorization"] = f"Bearer {config.API_KEY}"
    req = urllib.request.Request(
        f"{config.API_BASE_URL}/{endpoint}",
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=config.API_TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        raise ConnectionError(f"API unreachable ({config.API_BASE_URL}): {e}") from e


def list_models() -> list[str]:
    headers = {}
    if config.API_KEY:
        headers["Authorization"] = f"Bearer {config.API_KEY}"
    req = urllib.request.Request(f"{config.API_BASE_URL}/models", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    return [m["id"] for m in data.get("data", [])]


def ping_api() -> bool:
    """
    Test API connectivity and list available models.
    Returns True if connection is successful.
    """
    print(f"\n{BLD}{C}Pinging API:{RST} {config.API_BASE_URL}")
    print(f"  Auth: {'Bearer ***' if config.API_KEY else 'None (local mode)'}\n")
    try:
        models = list_models()
        if not models:
            print(f"{Y}⚠ Connected but no models found!{RST}")
            return False

        print(f"{G}✓ Connected! {len(models)} model(s) available:{RST}")
        for m in models:
            marker = f"  {G}<-- default{RST}" if m == config.DEFAULT_MODEL else ""
            print(f"  • {m}{marker}")

        # Test chat with first model
        test_model = models[0]
        print(f"\n{DIM}Testing chat with: {test_model}...{RST}")
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


def chat_with_tools(
    model: str, prompt: str, tools: list[dict],
    max_tokens: int, temperature: float, system: str = ""
) -> tuple[str, list[dict], float]:
    """
    Chat with tools (function calling). Returns (content, tool_calls, latency).
    tool_calls: list of {"name": str, "args": dict} — parsed from API response.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.time()
    resp = api_post("chat/completions", {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "max_tokens": max_tokens,
        "temperature": temperature,
    })
    latency = time.time() - t0

    msg = resp["choices"][0]["message"]
    content = msg.get("content") or ""

    raw_calls = msg.get("tool_calls") or []
    tool_calls = []
    for tc in raw_calls:
        func = tc.get("function", {})
        try:
            args = json.loads(func.get("arguments", "{}"))
        except Exception:
            args = {}
        tool_calls.append({"name": func.get("name", ""), "args": args})

    return content, tool_calls, latency
