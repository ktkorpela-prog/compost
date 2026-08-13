# Reading `experiment_01_patterns.csv`

## The primary result is not in this file, because it is empty

Experiment 01's pre-registered analysis nominated **zero candidates**. The rule required
a pattern to appear in ≥25% of AI discovery documents; the most widespread pattern across
360 AI documents is `such as` at 19.4%, so the floor was unreachable by construction.

A CSV of one-row-per-candidate cannot represent an empty candidate set. There is no
honest row to write, and writing a placeholder row would fabricate a result that does not
exist. So **the primary finding of Experiment 01 is recorded here in prose and nowhere in
the data file.**

Every one of the 110 rows carries `is_primary_result = False`. If you are reading the CSV
without this note, that column is the signal: nothing in the file is a confirmatory
finding.

## What the rows are

| `analysis_label` | Rows | What it means |
|---|---:|---|
| `post_hoc_exploratory` | 107 | Nominated at a ≥5% document-prevalence floor chosen **after** inspecting the discovery distribution. Post-hoc. Not confirmatory. |
| `structural_exhaustive_descriptive` | 3 | Every structural frame that fired in discovery, with no threshold applied. Descriptive, so no selection bias is possible — but also not a pre-registered test. |
| `preregistered_primary` | **0** | The pre-registered analysis. Empty by result, not by omission. |

## Provenance columns

- `is_primary_result` — `False` on every row in this file.
- `analysis_label` — as above.
- `nomination_floor` — document-prevalence floor actually applied (`0.05`, or `none` for the exhaustive structural set).
- `preregistered_floor` — `0.25`, the floor that was pre-registered and produced nothing.
- `preregistered_candidate_count` — `0`.

## Caveats that apply to every number in this file

1. **Lift is computed against a pooled human baseline**, roughly half source-matched
   (55.2% discovery, 47.2% validation, 5 shared sources). Discovery and validation do not
   share a common matched control.
2. **Structural rows are denominated by sentences** while structural frames are extracted
   over sentence *and* adjacent-pair windows. AI structural lift is understated by
   approximately 1.17–1.19×. Treat structural lift as a lower bound.
3. **Lexical and structural rows must not be ranked against each other** — they have
   different exposure bases against a shared denominator.
4. Lift uses a 0.5 continuity correction, so very high lifts on rare patterns
   (`ingredients 1` at 64×) reflect tiny denominators, not strong effects.

## Amendment history

The CSV was amended in place to add the five provenance columns. No pre-existing value was
altered — verified by comparing every field of every row before and after (0 changes).
Extraction was not re-run and no number was recomputed. `scripts/run_experiment_01.py`
emits the same columns for future runs.

Full record: `RESULTS_EXPERIMENT_01.md`.
