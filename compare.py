"""
Side-by-side model comparison. Run the SAME prompts across several backends
and print quality + latency + cost. This is your decision tool: if an open
model's output is good enough on YOUR task, route that task to it and save money.

Edit MODELS_TO_TEST and TASKS below, then:  python compare.py
"""
from llm import chat

# Which backends to compare. Comment out any you don't have a key for yet.
MODELS_TO_TEST = [
    # "local-qwen",    # free, local — enable once the download finishes
    "or-deepseek",     # cheap, near-frontier
    "or-qwen",         # modern cheap open 80B MoE
    "or-claude",       # frontier baseline (what you'd pay for today)
]

# Put a few REAL examples from the workload you want to move off paid APIs.
# These are illustrative — a customer-support assistant that classifies, extracts,
# and replies. Swap them for prompts from your own workload.
SYSTEM = (
    "You are the WhatsApp assistant for a parcel/transport company. "
    "Follow the instruction exactly and reply with nothing extra."
)
TASKS = [
    # 1. Intent classification (a high-volume call in a support agent)
    "Classify this message as exactly one of "
    "[track_parcel, book_pickup, price_enquiry, complaint, other]. "
    "Reply with only the label.\n\n"
    "Message: 'anna en parcel ennaiku varum, LR number 4471'",

    # 2. Entity extraction to JSON (code-friendly output)
    "Extract strict JSON {name, phone, from_city, to_city, item}. "
    "Use null for anything missing. Reply with ONLY the JSON.\n\n"
    "Message: 'Hi this is Ravi 98765 43210, need to send 2 cartons of "
    "spare parts from Coimbatore to Madurai tomorrow'",

    # 3. Short templated reply in the customer's language (tone + bilingual)
    "The customer asked in Tamil-English for the status of parcel LR 4471, "
    "which is 'out for delivery, expected today evening'. "
    "Write a warm 1-2 line WhatsApp reply in the same Tamil-English style.",
]


def main():
    for i, task in enumerate(TASKS, 1):
        print(f"\n{'='*70}\nTASK {i}: {task[:60]}...\n{'='*70}")
        for mk in MODELS_TO_TEST:
            try:
                r = chat(mk, task, system=SYSTEM, temperature=0)
                print(f"\n-- {mk} ({r['model']}) "
                      f"| {r['latency_s']}s | ${r['cost_usd']:.6f} "
                      f"| {r['in_tokens']}+{r['out_tokens']} tok --")
                print(r["text"].strip())
            except Exception as e:
                print(f"\n-- {mk}: ERROR: {e}")


if __name__ == "__main__":
    main()
