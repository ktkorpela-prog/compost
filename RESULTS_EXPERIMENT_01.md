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
| RAID `train.csv` | primary | Dugan et al., ACL 2024, arXiv:2405.07940. 11,779,491,051 bytes, `sha256[:16MB]=9a89907e44073cca` |
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

Human documents are matched: only human rows whose id appears as the `source_id` of a
sampled generation were eligible. 720 AI documents drew on 704 distinct source ids.

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

## 3. Strongest replicated patterns

All lexical; all from the post-hoc exploratory set. `hc3_lift` is the independent
corpus (different research group, different domains, different model).

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

5. **Paragraph structure differs systematically between partitions.** `human_baseline`
   has 361 paragraphs across 360 documents — RAID's human sources carry essentially no
   blank-line structure — against 1,518 and 2,076 for the AI partitions. Since structural
   adjacency is paragraph-scoped, human text gets *more* adjacent-sentence pairs per
   sentence than AI text. This biases structural lift downward for AI. Conservative in
   direction, but real, and it means structural lift is not measured on equal footing.

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

Not STOP: a cross-model replication signal does exist. 10 of 107 candidates survived a
change of AI system, 7 of those also surviving into an independently collected corpus.
That is more than noise would predict and the effect sizes are real if modest.

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
the upstream files are unchanged; `fetch_corpus.py` prints a size and hash prefix for
each raw file to detect upstream drift.

Machine-readable output: `experiment_01_patterns.csv` — 110 rows, one per frozen
candidate, with a `candidate_set` column separating `preregistered` (empty),
`exploratory` (post-hoc) and `structural_exhaustive`.
