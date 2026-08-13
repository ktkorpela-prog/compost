# Compost — Project Charter

> **Don't detect the slop. Compost it.**

## What Compost is

Compost is an open experiment in measuring **linguistic convergence** in AI-assisted writing.

AI is already part of how people write. The project does not treat that as misconduct and does not attempt to infer authorship. Instead, it asks a narrower question:

> Which lexical and rhetorical patterns are becoming disproportionately common, and how are those patterns changing over time?

The long-term idea is a community-maintained Language Commons that agents and writers can query before finalising text. A pattern that is currently saturated can be avoided or deliberately retained; a pattern that is fading may eventually become ordinary again. The system describes the language ecosystem. It does not police the writer.

## The problem

AI-assisted prose can converge on repeated vocabulary, sentence frames and rhetorical constructions. Existing discussion often collapses three separate questions:

1. Was AI involved?
2. Is the writing repetitive or stylistically homogeneous?
3. Was authorship misrepresented?

Compost deliberately addresses only the second.

## Core hypothesis

Automatically extracted language patterns discovered in one sample of AI-assisted writing will recur at materially elevated rates across independent AI-assisted samples while remaining less prevalent in reasonably matched human writing.

If that signal does not replicate, the project should change direction before any platform is built.

## What Compost is not

- An AI detector.
- A plagiarism detector.
- A tool for proving or disproving human authorship.
- A blacklist of forbidden words.
- A single opaque "AI score".
- A system that labels common language as bad language.

## Vocabulary

**Prevalence** — how often a pattern occurs in a corpus, with an explicit denominator.

**Lift** — how much more or less prevalent a pattern is relative to a reference corpus.

**Momentum** — whether prevalence is rising, falling or stable across comparable time windows. Not implemented in v0.1, but the data model must not prevent it later.

**Confidence** — evidence that a signal replicates across independent samples; not merely the size of the corpus.

**Pattern** — a lexical phrase or structural language frame observed by a mechanical extractor.

**Language Commons** — the future shared registry of aggregate pattern observations. Not part of v0.1.

## v0.1 decision

v0.1 is a **signal-validation experiment**, not a shippable service.

It contains:

- local corpus ingestion;
- sentence and document counting;
- mechanical lexical and structural pattern extraction;
- prevalence and lift calculation;
- comparison across three corpus states;
- CSV output suitable for inspection and later analysis.

It deliberately does not contain:

- an MCP server;
- an API;
- accounts or identity;
- a public database;
- a dashboard;
- crowdsourcing;
- rewrite suggestions;
- a governance workflow.

Those are roadmap items only if the signal earns them.

## Success

v0.1 succeeds if patterns discovered in one AI-assisted sample replicate in held-out AI-assisted material and remain materially less prevalent in matched human controls.

A null result is a useful result. If the extractor mainly rediscovers ordinary English, genre differences, prompt artefacts or one model's quirks, we should know that before building infrastructure.
