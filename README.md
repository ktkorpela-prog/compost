# Compost v0.1

**Don't detect the slop. Compost it.**

This repository is the first signal-validation experiment for Compost: an open project for measuring linguistic convergence in AI-assisted writing without inferring or shaming authorship.

Read first:

- [`PROJECT.md`](PROJECT.md) — problem statement, scope and success condition.
- [`PRINCIPLES.md`](PRINCIPLES.md) — the project's normative guardrails.
- [`EXPERIMENT_V0.1.md`](EXPERIMENT_V0.1.md) — experimental design and measurement rules.
- [`CORPUS_PLAN.md`](CORPUS_PLAN.md) — first external validation datasets and sampling plan.

## What the code does

Given three local corpora — pre-AI human, contemporary human and AI-assisted — the experiment:

1. reads one text document per `.txt` file;
2. counts document, paragraph, sentence and token denominators;
3. extracts lexical n-grams plus a small set of structural frames;
4. calculates pattern prevalence;
5. calculates lift of AI-assisted prevalence over each human baseline;
6. writes a ranked CSV for inspection.

It does **not** classify a document as AI-written.

## Repository layout

```text
compost-v0.1/
├── PROJECT.md
├── PRINCIPLES.md
├── EXPERIMENT_V0.1.md
├── README.md
├── pyproject.toml
├── compost/
│   ├── __init__.py
│   ├── normalizer.py
│   ├── extractor.py
│   ├── scorer.py
│   └── experiment.py
├── corpora/
│   ├── pre_ai_human/
│   ├── contemporary_human/
│   └── ai_assisted/
└── tests/
```

## Quick start

Requires Python 3.10+ and no third-party runtime dependencies.

Put `.txt` files into the three corpus directories, one document per file, then run:

```bash
python -m compost.experiment \
  --pre-human corpora/pre_ai_human \
  --contemporary-human corpora/contemporary_human \
  --ai corpora/ai_assisted \
  --output results.csv
```

Useful options:

```bash
python -m compost.experiment --help
```

By default the report only includes patterns observed in at least two AI-assisted documents. For tiny smoke tests, use `--min-ai-docs 1`.

## Output columns

The CSV includes:

- pattern type and text;
- counts in all three corpora;
- occurrences per 10,000 sentences;
- document prevalence;
- smoothed lift vs pre-AI human;
- smoothed lift vs contemporary human.

A high lift is not a verdict that a phrase is bad, nor proof that AI wrote it. It is a signal worth investigating.

## Corpus hygiene

Do not treat arbitrary scraped text as ground truth. Keep provenance and genre metadata. Remove boilerplate and navigation. For any publishable result, create discovery and validation partitions by independent source/model/prompt family rather than randomly splitting sentences.
