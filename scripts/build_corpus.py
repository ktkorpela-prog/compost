"""Build the Experiment 01 corpus partitions from the raw downloads.

Standard library only. Reads ``corpora/_raw/`` and writes one ``.txt`` per
document into partition directories, plus a tracked ``corpora/metadata.csv``
recording provenance for every sampled document.

Partitioning
------------
The independence axis is the **generating model**, not the topic and not a
random split of rows from the same models. Discovery and validation draw from
disjoint model families, so a pattern surviving validation has survived a
change of AI system rather than a change of subject matter.

Both sides are instruction-tuned chat models from three different providers
each. Base completion models (gpt2, gpt3, mistral, mpt, cohere) are excluded
so that "chat-tuned vs base" cannot confound the discovery/validation split;
assistant-style prose is what the project is about.

Domains are held constant across partitions, so genre is matched rather than
confounded.

Sampling procedure
------------------
Deterministic and seedless. A document is selected when sha256(row id) ranks
among the lowest N within its (partition, domain, model) stratum. This is
reproducible without storing a seed and is independent of the order rows are
read, which matters because RAID's train.csv is grouped by domain.

Human documents are **matched**: only human rows whose id appears as the
``source_id`` of a sampled AI generation are eligible, so the human baseline
is the same source material the models were asked to rewrite or continue.

Usage
-----
    python scripts/build_corpus.py --survey    # tally strata, write nothing
    python scripts/build_corpus.py             # build partitions
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "corpora" / "_raw"
CORPORA = ROOT / "corpora"
RAID_CSV = RAW / "raid_train.csv"

csv.field_size_limit(2**31 - 1)

# English prose only. RAID's code/czech/german domains would measure programming
# syntax or non-English grammar; poetry has line conventions the sentence
# segmenter is not built for.
PROSE_DOMAINS = ("abstracts", "books", "news", "recipes", "reddit", "wiki")

# Verified against --survey output. Disjoint, instruction-tuned, 3 providers each.
DISCOVERY_MODELS = ("chatgpt", "mistral-chat", "mpt-chat")
VALIDATION_MODELS = ("gpt4", "llama-chat", "cohere-chat")

DOCS_PER_STRATUM = 20      # per (partition, domain, model)
HUMAN_PER_DOMAIN = 60      # matched human docs per domain
HC3_PER_STRATUM = 40
MIN_CHARS = 400            # skip stubs that cannot carry a multi-sentence structure


def _rank(row_id: str) -> str:
    return hashlib.sha256(row_id.encode("utf-8")).hexdigest()


def _partition_for(model: str) -> str | None:
    if model in DISCOVERY_MODELS:
        return "ai_discovery"
    if model in VALIDATION_MODELS:
        return "ai_validation"
    return None


def _bounded_add(bucket: list, entry: tuple, limit: int) -> None:
    """Keep the `limit` lowest-ranked entries; order-independent."""
    bucket.append(entry)
    if len(bucket) > 2 * limit:
        bucket.sort(key=lambda e: e[0])
        del bucket[limit:]


def survey(path: Path) -> None:
    counters = {k: Counter() for k in ("model", "domain", "attack", "decoding")}
    pairs: Counter[tuple[str, str]] = Counter()
    total = 0
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            total += 1
            for key in counters:
                counters[key][row[key]] += 1
            if row["attack"] == "none" and row["domain"] in PROSE_DOMAINS:
                pairs[(row["model"], row["domain"])] += 1
    print(f"rows: {total:,}\n")
    for name, counter in counters.items():
        print(f"--- {name} ---")
        for key, n in counter.most_common():
            print(f"  {key or '(empty)':<26} {n:>10,}")
        print()
    print("--- (model, domain), attack=none, prose domains ---")
    for (m, d), n in sorted(pairs.items()):
        print(f"  {m:<16} {d:<12} {n:>8,}")


def pass1_select_ai(path: Path) -> tuple[dict[str, list[dict]], dict[str, set[str]]]:
    """Select AI documents; return them plus the source ids they were built from."""
    buckets: dict[tuple[str, str, str], list] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["attack"] != "none" or row["domain"] not in PROSE_DOMAINS:
                continue
            partition = _partition_for(row["model"])
            if partition is None:
                continue
            text = (row["generation"] or "").strip()
            if len(text) < MIN_CHARS:
                continue
            key = (partition, row["domain"], row["model"])
            _bounded_add(
                buckets[key],
                (_rank(row["id"]), row["id"], row["source_id"], row["model"], row["domain"], text),
                DOCS_PER_STRATUM,
            )

    selected: dict[str, list[dict]] = defaultdict(list)
    source_ids: dict[str, set[str]] = defaultdict(set)
    for (partition, domain, _model), bucket in buckets.items():
        bucket.sort(key=lambda e: e[0])
        for rank, rid, src, model, dom, text in bucket[:DOCS_PER_STRATUM]:
            selected[partition].append(
                {"id": rid, "source_id": src, "model": model, "domain": dom,
                 "text": text, "source": "RAID", "rank": rank[:12]}
            )
            source_ids[domain].add(src)
    return selected, source_ids


def pass2_select_human(path: Path, wanted: dict[str, set[str]]) -> list[dict]:
    """Select human rows matched to the source ids of the sampled generations."""
    buckets: dict[str, list] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["model"] != "human" or row["attack"] != "none":
                continue
            domain = row["domain"]
            if domain not in wanted:
                continue
            if row["id"] not in wanted[domain] and row["source_id"] not in wanted[domain]:
                continue
            text = (row["generation"] or "").strip()
            if len(text) < MIN_CHARS:
                continue
            _bounded_add(
                buckets[domain],
                (_rank(row["id"]), row["id"], row["source_id"], domain, text),
                HUMAN_PER_DOMAIN,
            )

    out: list[dict] = []
    for domain, bucket in buckets.items():
        bucket.sort(key=lambda e: e[0])
        for rank, rid, src, dom, text in bucket[:HUMAN_PER_DOMAIN]:
            out.append({"id": rid, "source_id": src, "model": "human", "domain": dom,
                        "text": text, "source": "RAID", "rank": rank[:12]})
    return out


def collect_hc3() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(RAW.glob("hc3_*.jsonl")):
        domain = path.stem.replace("hc3_", "")
        rows = []
        with path.open("r", encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                line = line.strip()
                if line:
                    rows.append((i, json.loads(line)))
        for side, partition, model in (
            ("human_answers", "hc3_human", "human"),
            ("chatgpt_answers", "hc3_ai", "chatgpt"),
        ):
            scored = []
            for i, rec in rows:
                for j, answer in enumerate(rec.get(side) or []):
                    text = (answer or "").strip()
                    if len(text) >= MIN_CHARS:
                        rid = f"hc3-{domain}-{i}-{j}"
                        scored.append((_rank(rid), rid, text))
            scored.sort()
            for rank, rid, text in scored[:HC3_PER_STRATUM]:
                out[partition].append(
                    {"id": rid, "source_id": "", "model": model, "domain": domain,
                     "text": text, "source": "HC3", "rank": rank[:12]}
                )
    return out


def write_partitions(collected: dict[str, list[dict]]) -> list[dict]:
    meta: list[dict] = []
    for partition, docs in sorted(collected.items()):
        target = CORPORA / partition
        target.mkdir(parents=True, exist_ok=True)
        for old in target.glob("doc*.txt"):
            old.unlink()
        for n, doc in enumerate(sorted(docs, key=lambda d: (d["domain"], d["rank"])), start=1):
            name = f"doc{n:04d}.txt"
            (target / name).write_text(doc["text"], encoding="utf-8")
            meta.append({
                "file": f"{partition}/{name}",
                "partition": partition,
                "source": doc["source"],
                "source_id": doc["id"],
                "matched_source_id": doc["source_id"],
                "model": doc["model"],
                "domain": doc["domain"],
                "chars": len(doc["text"]),
            })
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--survey", action="store_true", help="tally strata and exit")
    args = ap.parse_args()

    if args.survey:
        survey(RAID_CSV)
        return

    print("pass 1/2: selecting AI generations ...")
    collected, source_ids = pass1_select_ai(RAID_CSV)
    print(f"  selected {sum(len(v) for v in collected.values())} AI documents; "
          f"{sum(len(s) for s in source_ids.values())} distinct source ids")

    print("pass 2/2: selecting matched human sources ...")
    collected["human_baseline"] = pass2_select_human(RAID_CSV, source_ids)
    print(f"  selected {len(collected['human_baseline'])} human documents")

    for partition, docs in collect_hc3().items():
        collected[partition].extend(docs)

    meta = write_partitions(collected)
    out = CORPORA / "metadata.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(meta[0].keys()))
        w.writeheader()
        w.writerows(meta)

    print(f"\nwrote {len(meta)} documents; provenance -> {out.relative_to(ROOT)}\n")
    by_part: Counter[str] = Counter(m["partition"] for m in meta)
    for partition, n in sorted(by_part.items()):
        models = sorted({m["model"] for m in meta if m["partition"] == partition})
        domains = sorted({m["domain"] for m in meta if m["partition"] == partition})
        print(f"  {partition:<16} {n:>4} docs  models={','.join(models)}")
        print(f"  {'':<16}      domains={','.join(domains)}")


if __name__ == "__main__":
    sys.exit(main())
