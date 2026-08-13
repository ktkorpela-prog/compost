# Changelog

Notable changes to Compost. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

Nothing on `main` beyond `0.1.0` at time of writing.

### Planned — not yet merged

The following exists only on the local branch `fix/adjacent-sentence-structural-frames` (commit `d19c9d1`). **It is not part of `main` and has not been published.** It is recorded here so the decisions are not lost, and moves to a released section only when merged.

- **Fix:** structural frames detected across adjacent sentences. A reframe written across a full stop was invisible while the comma form was counted, suppressing the signal where the hypothesis expects it.
- **Change:** structural extraction runs over each sentence and each directly adjacent sentence pair, confined to one paragraph; overlapping matches of the same frame collapse to one occurrence.
- **Change:** sentences segmented per paragraph rather than per document. The segmentation rule is unchanged, only its scope. Affects sentence counts only for segments lacking terminal punctuation.
- **Removed:** structural frame `whether <X> or <Y>` — ordinary English subordination rather than a rhetorical construction.

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

- The ranked CSV mixes n-gram and structural rows against a shared sentence denominator despite different exposure bases. Within-kind comparison is unaffected; cross-kind ranking is not meaningful.
- Sentence segmentation is regex-based and unbenchmarked.
- `paragraphs()` splits on blank lines, which dataset-derived corpora may not carry.
