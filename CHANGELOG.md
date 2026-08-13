# Changelog

Notable changes to Compost. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Fixed

- Structural frames are detected across adjacent sentences. A reframe written across a full stop — `The real question isn't whether AI will replace us. It's what happens when it does.` — was invisible to the extractor while the same construction written with a comma was counted. That asymmetry suppressed the signal precisely where the hypothesis expects it, and the test suite stayed green because every structural test used a single-sentence form.

### Changed

- Structural extraction runs over two unit families, both confined to one paragraph: each individual sentence, and each pair of directly adjacent sentences. Non-adjacent sentences are never combined, and a paragraph break ends adjacency.
- Overlapping matches of the same frame collapse to a single occurrence, resolved in absolute paragraph coordinates. Deliberately conservative: distinct overlapping instances of one frame count once.
- Sentences are segmented per paragraph rather than per document. The segmentation rule is unchanged — only its scope. This can only raise sentence counts, and only for segments lacking terminal punctuation such as headings and list fragments; continuous prose is unaffected.
- Lexical n-gram extraction is unchanged and still never crosses a sentence boundary.
- Sentence count remains the prevalence denominator. A frame spanning two adjacent sentences contributes one occurrence against a denominator counting both.

### Removed

- Structural frame `whether <X> or <Y>`. It matches ordinary English subordination — indirect questions, disjunctive complements, plain conditionals — rather than a rhetorical construction, so it would appear at similar rates in every corpus and rank on lift only through sampling variation. Recorded in `WITHDRAWN_STRUCTURAL_RULES`; not replaced by a curated phrase list.

### Added

- Eight regression tests: cross-sentence detection, single-sentence detection, the non-adjacent boundary, de-duplication across overlapping extraction paths, denominator integrity, the paragraph boundary, frame withdrawal, and n-gram containment.

### Known limitations

- Structural frames now get `2n−1` extraction opportunities per `n` sentences where n-grams get `n`, against a shared sentence denominator. Within-kind comparison is unaffected, but the ranked CSV structurally favours frames over n-grams and should not be read as a single leaderboard.

## [0.1.0] — 2026-08-13

Initial public scaffold (`e7ec0fa`). A signal-validation experiment, not a shippable service: no MCP server, API, database, dashboard or crowdsourcing.

### Added

- `PROJECT.md` — charter, core hypothesis, explicit non-goals, success condition.
- `PRINCIPLES.md` — 13 normative guardrails.
- `EXPERIMENT_V0.1.md` — three-state corpus design, prevalence/lift/momentum definitions, discovery-vs-validation partitioning, failure modes.
- `CORPUS_PLAN.md` — RAID and HC3 as first external datasets; temporal baseline outstanding.
- `compost/` — dependency-free Python 3.10+: `normalizer`, `extractor`, `scorer`, `experiment`.
- MIT licence.

### Known limitations

Carried forward because they constrain how results may be read:

- The ranked CSV mixes n-gram and structural rows in one ordering despite their being different classes of pattern; cross-kind ranking is not meaningful.
- Sentence segmentation is regex-based and unbenchmarked.
- `paragraphs()` splits on blank lines, which dataset-derived corpora may not carry.
