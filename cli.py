#!/usr/bin/env python3
"""ask — one-shot LLM from the terminal, routed to local/cheap models by default.

Examples:
    ask "what is a closure in JS"               # local qwen (free, offline)
    cat error.log | ask "explain this error"    # pipe a file / command output in
    ask -m deepseek "classify intent: <text>"   # cloud open-weight (cheap)
    ask -m claude "a genuinely hard question"    # frontier, as a quality baseline
    ask -s "You translate to Tamil" "Good night" # system prompt
    ask --models                                 # list models + prices

The response goes to stdout; the cost/latency footer goes to stderr, so
`ask ... | pbcopy` or `ask ... > out.txt` stay clean.

This is for quick, one-off, or bulk-scriptable tasks on cheap models.
"""
import os
import sys
import argparse
from llm import chat, MODELS

# friendly short names -> registry keys in llm.py
ALIASES = {
    "local": "local-qwen", "qwen": "local-qwen", "llama": "local-llama",
    "deepseek": "or-deepseek", "qwen80": "or-qwen", "llama70": "or-llama70b",
    "claude": "or-claude", "groq": "groq-llama70b",
}


def main():
    p = argparse.ArgumentParser(prog="ask", add_help=True,
                                description="One-shot LLM in the terminal (default: free local model).")
    p.add_argument("prompt", nargs="*", help="the prompt; piped stdin is appended")
    p.add_argument("-m", "--model", default=os.getenv("ASK_MODEL") or "local",
                   help="model key or alias. Default: $ASK_MODEL if set, else 'local'. See --models.")
    p.add_argument("-s", "--system", help="system prompt")
    p.add_argument("-t", "--temperature", type=float, default=0.3)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("-q", "--quiet", action="store_true", help="hide the cost/latency footer")
    p.add_argument("--models", action="store_true", help="list available models and exit")
    a = p.parse_args()

    if a.models:
        print(f"{'alias':10} {'key':14} {'model':42} price /1M (in/out)")
        for k, b in MODELS.items():
            alias = next((al for al, key in ALIASES.items() if key == k), "")
            print(f"{alias:10} {k:14} {b.model:42} ${b.price_in}/{b.price_out}")
        return

    parts = []
    if a.prompt:
        parts.append(" ".join(a.prompt))
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            parts.append(piped)
    prompt = "\n\n".join(parts).strip()
    if not prompt:
        p.error("no prompt — pass text as arguments or pipe it in")

    key = ALIASES.get(a.model, a.model)
    try:
        r = chat(key, prompt, system=a.system,
                 temperature=a.temperature, max_tokens=a.max_tokens)
    except Exception as e:  # noqa: BLE001 - surface any backend error cleanly
        print(f"ask: {e}", file=sys.stderr)
        sys.exit(1)

    print(r["text"])
    if not a.quiet:
        print(f"\n[{r['model_key']} · {r['model']}] "
              f"{r['in_tokens']}+{r['out_tokens']} tok · {r['latency_s']}s · ${r['cost_usd']}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
