# Experiment v0.1 — Does the signal exist?

## Research question

Can mechanically extracted lexical and structural patterns discovered in AI-assisted writing recur at elevated rates in independent AI-assisted samples while remaining less prevalent in reasonably matched human writing?

This is **not** an authorship-classification experiment.

## Corpus design

Use three states:

- **A — Pre-AI human:** human-authored text from before widespread generative-AI writing adoption.
- **B — Contemporary human:** recent human-authored text with credible provenance and minimal or disclosed AI assistance.
- **C — Contemporary AI-assisted:** text generated or materially assisted by one or more LLMs, with generation provenance where possible.

Genre should be matched as closely as practical. Comparing nineteenth-century fiction with contemporary LinkedIn posts would mostly measure genre and era.

Each file represents one document. The scanner records:

- documents scanned;
- paragraphs scanned;
- sentences scanned;
- tokens scanned;
- occurrences of each pattern;
- documents containing each pattern.

The denominator is part of the observation and must never be discarded.

## Metadata

For serious corpus runs, maintain a `metadata.csv` with at least:

- `file`
- `corpus`
- `date`
- `genre`
- `source`
- `provenance`
- `model` when relevant
- `prompt_family` when relevant

Optional future fields include geography, language variant, editing level and `suggested_by_compost`.

## Candidate patterns in v0.1

The first extractor is deliberately mechanical and interpretable. It emits:

1. **Lexical n-grams** — repeated 2–5 token sequences, excluding candidates made entirely from common function words.
2. **Structural frames** — a small set of generic rhetorical constructions represented as templates, e.g. `not <X> but <Y>` and `<X> isn't about <Y> it's about <Z>`.

No LLM is asked whether a sentence "sounds like AI". That would contaminate the test with the judgement we are trying to measure.

The structural catalogue is intentionally small in v0.1. If the signal exists, later versions can test automatic frame induction and clustering.

### Extraction scope

N-grams are extracted within a single sentence and never cross a sentence boundary.

Structural frames are extracted over two unit families, both confined to a single paragraph:

1. each individual sentence;
2. each pair of directly adjacent sentences.

Non-adjacent sentences are never combined, and the last sentence of a paragraph is not adjacent to the first sentence of the next. Without adjacent pairs, a reframe written across a full stop — `The real question isn't whether AI will replace us. It's what happens when it does.` — is invisible to the extractor, while the same construction written with a comma is counted. That asymmetry would suppress the signal precisely where the hypothesis expects it.

A frame visible inside one sentence is also visible inside the adjacent pair containing that sentence. Matches are therefore resolved to absolute paragraph coordinates and overlapping matches of the same frame collapse to a single occurrence.

Sentence count remains the denominator. A frame spanning two adjacent sentences contributes one occurrence against a denominator that counts both sentences.

### Withdrawn frames

`whether <X> or <Y>` was withdrawn before the first validation run. It matches ordinary English subordination — indirect questions, disjunctive complements, plain conditionals — rather than a rhetorical construction. Its prevalence would be dominated by grammar, appear at similar rates in every corpus, and rank on lift only through sampling variation.

It has not been replaced by a hand-curated phrase list. A withdrawn frame is readmitted only if it can be constrained to a genuinely rhetorical shape.

## Metrics

For each pattern `p` in corpus `c`:

### Sentence prevalence

`occurrences(p,c) / sentences(c)`

Reported as occurrences per 10,000 sentences for readability.

### Document prevalence

`documents_containing(p,c) / documents(c)`

This distinguishes one document repeating a phrase many times from independent recurrence across documents.

### Lift

Lift compares target prevalence with a reference prevalence.

`lift = target_rate / reference_rate`

v0.1 reports a **smoothed lift** using a 0.5 continuity correction so a zero count in a finite reference sample does not produce infinity. The unsmoothed raw rates remain in the output.

Two comparisons are required:

- AI-assisted vs pre-AI human.
- AI-assisted vs contemporary human.

The second is essential: a pattern may have changed because language changed, not because AI caused it.

### Momentum

Not calculated in the first static experiment. It requires comparable timestamped windows. Preserve dates now so it can be added without reconstructing history.

### Confidence

No synthetic 0–100 confidence score in v0.1. Replication is the evidence:

- discover candidates in one partition;
- freeze the candidate set;
- evaluate on held-out material;
- compare across models/sources where possible.

## Discovery and validation

Do not randomly split sentences from the same documents. That creates leakage.

Prefer partitioning by independent source, prompt family, model or document collection. A strong signal should survive a change in sample.

Suggested workflow:

1. Run candidate discovery on `C_discovery`.
2. Rank candidates using prevalence and lift against A and B.
3. Freeze the candidate list.
4. Test those exact candidates on `C_validation`.
5. Report which signals replicate and how much their lift changes.

## First-pass acceptance criteria

These are exploratory gates, not claims of statistical proof.

A candidate is interesting enough for manual review if it:

- appears across multiple documents rather than a single repeated source;
- has non-trivial prevalence in the AI-assisted discovery corpus;
- shows elevated lift against both human baselines;
- retains directionally elevated lift in held-out AI-assisted material.

The project earns a Commons phase only if a meaningful set of candidates survives held-out validation across more than one source/model family.

## Failure modes to inspect

- Genre mismatch.
- Topic leakage: phrases are about AI because the corpus is about AI.
- Prompt leakage: repeated prompt wording creates repeated output wording.
- One-model artefacts presented as universal AI patterns.
- Publication-platform conventions mistaken for AI signals.
- Boilerplate, navigation or metadata entering the corpus.
- Sentence segmentation errors.
- N-gram explosion producing statistically impressive trivia.
- Human controls contaminated by undisclosed AI assistance.

## Privacy and Commons notes — deliberately deferred

A future Commons should not assume a hash is private merely because it is a hash; predictable phrases are dictionary-guessable. A k-contributor threshold can reduce exposure and lazy poisoning but is an exposure control, not a complete privacy or Sybil-resistance guarantee.

Those problems matter, but v0.1 has no networked contribution layer and therefore does not need to pretend they are solved.
