# Quickstart

A step-by-step guide to running `llm-switch`.

## 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Pick at least one backend

You need **either** a local model **or** a cloud key — ideally both.

### Option A — cloud (fastest to start)

```bash
cp .env.example .env
```

Open `.env` and paste an **OpenRouter** key from <https://openrouter.ai/keys>
(add a few dollars of credit). That one key unlocks DeepSeek, Qwen, Llama, Claude,
and more. Groq and a direct Anthropic key are optional.

### Option B — local (free, offline)

Install [Ollama](https://ollama.com), then pull a model that fits your RAM:

```bash
ollama pull qwen2.5:7b      # ~5 GB, good general model
```

Local models need no key and cost nothing.

## 3. Smoke test

```bash
python llm.py
```

Prints a one-line answer plus a token/latency/cost footer. (Edit the last block of
`llm.py` to use `or-deepseek` instead of `local-qwen` if you went cloud-only.)

## 4. Use `ask` day-to-day

```bash
ask "explain tail-call optimization"       # free local by default
cat server.log | ask "what's failing here" # pipe input in
ask -m deepseek "summarize: <text>"        # cheap cloud model
ask -m claude  "a genuinely hard question" # frontier baseline
ask -s "Reply only in JSON" "..."          # system prompt
ask --models                               # list models + prices
```

Set a default model without typing `-m` every time:

```bash
export ASK_MODEL=deepseek
```

## 5. Decide what to move off the frontier

Edit `MODELS_TO_TEST` and `TASKS` in `compare.py` with a few **real** prompts from
your workload, then:

```bash
python compare.py
```

You'll see each model's answer, latency, and cost side by side. If a cheap model's
output is good enough on your task, route that task to it and keep the frontier for
the hard calls.

## Adding a model

Add one entry to the `MODELS` dict in `llm.py` — any OpenAI-compatible endpoint
works. Set `price_in` / `price_out` (USD per 1M tokens) so the cost footer is accurate.
