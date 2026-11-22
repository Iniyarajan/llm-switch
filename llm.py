"""
Unified LLM client: call local Ollama or any cloud open-weight provider
through ONE function. Every backend here is OpenAI-compatible, so the same
code talks to all of them — you only change the model name.

Usage:
    from llm import chat, MODELS
    print(chat("local-qwen", "Summarize: ..."))
    print(chat("or-deepseek", "Summarize: ..."))
"""
import os
import time
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


@dataclass
class Backend:
    base_url: str
    api_key: str
    model: str
    # USD per 1M tokens (input, output). 0 for local. Rough public prices —
    # update from each provider's pricing page when you care about exact cost.
    price_in: float = 0.0
    price_out: float = 0.0


# ---- The model registry. Add/rename freely. Keys are YOUR shorthand. ----
MODELS = {
    # Local (free, runs on your M1 Pro via Ollama). No key needed.
    "local-qwen": Backend(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",  # placeholder; Ollama ignores it
        model="qwen2.5:7b",
    ),
    "local-llama": Backend(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",
        model="llama3.1:8b",
    ),

    # Cloud open-weight via OpenRouter (one key, many models).
    "or-deepseek": Backend(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="deepseek/deepseek-chat",      # DeepSeek-V3 class, near-frontier, cheap
        price_in=0.28, price_out=0.88,
    ),
    "or-qwen": Backend(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="qwen/qwen3-next-80b-a3b-instruct",  # modern 80B MoE, very cheap
        price_in=0.14, price_out=0.28,
    ),
    "or-llama70b": Backend(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="meta-llama/llama-3.3-70b-instruct",
        price_in=0.30, price_out=0.40,
    ),

    # Frontier, for the hard calls / as a quality baseline (also via OpenRouter).
    "or-claude": Backend(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model="anthropic/claude-sonnet-4.5",
        price_in=3.00, price_out=15.00,
    ),

    # Groq: fastest open-model inference (good for latency-sensitive agents).
    "groq-llama70b": Backend(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY", ""),
        model="llama-3.3-70b-versatile",
        price_in=0.59, price_out=0.79,
    ),
}


def chat(model_key: str, prompt: str, system: str | None = None,
         temperature: float = 0.3, max_tokens: int = 1024) -> dict:
    """Send one prompt. Returns a dict with text, token counts, latency, cost."""
    if model_key not in MODELS:
        raise KeyError(f"Unknown model '{model_key}'. Options: {list(MODELS)}")
    b = MODELS[model_key]
    if not b.api_key:
        raise RuntimeError(
            f"No API key for '{model_key}'. Fill it in .env (see .env.example).")

    # timeout + capped retries so a slow/unavailable provider fails fast
    # instead of hanging on the SDK's default 600s timeout.
    client = OpenAI(base_url=b.base_url, api_key=b.api_key,
                    timeout=60.0, max_retries=1)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    t0 = time.time()
    resp = client.chat.completions.create(
        model=b.model, messages=messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    dt = time.time() - t0

    u = resp.usage
    cost = (u.prompt_tokens / 1e6) * b.price_in + \
           (u.completion_tokens / 1e6) * b.price_out
    return {
        "model_key": model_key,
        "model": b.model,
        "text": resp.choices[0].message.content,
        "in_tokens": u.prompt_tokens,
        "out_tokens": u.completion_tokens,
        "latency_s": round(dt, 2),
        "cost_usd": round(cost, 6),
    }


if __name__ == "__main__":
    # Smoke test against local model (works as soon as `ollama pull` finishes).
    r = chat("local-qwen", "In one sentence, what is an open-weight LLM?")
    print(r["text"])
    print(f"\n[{r['model']}] {r['in_tokens']}+{r['out_tokens']} tok, "
          f"{r['latency_s']}s, ${r['cost_usd']}")
