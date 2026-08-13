"""Command-line comparison experiment for Compost v0.1."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .extractor import Pattern
from .scorer import CorpusStats, scan_directory, smoothed_lift


def _summary(stats: CorpusStats) -> str:
    return (
        f"{stats.name}: {stats.documents} docs, {stats.paragraphs} paragraphs, "
        f"{stats.sentences} sentences, {stats.tokens} tokens"
    )


def build_rows(
    pre: CorpusStats,
    contemporary: CorpusStats,
    ai: CorpusStats,
    min_ai_docs: int,
    min_ai_occurrences: int,
) -> list[dict[str, object]]:
    patterns = [
        p
        for p in ai.occurrences
        if ai.documents_with[p] >= min_ai_docs and ai.occurrences[p] >= min_ai_occurrences
    ]

    rows: list[dict[str, object]] = []
    for p in patterns:
        lift_pre = smoothed_lift(ai.occurrences[p], ai.sentences, pre.occurrences[p], pre.sentences)
        lift_contemporary = smoothed_lift(
            ai.occurrences[p], ai.sentences, contemporary.occurrences[p], contemporary.sentences
        )
        rows.append(
            {
                "pattern_kind": p.kind,
                "pattern": p.text,
                "ai_occurrences": ai.occurrences[p],
                "ai_documents_with": ai.documents_with[p],
                "ai_rate_per_10k_sentences": round(ai.per_10k_sentences(p), 4),
                "ai_document_prevalence": round(ai.document_prevalence(p), 6),
                "pre_human_occurrences": pre.occurrences[p],
                "pre_human_rate_per_10k_sentences": round(pre.per_10k_sentences(p), 4),
                "contemporary_human_occurrences": contemporary.occurrences[p],
                "contemporary_human_rate_per_10k_sentences": round(
                    contemporary.per_10k_sentences(p), 4
                ),
                "lift_vs_pre_human_smoothed": round(lift_pre, 4),
                "lift_vs_contemporary_human_smoothed": round(lift_contemporary, 4),
            }
        )

    # Conservative ranking: the weaker of the two human-baseline lifts wins.
    rows.sort(
        key=lambda r: (
            min(
                float(r["lift_vs_pre_human_smoothed"]),
                float(r["lift_vs_contemporary_human_smoothed"]),
            ),
            int(r["ai_documents_with"]),
            int(r["ai_occurrences"]),
        ),
        reverse=True,
    )
    return rows


def write_csv(rows: list[dict[str, object]], output: str | Path) -> None:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare language-pattern prevalence across Compost v0.1 corpora."
    )
    parser.add_argument("--pre-human", required=True, help="Directory of pre-AI human .txt files")
    parser.add_argument(
        "--contemporary-human", required=True, help="Directory of contemporary human .txt files"
    )
    parser.add_argument("--ai", required=True, help="Directory of AI-assisted .txt files")
    parser.add_argument("--output", default="results.csv", help="CSV output path")
    parser.add_argument("--min-ai-docs", type=int, default=2, help="Minimum AI documents containing pattern")
    parser.add_argument(
        "--min-ai-occurrences", type=int, default=2, help="Minimum AI occurrences of pattern"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pre = scan_directory(args.pre_human, "pre_ai_human")
    contemporary = scan_directory(args.contemporary_human, "contemporary_human")
    ai = scan_directory(args.ai, "ai_assisted")

    print(_summary(pre))
    print(_summary(contemporary))
    print(_summary(ai))

    rows = build_rows(pre, contemporary, ai, args.min_ai_docs, args.min_ai_occurrences)
    write_csv(rows, args.output)
    print(f"wrote {len(rows)} candidate patterns to {args.output}")


if __name__ == "__main__":
    main()
