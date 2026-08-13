# Results — Experiment 01: Signal Validation

**Date:** 2026-08-13
**Branch:** `exp/experiment-01-signal-validation`
**Recommendation: ITERATE**

## Hypothesis

> Can automatically extracted language patterns recur at elevated rates across
> *independent* AI samples while remaining less prevalent in comparable human writing?

This is not an authorship-detection experiment. No document is classified, and no
combined "AI probability" or saturation score is produced.

## Headline result

**Under the pre-registered thresholds, the experiment produced no candidate set at all.**

The pre-registered rule nominated patterns appearing in ≥25% of AI discovery documents.
The most widespread pattern in 360 AI documents is `such as` at 19.4% document
prevalence. The threshold was unreachable by construction, so zero candidates were
nominated and zero were tested. That is the primary result, and it is a null.

A second, explicitly post-hoc pass at a ≥5% floor nominated 107 lexical candidates, of
which **10 replicated** across a change of AI system. Those survivors are dominated by
genre markers and generic English rather than rhetorical style.

The structural frame catalogue — the part of the extractor the project was actually
built around — is effectively inert on this corpus. Only 3 of 4 frames fired at all,
and the flagship `isn't <X> it's <Y>` occurs **3 times in 5,512 validation sentences**.

## 1. Corpus

### Sources

| Dataset | Role | Provenance |
|---|---|---|
| RAID `train.csv` | primary | Dugan et al., ACL 2024, arXiv:2405.07940. 11,779,491,051 bytes, full SHA-256 `52f04ceebc126064e68fbd22d8b736964065745464f4bfd52e488150b49f84e4` — **verified against the upstream published LFS hash** |
| HC3 (4 domains) | independent replication | Guo et al., 2023, arXiv:2301.07597. 17.7 MB |

RAID's other files were verified unusable rather than assumed: `test.csv` carries only
`id,generation` with model labels withheld for the leaderboard, and `extra.csv` contains
only the `german`, `czech` and `code` domains. Only `train.csv` has both labels and
English prose.

### Partitions

| Partition | Docs | Paragraphs | Sentences | Tokens | Models |
|---|---:|---:|---:|---:|---|
| `ai_discovery` | 360 | 1,518 | 4,348 | 80,300 | chatgpt, mistral-chat, mpt-chat |
| `ai_validation` | 360 | 2,076 | 5,512 | 92,172 | gpt4, llama-chat, cohere-chat |
| `human_baseline` | 360 | 361 | 5,096 | 104,984 | human (matched by `source_id`) |
| `hc3_ai` | 160 | 418 | 1,151 | 29,136 | chatgpt |
| `hc3_human` | 160 | 204 | 1,076 | 25,110 | human |

Domains (RAID partitions): abstracts, books, news, recipes, reddit, wiki.
Filters: `attack=none` (RAID ships 11 adversarial perturbations), minimum 400 characters.
Excluded: `code`, `czech`, `german` (not English prose), `poetry` (line conventions the
segmenter is not built for), `reviews` (≈53% of the row count of other domains;
per-model coverage was not verified, so it was dropped rather than risk an unbalanced
stratum).

### Sampling procedure

Deterministic and **seedless**. A document is selected when `sha256(row_id)` ranks among
the lowest N within its `(partition, domain, model)` stratum: 20 per stratum for AI, 60
per domain for human, 40 per stratum for HC3. Reproducible with no seed to store, and
independent of read order — which matters because `train.csv` is grouped by domain, so
any order-dependent scheme would have skewed the sample.

### Human baseline: pooled, approximately half source-matched

**The human baseline is pooled, not matched.** An earlier draft of this document
described it as "matched". That overstated what was achieved and has been corrected.

Eligibility required a human row whose RAID id appeared as the `source_id` of a sampled
generation, but the cap of 60 documents per domain (360 total) bound far below the 704
eligible source ids. The cap, not data availability, determined selection.

| Metric | Value |
|---|---:|
| AI discovery unique source ids | 357 (from 360 documents) |
| AI validation unique source ids | 356 (from 360 documents) |
| Union / intersection | 704 / 9 |
| Human baseline unique source ids | 360 |
| Discovery source ids **with** matched human | **197 / 357 = 55.2%** |
| Validation source ids **with** matched human | **168 / 356 = 47.2%** |
| AI source ids **without** matched human | 344 / 704 = 48.9% |

The 360 human documents decompose as 192 sources used only by discovery, 163 used only
by validation, and **5 used by both**.

Consequence: `lift_discovery_vs_human` and `lift_validation_vs_human` are computed
against the *same pooled* human corpus, which is roughly half-matched to each AI
partition and almost entirely non-overlapping between them. They do not share a common
matched control. Any difference between discovery lift and validation lift may reflect
which human documents happened to enter the pool rather than a property of the models.

## 2. Method

1. Candidates nominated from `ai_discovery` **only**. The nomination rule reads no human
   and no validation statistic.
2. Candidate set frozen.
3. Frozen candidates measured on `ai_validation`, `human_baseline`, and the HC3 pair.

Discovery and validation use disjoint generating models from six different providers,
so replication means a pattern survived a change of AI system, not a change of topic.
Both sides are instruction-tuned chat models; base completion models were excluded so
that "chat-tuned vs base" could not confound the split.

Replication required **all three**: lift ≥ 1.5 vs human, validation document prevalence
≥ 10%, and ≥ 5 validation occurrences. Lift uses a 0.5 continuity correction, so a zero
baseline never yields infinite lift.

## 3. Strongest replicated patterns — POST-HOC EXPLORATORY ONLY

> **These are not the primary result.** The pre-registered analysis nominated zero
> candidates and therefore produced no replicated patterns at all. Every pattern in this
> section comes from the post-hoc ≥5% exploratory pass, whose floor was chosen after
> inspecting the discovery distribution. Nothing below can be cited as a confirmatory
> finding.

All lexical. `hc3_lift` is the independent corpus (different research group, different
domains, different model).

| Pattern | Discovery lift | Validation lift | Val. doc prev. | Val. occ. | Human occ. | HC3 lift |
|---|---:|---:|---:|---:|---:|---:|
| `including the` | 3.24 | 5.28 | 10.0% | 48 | 8 | 2.54 |
| `a novel` | 3.27 | 4.33 | 10.3% | 44 | 9 | 0.93 |
| `a young` | 2.30 | 2.77 | 10.0% | 37 | 12 | 2.80 |
| `the world` | 2.56 | 2.66 | 12.8% | 70 | 24 | 1.65 |
| `in a large` | 1.69 | 2.49 | 14.4% | 60 | 22 | 0.31 |
| `this paper` | 2.21 | 2.36 | 14.4% | 57 | 22 | 0.93 |
| `about the` | 2.09 | 2.28 | 11.1% | 50 | 20 | 4.67 |
| `such as` | 2.54 | 2.24 | 19.4% | 95 | 39 | 2.13 |
| `a new` | 1.27 | 1.75 | 11.1% | 46 | 24 | 2.54 |
| `until the` | 1.94 | 1.66 | 11.7% | 65 | 36 | 2.80 |

7 of the 10 were also elevated (lift ≥ 1.5) in the independent HC3 pair.

**These should not be read as AI style.** `this paper` is an abstracts marker, `until the`
and `in a large` are recipe instructions, `a novel` and `a young` are book-summary
vocabulary. Only `such as` and `including the` — both enumerative — are plausibly
register rather than subject matter, and their lift is modest (2.24 and 5.28).

### Structural frames (reported exhaustively, no threshold)

| Frame | Discovery lift | Validation lift | Val. doc prev. | Val. occ. | Human occ. | Verdict |
|---|---:|---:|---:|---:|---:|---|
| `isn't <X> it's <Y>` | 3.52 | 6.47 | 0.8% | 3 | 0 | failed — evidence too thin |
| `not only <X> but also <Y>` | 1.95 | 2.36 | 3.1% | 11 | 4 | failed — below prevalence floor |
| `not <X> but <Y>` | 0.74 | 1.29 | 11.7% | 49 | 35 | not elevated |
| `isn't about <X> it's about <Y>` | — | — | — | 0 | 0 | never fired |

**None replicated.** The flagship reframe is directionally elevated in both AI partitions
and absent from human text, but 3 occurrences cannot support a claim. `not <X> but <Y>` —
the only frame with real volume — is *less* prevalent in AI discovery than in human
writing (lift 0.74).

## 4. Strongest discovery signals that failed validation

Ranked by discovery lift. Note what actually failed:

| Pattern | Discovery lift | Validation lift | Val. doc prev. | Why it failed |
|---|---:|---:|---:|---|
| `ingredients 1` | 64.46 | 13.87 | 1.9% | document-prevalence floor |
| `instructions 1` | 45.71 | 12.02 | 1.7% | document-prevalence floor |
| `in various` | 17.58 | 9.55 | 3.6% | document-prevalence floor |
| `making it` | 14.45 | 12.02 | 5.0% | document-prevalence floor |
| `insights into` | 14.45 | 6.47 | 2.8% | document-prevalence floor |
| `the potential` | 12.42 | 9.80 | 5.0% | document-prevalence floor |
| `minutes or until the` | 11.49 | 7.95 | 5.3% | document-prevalence floor |
| `known for` | 10.33 | 7.65 | 8.9% | document-prevalence floor |

**Almost nothing failed on lift.** Every pattern above kept a high lift into validation;
what killed them was concentration — they appear in a handful of documents. `ingredients 1`
and `minutes or until the` are recipe formatting. `known for his` is biography. The
document-prevalence floor is doing the real work of rejecting genre artifacts, and the
extremely high discovery lifts (64×, 46×) are an artifact of tiny human denominators
under continuity correction, not evidence of anything.

## 5. Methodological limitations

1. **The pre-registered threshold was miscalibrated and produced no experiment.** The
   exploratory rerun is post-hoc. It reads no validation or human statistic, so the
   discovery→validation separation holds, but the 5% floor was chosen after seeing the
   discovery distribution and the 10 survivors carry that caveat.

2. **No contemporary-human baseline exists.** RAID's human side is source material of
   mixed and largely pre-2023 vintage. Every comparison here is AI-vs-human, not
   AI-vs-*recent*-human, so nothing distinguishes "AI caused this" from "written English
   changed." This was anticipated in `CORPUS_PLAN.md` and remains unresolved.

3. **Genre dominates the results.** Most surviving patterns are domain vocabulary.
   Holding domains constant across partitions was not sufficient; per-domain lift, or
   domain-stratified nomination, is needed.

4. **Discovery and validation rest on largely disjoint source documents** — 704 distinct
   sources behind 720 generations. Sampling was AI-first, then matched humans, so the two
   AI partitions are matched on domain but not on underlying source text. A failure to
   replicate may reflect a topic change rather than a model change. Sampling human
   sources first and pulling every model's generation of those same sources would make
   the comparison genuinely paired.

5. **The structural denominator is wrong, and the bias is quantified.** Structural frames
   are extracted over two window families — every single sentence, and every adjacent
   sentence pair within a paragraph — but prevalence and lift are denominated by
   **sentences alone**. The number of windows per sentence is not constant across
   partitions, because it depends on paragraph structure:

   | Partition | Paragraphs | Sentences | Single windows | Pair windows | Total windows | Windows/sentence |
   |---|---:|---:|---:|---:|---:|---:|
   | `ai_discovery` | 1,518 | 4,348 | 4,348 | 2,830 | 7,178 | 1.651 |
   | `ai_validation` | 2,076 | 5,512 | 5,512 | 3,436 | 8,948 | 1.623 |
   | `human_baseline` | 361 | 5,096 | 5,096 | 4,735 | 9,831 | **1.929** |
   | `hc3_ai` | 418 | 1,151 | 1,151 | 733 | 1,884 | 1.637 |
   | `hc3_human` | 204 | 1,076 | 1,076 | 872 | 1,948 | 1.810 |

   RAID's human sources carry essentially no blank-line structure — 361 paragraphs across
   360 documents — so a human document is usually one long paragraph and yields far more
   adjacent pairs. Human text therefore offers **1.169×** the structural windows per
   sentence versus discovery and **1.188×** versus validation.

   **All AI structural lift figures in this report are understated by approximately
   1.17–1.19×.** The direction is conservative, so no positive claim is inflated, but
   structural lift is not measured on equal footing and the reported values should be
   treated as lower bounds. Correcting `not <X> but <Y>` (discovery lift 0.74) by 1.169
   gives ≈0.87 — still below parity, so that conclusion survives the correction. Not
   corrected in this run: fixing it requires recomputing prevalence against a window
   denominator, which would change numerical results.

6. **The structural catalogue is too small to test.** Four hand-written frames, three of
   which fired. Experiment 01 cannot evaluate the structural hypothesis, only report that
   the current frames are too rare to measure.

7. **Exposure bases differ between pattern kinds.** Structural frames get `2n−1`
   extraction opportunities per `n` sentences where n-grams get `n`, against a shared
   sentence denominator. Lexical and structural results are reported separately for this
   reason and must not be ranked against each other.

8. **Single research group for the primary corpus.** HC3 mitigates this partially, but
   HC3 is one model (ChatGPT, early 2023) and its partitions are small (~1,100 sentences),
   so HC3 agreement is weak evidence.

## 6. Recommendation: **ITERATE**

Not STOP: a *post-hoc exploratory* cross-model signal does exist. In the exploratory
≥5% pass — **not** the pre-registered analysis, which nominated nothing — 10 of 107
candidates survived a change of AI system, 7 of those also surviving into an
independently collected corpus. That is more than noise would predict and the effect
sizes are real if modest. It is a reason to run a better-calibrated experiment, not a
finding to build on.

Not PROCEED: nothing here justifies building a Language Commons. The pre-registered
experiment returned nothing, the survivors are mostly genre vocabulary, and the structural
frames that motivated the project are too rare to measure. Building infrastructure on
this would be building on `such as`.

Iterate on, in priority order:

1. **Domain-stratified nomination and per-domain lift.** Genre is the dominant confound.
   A pattern should have to clear its bar within multiple domains independently.
2. **Paired sampling by source document.** Select human sources first, then every model's
   generation of those same sources, so discovery/validation/human share identical
   underlying material.
3. **A contemporary-human baseline.** Until this exists, no causal claim about AI is
   available at all.
4. **Frame induction instead of hand-written frames.** Four frames cannot test a
   structural hypothesis. Candidate frames should be induced from data — the clustering
   step `EXPERIMENT_V0.1.md` defers to a later version.
5. **Normalise paragraph structure**, or measure structural frames against an
   adjacency-pair denominator rather than a sentence denominator.
6. **Pre-register thresholds against a pilot sample**, so the floor is calibrated before
   it becomes load-bearing.

## 7. Reproducing this run

```bash
python scripts/fetch_corpus.py      # ~11.8 GB RAID + 17.7 MB HC3 -> corpora/_raw/ (git-ignored)
python scripts/build_corpus.py      # two streaming passes -> partitions + corpora/metadata.csv
python scripts/run_experiment_01.py # -> results_experiment_01.csv
```

Optional: `python scripts/build_corpus.py --survey` re-prints the strata tally.
`python scripts/fetch_corpus.py --skip-raid` fetches HC3 only.

Sampling is seedless-deterministic, so a rerun reproduces the identical corpus provided
the upstream files are unchanged. `fetch_corpus.py` computes a **full-file SHA-256** for
each raw download and compares it against the hash HuggingFace publishes, reporting
`VERIFIED` or `MISMATCH` per file. An earlier version hashed only the first 16 MB, which
would not have detected corruption past that point.

Verified corpus hashes:

| File | Bytes | Full SHA-256 | Status |
|---|---:|---|---|
| RAID `train.csv` | 11,779,491,051 | `52f04ceebc126064e68fbd22d8b736964065745464f4bfd52e488150b49f84e4` | VERIFIED against upstream |
| RAID `extra.csv` | 3,707,337,095 | `fed9b80bd6a5712bd49bd035cf92500ac1c562a2da3bbf9a4518b1308b5fbc1f` | VERIFIED, then deleted — no English prose, unused |

Machine-readable output: `experiment_01_patterns.csv` — 110 rows, none of which is a
primary result. See `experiment_01_patterns.NOTES.md`, which explains why the
pre-registered result appears nowhere in the data file: it is empty, and a
one-row-per-candidate CSV cannot represent an empty candidate set without fabricating a
row. Every row carries `is_primary_result = False`; `analysis_label` separates
`post_hoc_exploratory` (107) from `structural_exhaustive_descriptive` (3).
