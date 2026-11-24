# How to Write an Evaluation Rubric for LLM Outputs

*Personal portfolio writing sample by Ambrose Makai. Concrete rubric criteria, prompts, and agreement metrics are drawn from the companion project `llm-eval-toolkit`.*

Evaluating large language models without a written rubric quickly turns into opinionated guesswork. One reviewer penalizes a missing edge case harshly while ignoring a formatting violation; another rewards fluent prose even when the answer fabricates a non-existent software release. When those inconsistent scores feed into model selection, prompt tuning, or reinforcement learning from human feedback (RLHF), teams optimize for noise rather than real capability.

A well-designed evaluation rubric turns subjective quality judgments into repeatable, auditable measurements. Below is a practical method for writing rubrics that human annotators—and optional LLM judges—can apply consistently, illustrated with real examples from `llm-eval-toolkit`.

## 1. Separate Independent Dimensions Instead of Using One Global Score

A single 1–5 "overall quality" score hides *why* a response failed. Consider a coding prompt (`CODE-02` in `llm-eval-toolkit`): *"Write a parameterized SQLite query in Python to fetch a user by email safely."*

Suppose Candidate A returns:

```python
def get_user(conn, email):
    return conn.execute(f"SELECT * FROM users WHERE email = '{email}'").fetchone()
```

This snippet is concise and runs on a normal email address, yet it introduces a critical SQL injection vulnerability. Under a single global score, one annotator might give it a 3 ("it works") while another gives it a 1 ("critical security flaw").

Splitting `code_correctness` into weighted, orthogonal criteria removes that ambiguity:

- **Functional Accuracy (weight 0.40):** Does the code satisfy stated requirements?
- **Edge-Case & Error Handling (weight 0.25):** Does it handle empty, invalid, or boundary inputs?
- **Security & Data Integrity (weight 0.20):** Does it avoid vulnerabilities or silent data corruption?
- **Clarity & Maintainability (weight 0.15):** Is it idiomatic and easy to review?

With those four criteria, both annotators can score `readability=4` and `functional_accuracy=3` while strictly capping `security_and_safety=1`, yielding a clear weighted score of **2.50 / 5.0** compared to **4.75 / 5.0** for a parameterized query.

## 2. Anchor Every Point on the Scale to Observable Behavior

Vague scale labels such as *"1 = Bad, 3 = Average, 5 = Great"* cause annotators to drift toward different personal baselines. Every score from 1 to 5 should describe **observable evidence** that a reviewer can verify directly in the text.

For example, in `factual_accuracy.yaml`, the **Uncertainty & Scope Calibration** criterion anchors each level concretely:

- **1:** States guesses or unknown facts with unwarranted certainty.
- **2:** Overstates confidence or ignores clear ambiguity in the prompt.
- **3:** Partially acknowledges assumptions or limits.
- **4:** Clearly states assumptions and avoids overclaiming.
- **5:** Explicitly distinguishes known facts, assumptions, and unknowns.

When evaluating a trap prompt like `FACT-07` (*"What is the exact release date of Python 5.0?"*), an annotator does not have to wonder whether a refusal should be penalized for "not answering." The descriptor makes the ruling objective: fabricating *"October 2025"* scores **1**, while stating that Python remains on the 3.x line and no 5.0 release exists scores **5**.

## 3. Write Explicit Edge-Case Rules Before Scaling Annotation

Even clear scales leave gray zones where two careful reviewers will reasonably disagree. Document those edge cases upfront in a companion `annotation_guidelines.md`:

- **Valid content in the wrong format:** In `INST-02` (*"Return ONLY a valid JSON object with keys `status` and `retryable`. No prose."*), a model that replies *"Sure! Here is the JSON..."* breaks downstream JSON parsers. Our guideline explicitly caps `constraint_adherence` and `format_compliance` at **2** whenever conversational filler violates a strict format constraint.
- **Security overrides happy-path correctness:** Working code with SQL injection or timing-unsafe secret comparison (`==` instead of `hmac.compare_digest`) is capped at **1–2** on `security_and_safety`.
- **Pairwise tie margins:** When deriving pairwise winners from pointwise scores, define an explicit tie band (for example, `±0.15` on a 5-point scale) so a negligible 0.05 difference does not get logged as a decisive win.

## 4. Measure Inter-Annotator Agreement Before Trusting the Numbers

You cannot know whether a rubric is clear by reading it yourself—you have to measure whether two independent raters apply it the same way on the same batch of prompts.

Raw percent agreement is misleading when one rating dominates a dataset, because raters agree often by pure chance. Two complementary metrics give a much clearer diagnostic:

- **Unweighted Cohen's kappa:** Adjusts exact agreement for chance; useful for categorical verdicts like pairwise wins (`candidate_a`, `candidate_b`, `tie`).
- **Quadratic Weighted Kappa (QWK):** Designed for ordinal 1–5 scales, penalizing a 1-vs-5 disagreement much more heavily than a 4-vs-5 boundary difference.

In `llm-eval-toolkit`'s 40-prompt benchmark (80 candidate responses evaluated across two simulated annotators with `seed=101`), the rubrics produced **84.69% exact criterion agreement**, an unweighted Cohen's kappa of **0.7850**, and a **Quadratic Weighted Kappa of 0.9663**. In real human annotation workflows, any individual criterion that drops below **QWK 0.60** during a pilot batch is a strong signal to pause labeling, inspect the disagreed items, and tighten the scale descriptors rather than blaming the annotators.

## 5. Version Rubrics Like Code

Store rubrics in structured, version-controlled files (such as YAML with explicit `version` fields and automated weight-sum validation). Whenever you tighten a descriptor or adjust a criterion weight, bump the rubric version so scores from `v1.0` are never silently mixed with `v1.1`. Treating evaluation rubrics with the same engineering rigor as production schemas ensures that model score gains reflect genuine improvements—not shifting goalposts.
