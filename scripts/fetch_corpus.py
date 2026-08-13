"""Download the public source datasets for Experiment 01.

Standard library only. Files land in ``corpora/_raw/``, which .gitignore keeps
out of Git: raw corpus text is local by default.

Sources
-------
RAID   Dugan et al., ACL 2024. arXiv:2405.07940
       https://huggingface.co/datasets/liamdugan/raid

       ``train.csv`` is the only usable file of the three, verified by range
       reads rather than by filename:

       - ``test.csv``  (1.2 GB) carries only ``id,generation``. Model labels
         are withheld for the leaderboard, so no labelled comparison.
       - ``extra.csv`` (3.5 GB) is fully labelled but contains only the
         ``german``, ``czech`` and ``code`` domains — no English prose.
       - ``train.csv`` (11.2 GB) is fully labelled and carries the English
         prose domains: abstracts, books, news, recipes, reddit, wiki.

       The file is grouped by domain, so a prefix sample would be biased
       toward whichever domain happens to sort first. Sampling must stream
       the whole file.

HC3    Guo et al., 2023. arXiv:2301.07597
       https://huggingface.co/datasets/Hello-SimpleAI/HC3
       Used as an independent replication corpus assembled by a different
       group. ``reddit_eli5`` is skipped: at 53 MB it dwarfs the other domains
       and would dominate any pooled sample.

Usage
-----
    python scripts/fetch_corpus.py
    python scripts/fetch_corpus.py --skip-raid    # HC3 only, ~17 MB
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "corpora" / "_raw"

RAID_URL = "https://huggingface.co/datasets/liamdugan/raid/resolve/main/train.csv"
HC3_BASE = "https://huggingface.co/datasets/Hello-SimpleAI/HC3/resolve/main"
HC3_DOMAINS = ("open_qa", "wiki_csai", "medicine", "finance")


def download(url: str, dest: Path, chunk: int = 1 << 20) -> None:
    if dest.exists():
        print(f"  exists, skipping: {dest.name} ({dest.stat().st_size:,} bytes)")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": "compost-experiment-01"})
    started = time.time()
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        with tmp.open("wb") as fh:
            while True:
                buf = resp.read(chunk)
                if not buf:
                    break
                fh.write(buf)
                done += len(buf)
                if total:
                    pct = 100 * done / total
                    rate = done / max(time.time() - started, 1e-6) / 1e6
                    print(f"\r  {dest.name}: {pct:5.1f}%  {done/1e6:,.0f}/{total/1e6:,.0f} MB  {rate:.1f} MB/s",
                          end="", flush=True)
    print()
    tmp.replace(dest)


HF_TREE = {
    "raid_train.csv": ("liamdugan/raid", "train.csv"),
    "raid_extra.csv": ("liamdugan/raid", "extra.csv"),
    "hc3_open_qa.jsonl": ("Hello-SimpleAI/HC3", "open_qa.jsonl"),
    "hc3_wiki_csai.jsonl": ("Hello-SimpleAI/HC3", "wiki_csai.jsonl"),
    "hc3_medicine.jsonl": ("Hello-SimpleAI/HC3", "medicine.jsonl"),
    "hc3_finance.jsonl": ("Hello-SimpleAI/HC3", "finance.jsonl"),
}


def upstream_hashes(repo: str) -> dict[str, tuple[str | None, int | None]]:
    """Published SHA-256 (LFS oid) and size for each file in a HuggingFace dataset."""
    url = f"https://huggingface.co/api/datasets/{repo}/tree/main?recursive=1"
    req = urllib.request.Request(url, headers={"User-Agent": "compost-experiment-01"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            tree = json.load(resp)
    except Exception as exc:  # network failure must not mask a good download
        print(f"  ! could not fetch upstream hashes for {repo}: {exc}")
        return {}
    out: dict[str, tuple[str | None, int | None]] = {}
    for entry in tree:
        if entry.get("type") != "file":
            continue
        lfs = entry.get("lfs") or {}
        out[entry["path"]] = (lfs.get("oid"), lfs.get("size") or entry.get("size"))
    return out


def sha256_full(path: Path, chunk: int = 1 << 22) -> str:
    """Full-file SHA-256, so integrity is checked past the first megabytes."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-raid", action="store_true", help="fetch HC3 only")
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)

    if not args.skip_raid:
        print("RAID (Dugan et al., ACL 2024) — train.csv, ~11.2 GB")
        download(RAID_URL, RAW / "raid_train.csv")

    print("HC3 (Guo et al., 2023)")
    for domain in HC3_DOMAINS:
        download(f"{HC3_BASE}/{domain}.jsonl", RAW / f"hc3_{domain}.jsonl")

    print("\nProvenance (full-file SHA-256 verified against upstream where published):")
    cache: dict[str, dict] = {}
    for path in sorted(RAW.glob("*")):
        if not path.is_file() or path.name.endswith(".part"):
            continue
        repo_file = HF_TREE.get(path.name)
        expected_oid = expected_size = None
        if repo_file:
            repo, remote = repo_file
            if repo not in cache:
                cache[repo] = upstream_hashes(repo)
            expected_oid, expected_size = cache[repo].get(remote, (None, None))

        size = path.stat().st_size
        digest = sha256_full(path)
        if expected_oid:
            ok = digest == expected_oid and size == expected_size
            verdict = "VERIFIED" if ok else "MISMATCH"
        else:
            verdict = "unverified (no upstream hash published)"
        print(f"  {path.name:<26} {size:>14,} bytes")
        print(f"    {'sha256':<10} {digest}")
        if expected_oid:
            print(f"    {'upstream':<10} {expected_oid}")
        print(f"    {'status':<10} {verdict}")


if __name__ == "__main__":
    sys.exit(main())
