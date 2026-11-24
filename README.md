# Technical Writing Portfolio (Payments Engineering & LLM Evaluation)

*Personal portfolio project by Ambrose Makai. All articles, documentation, and runnable code examples are original writing with synthetic examples. No real company names, customer data, or credentials are used.*

## Problem
Strong engineering and AI-evaluation work depends on clear, precise written communication—whether explaining subtle distributed-systems invariants to backend teams, writing unambiguous annotation rubrics, or documenting developer tools so others can reproduce results without guesswork.

This repository collects two original long-form technical articles (800–1,200 words each), a runnable webhook security demo, and a clean operator/user documentation sample.

## Contents
- **Article 1:** [`articles/handling-payment-webhooks-safely.md`](articles/handling-payment-webhooks-safely.md) — *Handling Payment Webhooks Safely: Idempotency, Signatures, and Retries*
  - Runnable companion code: [`examples/webhook_handler_demo.py`](examples/webhook_handler_demo.py)
- **Article 2:** [`articles/writing-llm-evaluation-rubrics.md`](articles/writing-llm-evaluation-rubrics.md) — *How to Write an Evaluation Rubric for LLM Outputs* (grounded in real examples and metrics from `llm-eval-toolkit`)
- **Documentation Sample:** [`docs/llm-eval-toolkit-guide.md`](docs/llm-eval-toolkit-guide.md) — Operator & CLI documentation for `llm-eval-toolkit`

## How to Run & Verify
```bash
# Run the companion webhook handler example (standard library only, Python 3.9+)
python3 examples/webhook_handler_demo.py

# Check article word counts
wc -w articles/handling-payment-webhooks-safely.md articles/writing-llm-evaluation-rubrics.md
```

## Results (Actual Output)
- `python3 examples/webhook_handler_demo.py` ran cleanly and verified first-time settlement (`settled`), duplicate retry acknowledgement (`200 OK`, `duplicate_ignored`, balance preserved at `250000` kobo), and forged-signature rejection (`PermissionError`).
- Verified article word counts (`wc -w`):
  - `articles/handling-payment-webhooks-safely.md`: **903 words**
  - `articles/writing-llm-evaluation-rubrics.md`: **887 words**
  - `docs/llm-eval-toolkit-guide.md`: **490 words**

## Limitations
- The runnable webhook demo uses SQLite in-memory storage to stay zero-dependency; production deployments should use PostgreSQL or MySQL with explicit row locking (`SELECT ... FOR UPDATE`) and persistent queues.
- Articles focus on core patterns rather than framework-specific middleware boilerplate.

## What I Would Do Next
- Add a third deep-dive article on designing SQL reconciliation queries for multi-gateway ledgers using examples from `fintech-transactions-analysis`.
- Add automated markdown link-checking and spell/lint checks via GitHub Actions.
