# Experiment 02 — Cross-model replicated convergence

**Status:** design frozen, not implemented.
**Predecessor:** [`RESULTS_EXPERIMENT_01.md`](RESULTS_EXPERIMENT_01.md) — recommendation `ITERATE`.

Every decision in this document is frozen before data acquisition. Thresholds derive
from Experiment 01's published distributions and are not tuned during execution.

## 1. Hypothesis and non-claims

### Hypothesis

**H1 — cross-model replicated convergence.** A language pattern that is elevated in AI
output relative to source-matched human controls, in at least 2 of 3 generating models
within a domain, across at least 3 of 5 domains, independently in both a discovery phase
and a held-out validation phase using disjoint source documents and disjoint model
families, exhibits cross-model replicated convergence.

- **H1a** — lexical patterns (within-sentence n-grams).
- **H1b** — structural patterns (mechanically induced skeletons, within- and cross-sentence).

**H0** — apparent elevation is explained by domain, by a single model family, by prompt
material, or by source-sampling variation.

### Non-claims

This experiment does **not** claim, and its design cannot support:

1. **That any document was written by AI.** No document is classified. No per-document
   score is produced.
2. **That AI caused a change in written English.** RAID has no contemporary-human
   stratum, so every comparison is AI vs human *source material*, not AI vs recent human
   writing. The distinction between "AI-associated" and "AI-caused" is unresolved and
   remains out of scope.
3. **Generalisation to models outside the six named families.** The claim is conditional
   on `chatgpt`, `mistral-chat`, `mpt-chat`, `gpt4`, `llama-chat` and `cohere-chat`.
   The term used throughout is *cross-model replicated convergence*, never
   "model-general" and never "generalises to AI writing".
4. **Statistical significance for AI vs human differences.** No permutation or
   null-hypothesis significance test is performed; see §7.
5. **Anything about repetition penalty.** That axis is unavailable for half the model set
   (§2.3) and is perfectly confounded with model family.
6. **Anything about conversational register.** `reddit` is excluded (§2.2).
7. **Anything about patterns below the prevalence floor.** Patterns under 10% document
   prevalence are out of scope, not shown absent (§6.1).

## 2. Corpus architecture

### 2.1 Source

RAID (Dugan et al., ACL 2024; arXiv:2405.07940), `train.csv`, full SHA-256
`52f04ceebc126064e68fbd22d8b736964065745464f4bfd52e488150b49f84e4`, verified against the
upstream published LFS hash across all 11,779,491,051 bytes.

HC3 (Guo et al., 2023; arXiv:2301.07597) is retained for **feasibility testing and
external replication reporting only**. It never participates in nomination or replication
(§6).

### 2.2 Domains

**Primary domains (5):** `abstracts`, `books`, `news`, `recipes`, `wiki`.

**`reddit` is excluded.** Under the frozen generation configuration, complete six-model
coverage is **36.0%** for `reddit` (640 of 1,779 sources) against 96.4–99.6% for every
other domain. The human sources are unaffected — the loss is entirely on the generation
side, where models produce short reddit-style replies falling below the 400-character
minimum. The 640 survivors are therefore a length-biased subsample: the reddit prompts
that happened to elicit long output from all six models.

Including `reddit` would cap balanced N per domain per split at **320** instead of
**851**, discarding roughly 60% of usable data across the other domains to accommodate
the weakest stratum. Excluding it is a visible scope reduction; including it would be an
invisible confound.

Also excluded, carried forward from Experiment 01: `code`, `czech`, `german` (not English
prose) and `poetry` (line conventions the sentence segmenter is not built for).

### 2.3 Generation configuration — frozen

**`decoding = greedy`, `repetition_penalty = no`.**

`repetition_penalty=yes` exists only for `mistral-chat`, `mpt-chat` and `llama-chat`. It
is absent for `chatgpt`, `gpt4` and `cohere-chat`, so the value `no` is **forced by
availability, not chosen**, and the penalty axis is perfectly confounded with model
family.

Two configurations are common to all six models: `(greedy, no)` and `(sampling, no)`.
`greedy` is chosen because it is deterministic; sampling would add generation-level
randomness on top of the source and model clustering the bootstrap already carries.
Coverage is near-identical between them (9,382 vs 9,353 sources), so the choice costs
nothing.

All rows are further restricted to `attack=none`. RAID ships 11 adversarial
perturbations; `zero_width_space` and `homoglyph` in particular would corrupt extraction.

### 2.4 Phases, sources and models

| Cell | Sources | Models | Role |
|---|---|---|---|
| `DISC_AI` | S_A | chatgpt, mistral-chat, mpt-chat | nomination |
| `DISC_HUM` | S_A | human | source-matched control for `DISC_AI` |
| `VAL_AI` | S_B | gpt4, llama-chat, cohere-chat | confirmation |
| `VAL_HUM` | S_B | human | source-matched control for `VAL_AI` |

`S_A ∩ S_B = ∅` and the model sets are disjoint, so discovery and validation differ on
**both** axes simultaneously.

Human controls are **source-matched within each phase**: every AI cell is compared
against human documents drawn from the identical source documents. Experiment 01's pooled
half-matched baseline is not repeated, and the word "matched" is used only where source
identity actually holds.

Sampling is **seedless-deterministic**: a source is selected when `sha256(source_id)`
ranks among the lowest N within its domain, and the split into S_A / S_B follows the same
ordering. Reproducible with no seed to store, and independent of read order — which
matters because `train.csv` is grouped by domain.

Sources without a ≥400-character human document **and** ≥400-character generations from
all six models under the frozen configuration are excluded entirely; they cannot form a
complete matched cluster.

## 3. Extraction and structural induction

### 3.1 Lexical

Unchanged from Experiment 01: token n-grams of length 2–5 within a single sentence.
N-grams never cross a sentence boundary. Grams composed entirely of function words are
suppressed.

### 3.2 Structural induction — mechanical skeletonisation

Frames are **induced from data**, not hand-written. Four hand-written frames cannot test
a structural hypothesis; Experiment 01 demonstrated this, with only 3 of 4 firing at all.

No LLM is asked whether anything "sounds like AI". That would contaminate the test with
the judgement being measured.

**Normalisation, applied in this fixed order:**

1. Unicode NFKC.
2. Apostrophe folding (`’` `‘` → `'`).
3. Lowercase.
4. **Contraction handling — differs by pattern class.**

   **Structural skeletonisation only:** mechanically unambiguous negative contractions are
   canonicalised to their expanded form, so that equivalent frames do not split into two
   skeletons and halve their own evidence:

   ```
   isn't → is not        aren't → are not      wasn't → was not
   weren't → were not    don't → do not        doesn't → does not
   didn't → did not      won't → will not      can't → can not
   couldn't → could not  shouldn't → should not  wouldn't → would not
   ```

   Each expansion is deterministic and has exactly one reading, so no interpretation is
   introduced. Without this, `The real question isn't X` and `The real question is not X`
   would induce distinct skeletons for one construction.

   **Ambiguous contractions are left unresolved** and remain single tokens: `it's`,
   `that's`, `there's`, `here's` are each ambiguous between *is* and *has*, and resolving
   them would require a judgement this pipeline deliberately refuses to make.

   **Lexical extraction is unchanged.** N-gram extraction sees the original surface forms;
   no canonicalisation is applied to it.
5. Numerals → `<NUM>`. This prevents `1 cup` and `ingredients 1` recipe artifacts from
   re-entering as skeletons.
6. Any token not in the frozen lexicon (§3.4) and not `<NUM>` → `<X>`.
7. **Consecutive identical slots collapse**: `<X> <X> <X>` → `<X>`. This is what makes
   `not <X> but <Y>` match regardless of the length of the intervening phrase.
8. Punctuation: retain `. ! ? , ; :` as tokens; discard all others.

**Qualification constraints for an induced skeleton:**

- ≥2 function-word anchors
- 1–3 slots
- ≤12 tokens

Skeletons are mined over single sentences and over adjacent sentence pairs, using the
same window families as §5.

### 3.3 Correctness oracle — synthetic fixtures

Structural induction is validated against **deterministic synthetic fixtures with known
frames in known positions and known counts**, written before the inducer runs. The
fixture set must include:

- `not <X> but <Y>` within a single sentence and across a sentence boundary;
- `isn't <X> it's <Y>` in both period and comma forms;
- **contracted vs expanded equivalence**: each canonicalised negative contraction
  (rule 4) paired with its expanded form — `isn't`/`is not`, `don't`/`do not`,
  `won't`/`will not` and the rest — asserting that both surface forms induce the
  **identical skeleton** and that their occurrences aggregate rather than split;
- **ambiguous-contraction non-equivalence**: `it's`/`it is` and `that's`/`that has`
  asserting that these are *not* unified, confirming canonicalisation stops where
  ambiguity begins;
- **lexical non-interference**: the same fixtures asserting that n-gram extraction still
  sees original surface forms, so canonicalisation has not leaked out of skeletonisation;
- negative controls that must induce nothing;
- length variants exercising slot collapse (rule 7);
- numeral cases exercising `<NUM>` (rule 5).

Recovery of the four frames committed on `main` is a **required pass**. Failure blocks
the experiment.

HC3 is **not** a correctness oracle. Nobody knows HC3's true frame inventory, so
agreement there would prove nothing and disagreement would be uninterpretable. HC3 tests
only that the pipeline runs end to end at scale.

### 3.4 Structural anchor set

Committed as `compost/lexicon/structural_anchors_v1.txt` before any Experiment 02 run.
**Its SHA-256 is recorded in every result artifact.** Any change constitutes a new version
and invalidates cross-experiment comparison — enforced by the recorded hash, not by
convention.

The name is deliberate. This set defines which tokens survive as *anchors* under
skeletonisation (rule 6). It is not a general-purpose function-word list and should not be
reused as one.

**Inherited set** — the 59 entries already in `FUNCTION_WORDS` on `main`, retained
unchanged for continuity with Experiment 01:

```
a an and are as at be been but by for from had has have he her hers him his i if in
into is it its me my not of on or our ours she so that the their theirs them they
this to us was we were what when where which who why will with you your
```

**Extensions — project-defined, FROZEN for Experiment 02.**

Provenance of the complete set:

- **59 terms inherited** from the Experiment 01 implementation (`FUNCTION_WORDS` on `main`).
- **58 terms project-defined** during Experiment 02 design, authored for this
  specification.
- **Not claimed to be a canonical linguistic or function-word inventory.** These terms
  derive from no external lexicon, no published word list and no upstream standard. They
  carry no authority beyond this project's own judgement and should not be cited as a
  general-purpose function-word set.
- **Not tuned to Experiment 01 findings.** Notably `such` is absent, so Experiment 01's
  most prevalent lexical pattern `such as` skeletonises to `<X> as`. That is left standing
  deliberately: selecting anchors to make a prior result representable would make the
  anchor set a function of the answer it is used to compute.
- **Any future change requires a new anchor-set version.** `structural_anchors_v1` is
  closed. Adding, removing or substituting a term produces `v2`, with its own SHA-256, and
  invalidates comparison against any result computed under `v1`.

**Total: 117 anchors** (59 inherited + 58 project-defined, no overlap).

```
modals/auxiliaries : do does did can could shall should would may might must
negation/contracted: isn't aren't wasn't weren't don't doesn't didn't won't can't
                     couldn't shouldn't wouldn't it's that's there's here's
prepositions       : about after before between during over under through without
                     against among within across toward
subordinators      : because although while since than though unless whether
correlatives       : either neither nor both only also yet rather instead
```

`if`, `when` and `where` appear in the inherited set and are not duplicated. `whether`
does **not** appear in the inherited set; it is an extension term.

The twelve negative contractions listed above are **redundant under rule 4**, which
canonicalises them to `is not`, `do not` and so on before the anchor lookup runs — both
resulting tokens are already inherited anchors. They are **retained in v1 as defensive
anchors**: should the canonicaliser fail to match a surface form, the contraction survives
as an anchor rather than collapsing to `<X>` and silently destroying the frame. This is a
frozen decision for v1, not an open question.

`can't` canonicalises to `can not`, two tokens, rather than to the single token `cannot`.
`cannot` is not an anchor and would map to `<X>`, destroying the frame it appears in.

## 4. Prompt-echo control

RAID carries `prompt` and `title` per row. Models saw a prompt; human sources did not.
Uncontrolled, this manufactures spurious lift.

**Echo sets are built per source, at both representation levels:**

- **Lexical:** all 2–5-token sequences in the source's `prompt` and `title`, under the
  extraction normalisation.
- **Structural:** the `prompt` and `title` passed through the **identical skeletonisation
  pipeline** (§3.2). An induced skeleton occurrence is echoing when its skeleton appears
  in the source's skeletonised echo set.

Structural echo detection cannot be reduced to lexical matching. A prompt reading "Write
a news article titled X" and a generation opening "Write a blog post titled Y" share no
2–5-gram, yet collapse to the same skeleton.

**Applied symmetrically to both arms.** The echo set is a property of the *source*, not
of the document, and applies to the matched human control as well as the generations.
RAID's titles derive from the human source text, so title tokens recur in human
documents; stripping echoes from the AI arm alone would bias lift downward.

**Disposition — all three, pre-registered:**

| Output | Rule |
|---|---|
| **Primary** | Echoing occurrences **excluded** from both arms. All nomination and replication verdicts derive from this. |
| **Secondary** | Full counts including echo, reported alongside, so the size of the correction is visible. |
| **Diagnostic** | Any pattern above **0.5** AI-arm echo fraction is flagged `PROMPT_DERIVED` and reported separately regardless of verdict. |

## 5. Denominators and metrics

Let *S* = sentences, *P* = eligible adjacent pairs = Σ over paragraphs of max(0, nᵢ − 1),
*D* = documents. Adjacency never crosses a paragraph boundary.

| Pattern class | Exposure unit | Denominator |
|---|---|---|
| Lexical n-gram | sentence | **S** |
| Structural frame fitting within one sentence | single-sentence window | **S** |
| Structural frame spanning two adjacent sentences | adjacent-pair window | **P** |
| Combined structural (reported, flagged) | mixed | S + P |

Each structural occurrence is attributed to the **minimal window containing it** — single
if it fits one sentence, pair otherwise — so within-sentence and cross-sentence rates
never share a denominator.

This removes at source the bias Experiment 01 measured and could only quantify after the
fact: human partitions there offered 1.929 windows per sentence against 1.651 and 1.623
for the AI partitions, understating AI structural lift by ≈1.17–1.19×. Denominating by
*P* makes the human arm's near-absent paragraph structure a measured property rather than
a hidden distortion.

**Reported per pattern, per `(domain, model)` cell:** occurrences; documents containing;
rate per 10,000 exposure units; document prevalence; smoothed lift against that cell's
own source-matched human control, using a 0.5 continuity correction so a zero baseline
never yields infinite lift.

Lexical and structural patterns are reported separately and **must not be ranked against
each other**.

## 6. Nomination and replication

All thresholds are frozen from Experiment 01's published distributions. There is no
calibration slice; §8's pilot tests pipeline feasibility only and touches no threshold.

### 6.1 Cell test — `(domain, model)`

A pattern passes in cell `(d, m)` when, against the source-matched human control of the
same phase:

| Criterion | Value | Provenance |
|---|---|---|
| Lift | **≥1.5** | Exp 01: 60/107 candidates cleared 1.5 in validation, so not trivially passed; survivor val/disc ratio 0.85–1.63, median 1.15 |
| Occurrences | **≥10** | Exp 01's ≥5 was cleared by `ingredients 1` on 7 occurrences at 1.9% document prevalence |
| Document prevalence | **≥10%** | Scope definition, see below |

**The ≥10% floor is a scope decision, not a statistical calibration.** Experiment 02
adjudicates patterns common enough to matter for linguistic saturation. A construction
appearing in fewer than one in ten documents of a domain is not what a Language Commons
is about, whatever its lift. Patterns below the floor are **out of scope**, not shown
absent.

### 6.2 Domain test

Domain *d* qualifies within a phase when:

- the pattern passes the cell test in **≥2 of the 3 models** of that phase, **and**
- the remaining model shows **no strong reversal** — lift ≥0.8.

### 6.3 Pattern test

A pattern exhibits cross-model replicated convergence when it qualifies in **≥3 of the 5
domains**, evaluated **independently in discovery and in validation**, each phase using
its own models and its own disjoint sources.

The full lift matrix — 5 domains × 3 models per phase × 2 phases = 30 cells, equivalently
5 domains × all 6 models = 30 — is reported for every candidate, so concentration is
visible rather than averaged away. The two forms agree because each model belongs to
exactly one phase; no model is evaluated twice.

### 6.4 HC3

Reported as external replication only. Never used in nomination or replication.
Experiment 01 found 3 of 10 RAID-replicated patterns had HC3 lift <1.0 — it contradicts
often enough that folding it into selection would corrupt it.

## 7. Bootstrap and the absence of significance testing

**No AI/human permutation significance test is performed.** Labels were not randomised.
Whether a document is human or model-generated is a fixed property of how RAID was built,
and the exchangeability such a test requires is contradicted by two asymmetries Experiment
01 measured directly: human documents are longer, and carry almost no paragraph
structure. A permutation test resting on a false exchangeability assumption produces
something that looks like inference and is not.

**Source-cluster bootstrap for uncertainty.** Resample *sources* with replacement within
domain, carrying each source's entire cluster — its human document and its model
generations — as an indivisible unit. Recompute prevalence and lift on each resample.
Report percentile confidence intervals.

**Models are never resampled.** The six families are fixed by design, so all inference is
explicitly conditional on them. Resampling models would imply they were drawn from a
population of models; they were chosen. Confidence intervals describe uncertainty arising
from source sampling alone.

**Primary error control is the design, not a distribution.** A pattern must clear on
sources it was not discovered on, generated by models it was not discovered on. That
control is a property of the partitioning and requires no distributional assumption.

**Pipeline stress test (not inference).** The pipeline may be run on constructed data
where both arms are drawn from human documents, with length and paragraph asymmetries
deliberately imposed, to observe how often it emits qualifying verdicts anyway. This is a
defect probe on our own code and thresholds. It is **not** a Type-I rate for the
substantive hypothesis and will not be reported as one.

## 8. Power-simulation gate

Sample size is an **output** of simulation, determined **before** confirmatory extraction.

The independent-Poisson calculation used in earlier drafts is discarded: it assumed
occurrences are independent across documents, which is false in three compounding ways —
generations from one source share a prompt and content, generations from one model share
a generator, documents in one domain share genre.

**Procedure.** Estimate per-document count and exposure distributions, and
intra-source / intra-model / intra-domain correlation, from Experiment 01's committed
per-document data. Simulate corpora across a grid of N, injecting known lifts of 1.3, 1.5
and 2.0 across a prevalence grid. Run the complete nomination and replication pipeline on
each simulated corpus. Power is the proportion of injected patterns reaching the §6.3
verdict.

**Bound: N ≤ 851 sources per domain per split** (§9).

**Gate:** select the smallest N reaching **≥80% power at lift 1.5** within the target
prevalence band.

**If ≥80% power at lift 1.5 is unreachable at N=851, report that and stop.** Thresholds
are not weakened to manufacture a result. A negative feasibility finding is a valid
outcome and is published as one.

**Feasibility pilot.** Runs on HC3 only — already barred from nomination and replication.
It confirms the pipeline runs end to end, the inducer emits sane skeletons, echo detection
fires, denominators compute, and runtimes are tolerable. It consumes no RAID source and
informs no threshold.

## 9. Feasibility ceiling

Verified by streaming `train.csv`, not inferred from row counts. Sources with a
≥400-character human document **and** ≥400-character generations from all six models
under `(greedy, no)`:

| Domain | Human ≥400 | Complete 6-model | Coverage | Max N/split |
|---|---:|---:|---:|---:|
| abstracts | 1,766 | 1,703 | 96.4% | **851** |
| books | 1,781 | 1,760 | 98.8% | 880 |
| news | 1,780 | 1,772 | 99.6% | 886 |
| recipes | 1,772 | 1,761 | 99.4% | 880 |
| wiki | 1,779 | 1,746 | 98.1% | 873 |
| *(reddit, excluded)* | *1,779* | *640* | *36.0%* | *320* |

**Binding constraint: `abstracts` at 851 sources per domain per split.**

Maximum corpus: 851 × 5 domains × 2 splits × (1 human + 3 AI) = **34,040 documents**.

The human arm is the ceiling and cannot be relieved by adding models: each source
contributes exactly one human document, so enlisting more of RAID's eleven models expands
only the AI arm. Above N=851, RAID is exhausted for this design at any configuration.

## 10. Failure and stop conditions

The experiment **stops and reports** — it does not adapt — when any of the following
occurs:

1. **Power gate fails.** ≥80% power at lift 1.5 is unreachable at N=851 (§8).
2. **Inducer fails its oracle.** Synthetic fixtures do not recover the known frames (§3.3).
3. **Lexicon hash mismatch.** The lexicon SHA-256 in an artifact does not match the
   committed lexicon (§3.4).
4. **Corpus hash mismatch.** `train.csv` does not match its upstream published hash (§2.1).
5. **Coverage regression.** Complete six-model coverage falls below the verified figures
   in §9, indicating upstream drift.
6. **Stress test indicates confounding.** The §7 probe emits qualifying verdicts at a rate
   inconsistent with a functioning pipeline.

Anticipated failure modes carried forward, to be reported whether or not they trigger a
stop: skeleton explosion under slot abstraction; induction rediscovering genre boilerplate
(recipe step formatting is highly skeletal); length asymmetry between arms; residual
paragraph-structure asymmetry; chat-tuning confound (both phases are instruction-tuned by
design, so findings concern assistant prose, not base-model completions); unbenchmarked
regex sentence segmentation, which now carries more weight because *P* depends on it.

## 11. Pre-registered execution order

Steps run in this order. Later steps do not inform earlier ones.

1. **Freeze artifacts.** Transcribe the 117 frozen anchors (§3.4) into
   `compost/lexicon/structural_anchors_v1.txt` and record its SHA-256. The anchor set is
   already frozen; this step commits it, it does not reopen it. Commit synthetic fixtures
   with expected skeletons and counts.
2. **Verify integrity.** Confirm `train.csv` full SHA-256 against upstream. Confirm §9
   coverage figures still hold.
3. **Validate inducer.** Run against synthetic fixtures. Must recover the four `main`
   frames. Stop on failure.
4. **Feasibility pilot on HC3.** End-to-end run. Informs no threshold.
5. **Power simulation.** Determine N, bounded at 851. Stop and report if the gate fails.
6. **Build corpus at the determined N.** Source-matched, source-disjoint splits, frozen
   configuration.
7. **Nominate from `DISC_AI` vs `DISC_HUM` only.** Freeze the candidate set.
8. **Evaluate frozen candidates on `VAL_AI` vs `VAL_HUM`.**
9. **Bootstrap** confidence intervals over sources.
10. **Report** HC3 external replication, prompt-echo diagnostics, and the full 30-cell
    lift matrix per candidate.

Result artifacts must record: lexicon SHA-256, corpus SHA-256, frozen configuration,
determined N, and the Experiment 02 spec commit hash.
