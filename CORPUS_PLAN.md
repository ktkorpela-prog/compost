# Corpus Plan — v0.1

The first code is intentionally corpus-agnostic. The next workstream is to assemble data without turning dataset convenience into methodology.

## 1. Bootstrap validation: RAID

RAID (Dugan et al., ACL 2024; arXiv:2405.07940) is a useful first external benchmark because it contains human source texts and LLM generations across multiple models and domains, with source identifiers that support matched comparisons.

Use it to answer:

- Does the extractor find repeated lexical/structural patterns across multiple LLMs?
- Do those patterns survive domain changes?
- Are we mostly learning one model, one prompt family or one genre?

Do **not** treat RAID's human side as sufficient for the temporal baseline. It is a paired human-vs-generated benchmark, not a clean three-state history of language.

## 2. Independent holdout: HC3

HC3 (Guo et al., 2023; arXiv:2301.07597) pairs human and ChatGPT answers across several question-answering sources. Its genre is narrower than RAID, which makes it useful as an independent replication corpus rather than the primary benchmark.

Use it to ask whether patterns discovered elsewhere recur in a different dataset assembled by different researchers.

## 3. Temporal baseline: still required

We still need two reasonably genre-matched human corpora:

- pre-AI human writing;
- contemporary human writing with credible provenance and minimal or disclosed AI assistance.

This is the harder part of the experiment. A pre-2022 baseline alone cannot tell us whether a phrase changed because of AI or because internet writing changed generally.

## 4. Sampling rules

For the first serious run:

- sample by document, never by sentence;
- keep source/model/domain metadata;
- cap repeated generations from the same source prompt;
- create discovery and validation partitions by source/model/prompt family where practical;
- record all denominators before filtering pattern candidates;
- never publish copyrighted source text unless redistribution rights are clear.

## 5. Immediate next data milestone

Create a small, reproducible sample with roughly balanced document counts across:

- matched human source text;
- at least three LLM families;
- at least three prose domains;
- a held-out source/model partition.

The purpose is not statistical grandeur. It is to expose whether the current extractor produces interpretable, replicating signals before we make it cleverer.
