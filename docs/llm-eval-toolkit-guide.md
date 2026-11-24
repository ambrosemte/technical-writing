# Documentation Sample: `llm-eval-toolkit` User & Operator Guide

*Personal portfolio documentation sample by Ambrose Makai, documenting the companion `llm-eval-toolkit` project.*

## Overview
`llm-eval-toolkit` is an offline-first Python package and CLI for evaluating candidate LLM outputs against versioned YAML rubrics. It supports pointwise weighted scoring, pairwise win/tie/loss comparison, dual-annotator agreement analysis (exact agreement, unweighted Cohen's kappa, and Quadratic Weighted Kappa), and automated Markdown + PNG reporting.

An optional LLM-as-judge adapter is available when `LLM_EVAL_API_KEY` is configured, but the core workflow runs completely offline with zero external API calls.

## Installation
```bash
git clone https://github.com/ambrosemte/llm-eval-toolkit.git
cd llm-eval-toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start
```bash
# 1. Build the 40-prompt hand-written synthetic dataset (seed=101)
python scripts/build_dataset.py

# 2. Run the full evaluation and generate reports + charts
python -m llm_eval evaluate

# 3. Run the automated test suite
pytest -v
```

Outputs are written to `outputs/`:
- `outputs/eval_report.md` — summary metrics and per-rubric breakdown table
- `outputs/eval_results.json` — full per-item and aggregate JSON payload
- `outputs/charts/score_comparison.png` — Candidate A vs. Candidate B mean scores by rubric
- `outputs/charts/annotator_agreement.png` — QWK and exact criterion agreement by rubric

## CLI Reference

### `python -m llm_eval evaluate`
Evaluates a JSON dataset against a directory of YAML rubrics.

| Flag | Default | Description |
|---|---|---|
| `--dataset` | `data/eval_dataset.json` | Path to evaluation dataset JSON |
| `--rubrics` | `rubrics` | Directory containing `*.yaml` rubric definitions |
| `--out` | `outputs` | Output directory for reports and charts |
| `--tie-margin` | `0.15` | Minimum weighted score difference to declare a pairwise winner |

### `python -m llm_eval judge-sample`
Demonstrates the optional LLM-as-judge adapter.
- If `LLM_EVAL_API_KEY` is **unset**, returns `{"mode": "offline", ...}` and prints a preview of the generated judge prompt without making network requests.
- If `LLM_EVAL_API_KEY` is **set**, calls the OpenAI-compatible chat completions endpoint configured by `LLM_EVAL_API_BASE` and `LLM_EVAL_MODEL`.

## Rubric YAML Schema
Every rubric file in `rubrics/*.yaml` must satisfy two validation rules enforced by `llm_eval/rubric.py`:
1. Each criterion defines integer scale descriptors for all keys `1` through `5`.
2. Criterion weights sum to `1.0` (within floating-point tolerance `1e-6`).

```yaml
name: example_rubric
version: "1.0"
description: Concise description of what the rubric measures.
criteria:
  - id: accuracy
    name: Accuracy
    weight: 0.60
    scale:
      1: Incorrect core answer.
      2: Major errors present.
      3: Partially correct.
      4: Correct with minor omission.
      5: Fully correct and verifiable.
  - id: clarity
    name: Clarity
    weight: 0.40
    scale:
      1: Unclear.
      2: Hard to follow.
      3: Acceptable clarity.
      4: Clear and structured.
      5: Concise and publication-ready.
```

## Troubleshooting
- **`ValueError: weights must sum to 1.0`:** Check the `weight` values in your YAML rubric; rounding discrepancies larger than `1e-6` fail fast at load time.
- **`KeyError: Missing rating for criterion`:** Ensure every annotator object in your dataset provides an integer score (`1`–`5`) for every criterion ID defined in the item's assigned rubric.
- **Matplotlib cache warning in read-only environments:** Set `MPLCONFIGDIR=/tmp/mplcache` before running `evaluate`.
