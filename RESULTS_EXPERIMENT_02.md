# Results — Experiment 02: Cross-model replicated convergence

**Date:** 2026-08-15
**Design:** [`EXPERIMENT_02.md`](EXPERIMENT_02.md), frozen before data acquisition
**Predecessor:** [`RESULTS_EXPERIMENT_01.md`](RESULTS_EXPERIMENT_01.md) — recommendation `ITERATE`

This document separates two things that must not be conflated:

- the **operational confirmatory result** — what satisfied the frozen statistical criteria;
- the **construct-validity interpretation** — whether that result measures what Compost
  set out to measure.

The first is fixed and reported without adjustment. The second is interpretation, and it
does not change the first.

---

## Part I — Operational confirmatory result

### Corpus

| | |
|---|---|
| Documents | **2,800** |
| N | **70** sources per domain per phase |
| Domains | abstracts, books, news, recipes, wiki |
| Discovery models | chatgpt, mistral-chat, mpt-chat |
| Validation models | gpt4, llama-chat, cohere-chat |
| Configuration | `attack=none`, `decoding=greedy`, `repetition_penalty=no` |

### Integrity checks — all passed

| Check | Result |
|---|---|
| Sources per domain per phase | 70 / 70 across all five domains |
| Discovery ∩ validation | **0** |
| Selected ∩ calibration | **0** — all 575 calibration sources excluded |
| Sources missing a model | **0** (all six required per §2.4) |
| Documents written | 2,800, matching the expected count exactly |

### Canonical hashes

```
anchor set (117)      2b712d70b3c0051b29fd9c5b3b760199c6f0ad216733a409489ab65874d3688b
corpus metadata       a57707e0531a1da9f2c458139af5437e06e4cc1a0b7727f2aa45880039b10f31
corpus content digest 8bc244b558298fb4c5a69600c246f58d910a53df2127ca597efc04b30b440030
candidate artifact    c282003498b731aac943e97010cc9a592f25e6d272346134d25a60fb574d3587
RAID train.csv        52f04ceebc126064e68fbd22d8b736964065745464f4bfd52e488150b49f84e4
```

All are **canonical-content** hashes, not raw-byte hashes — see Part III.

### Result

| Stage | Count |
|---|---:|
| Patterns reaching cell floors in ≥1 discovery cell | 3,937 |
| **Discovery candidates** (≥3 of 5 domains) | **72** |
| — lexical | 1 |
| — within-sentence structural | 62 |
| — cross-sentence structural | 9 |
| **Replicated in held-out validation** | **31** |
| — lexical | **0** |
| — within-sentence structural | 27 |
| — cross-sentence structural | 4 |

Nomination used the discovery phase only. The candidate set was frozen to a hashed
artifact before validation ran, and no candidate was added or removed afterwards.

### Bootstrap

930 cells, 2,000 resamples each. Source clusters resampled with replacement within domain;
**models never resampled**, since the six families were chosen rather than drawn. 95%
percentile intervals. **No p-values and no significance claims** — none are computed
anywhere in the pipeline.

### Echo diagnostics

| Phase | Total occurrences | Echoing | Fraction |
|---|---:|---:|---:|
| Discovery | 2,533,851 | 25,586 | **1.010%** |
| Validation | 2,726,456 | 27,680 | **1.015%** |

Echo sets were built per source and applied symmetrically to the AI arms and the matched
human control. The two phases agree to within 0.005 percentage points, and the correction
is small enough that it cannot be driving the result in either direction.

### Stop conditions

**None fired on this run.** All six §10 conditions were evaluated; the corpus hash, the
anchor hash and coverage all verified.

---

## Part II — Construct-validity interpretation

**The 31 replicated patterns are, without exception, generic syntactic scaffolding.**

### Classification

| Category | Count |
|---|---:|
| Generic syntactic scaffolding | **31** |
| Recognisable rhetorical or linguistic constructions | **0** |
| Ambiguous or mixed | **0** |

This is not a judgement call at the margin. Across all 31 patterns, the complete anchor
vocabulary is ten tokens:

```
and (21)   of (16)   a (12)   the (10)   . (6)
is (4)     to (2)    that (2)   for (1)   , (1)
```

Determiners, prepositions, a coordinator, a copula, a complementiser, and punctuation.
**Not one of the 31 contains a negation, contrast, correlative or reframe marker** — no
`not`, `but`, `isn't`, `only`, `also`, `rather`, `instead`, `whether`, `neither`, `nor`.
The anchor set contains all of those; none survived.

### Representative examples

Within-sentence (27), for example:

```
<X> is a               a <X> of <X>            of <X> and
a <X> that             the <X> of <X> and      to <X> and <X>
<X> the <X> and <X>    a <X> of <X> and <X>    <X> for <X> and
```

Cross-sentence (4), the complete set:

```
. the <X> is        <X> . the <X> is        and <X> . the        and <X> . the <X>
```

The cross-sentence family is the clearest illustration. These frames are not rhetorical
moves spanning a sentence boundary; they are *sentence-initial `the`* preceded by the end
of the previous sentence. The cross-sentence window family — added specifically so that
constructions like `The real question isn't X. It's Y.` could be seen at all — replicated
only the fact that English sentences often begin with a definite article.

### Does this measure what Compost intends to measure?

**No.** Compost's structural representation exists to capture rhetorical convergence: the
reframes, contrasts and correlative constructions that motivated the project. What
replicated is English grammar.

`<X> is a` occurring more often in AI text than in matched human source text is a real,
reproducible difference. It is not a rhetorical epiphany that eighteen thousand agents had
this week. It reflects that these models write more predicate-nominal sentences, more
coordinated noun phrases and more prepositional modification than the human source
documents they were asked to work from — a difference in syntactic density, not in
rhetorical style.

**A statistically replicated generic syntactic skeleton is not validation of rhetorical
convergence.** It passed the frozen operational criteria, and those criteria were correct
to apply mechanically, but passing them is not the same as being the thing we set out to
find.

### The lexical result deserves separate note

The single lexical candidate was **`such as`** — Experiment 01's most prevalent pattern, at
19.4% document prevalence there. It was the only lexical pattern to clear discovery
nomination in Experiment 02, and it **failed held-out validation**.

So the lexical arm of Experiment 02 replicated **nothing**. Experiment 01's most
conspicuous lexical finding did not survive a change of models and sources under the
tightened per-domain, per-model criteria. That is a clean negative result and it should be
read as such.

### Why this happened, and what it is not

This is a limitation of the **representation**, not of the pipeline. Skeletonisation with a
117-anchor set and a 1–3 slot allowance can express `not <X> but <Y>`, but it can equally
express `a <X> of <X>`, and the latter is enormously more frequent. The frozen ≥10%
document-prevalence floor — a scope decision, and a defensible one — then selects for
exactly the high-frequency grammatical patterns that clear it most easily.

**No exclusion rule was created and nothing was re-scored.** Narrowing the anchor set or
adding a "rhetorical-only" filter now would be tuning the instrument to the answer, which
is precisely the discipline `EXPERIMENT_02.md` §3.4 froze the anchor set to prevent. Any
redesign belongs to a future experiment with its own pre-registration.

---

## Part III — The stopped run, recorded transparently

A first confirmatory run executed on 2026-08-15 and **stopped** on §10 condition 3.

**Cause.** The recorded anchor hash was
`1b74a52365ebbbb1d97733efc504f279982e394a814036e52415e78c73c9187e` against the committed
`2b712d70…3688b`. Raw-byte SHA-256 is platform-dependent under `core.autocrlf=true`: the
working copy held 117 CRLF endings (732 bytes), the committed blob held LF (615 bytes).

**The parsed 117-anchor content was identical** between the two representations, verified
by parsing both and comparing the sets. This was an **integrity-mechanism defect, not an
anchor-content mismatch** — the run used the correct anchors throughout; what failed was
the mechanism for proving it.

**Provisional numbers from the stopped run: 72 discovery candidates, 31 replications.**

**The repair preceded confirmatory acceptance.** Canonical-content hashing replaced
raw-byte hashing before any result was accepted: text normalised to LF with deterministic
final-newline handling, JSON hashed as a canonical serialisation with sorted keys.
`.gitattributes` pins text formats to LF as hygiene, but the guarantee is the canonical
hashing, which holds even where checkout settings do not. Eight regression tests assert
that LF, CRLF and CR forms hash identically and that a raw-byte hash *would* have differed.

**The clean rerun reproduced the stopped run exactly**: 3,937 → 72 → 31, with identical
per-domain sentence and pair counts and echo fractions agreeing to four decimal places.

**The stopped run's numbers are corroborative only.** They are not the official result. The
official result is the clean rerun reported in Part I.

---

## Part IV — Primary conclusion

> Experiment 02 found cross-model replicated differences under the frozen operational
> criteria, with 31 of 72 discovery candidates replicating in held-out models and sources.
> However, the structural representation produced **exclusively** generic syntactic
> scaffolding — not merely predominantly — with zero of 31 replicated patterns containing
> any negation, contrast or reframe marker, and the sole lexical candidate failing
> validation. Experiment 02 therefore **demonstrates reproducibility under the frozen
> operational criteria**, and the correctness of the pipeline, but **does not validate the
> current structural representation as a measure of rhetorical convergence.**

The wording departs from the draft in one respect, and deliberately: the draft anticipated
a set *dominated by* scaffolding. Systematic inspection found it to be entirely so. The
stronger claim is the accurate one, so it is the one recorded.

---

## Part V — Explicit non-claims

Carried forward unchanged from `EXPERIMENT_02.md` §1:

1. **No AI-authorship classification.** No document is classified; no per-document score exists.
2. **No causal claim.** RAID has no contemporary-human stratum, so every comparison is
   AI vs human *source material*, never AI vs recent human writing.
3. **No generalisation beyond the six named model families.** The claim is conditional on
   chatgpt, mistral-chat, mpt-chat, gpt4, llama-chat and cohere-chat.
4. **No significance testing.** No permutation test, no p-value. Labels were not randomised.
5. **Nothing about repetition penalty** — unavailable for half the model set.
6. **Nothing about conversational register** — `reddit` excluded.
7. **Nothing about patterns below the prevalence floor.** Sub-floor patterns are out of
   scope, not shown absent.

Added by this experiment:

8. **31 replicated patterns does not mean 31 useful Compost patterns.** None of the 31 is
   a candidate for a Pattern Card.
9. **Statistical replication does not establish construct validity.** Satisfying a frozen
   operational criterion is evidence that a measurement is reproducible, not evidence that
   it measures the intended construct.

---

## Artifacts

| File | Contents |
|---|---|
| `experiment_02_corpus_provenance.json` | corpus metadata SHA, content digest, filters, exclusion counts |
| `experiment_02_discovery_candidates.json` | the 72 frozen candidates with qualifying domains and models |
| `experiment_02_discovery_candidates.sha256` | candidate artifact canonical hash |
| `experiment_02_lift_matrix.csv` | full lift matrix — 2,160 rows, per pattern × phase × domain × model, with bootstrap intervals |
| `experiment_02_summary.json` | counts, echo diagnostics, bootstrap methodology, all hashes |

Raw corpus text is git-ignored and is not committed.

## Reproducing

```bash
python scripts/build_exp02_corpus.py    # 2,800 documents, invariants verified, STOPs on failure
python scripts/run_experiment_02.py     # discovery -> freeze -> validation -> bootstrap
```

Source selection is seedless-deterministic on `sha256(source_id)`; the calibration
exclusion list is read as a hard filter.
