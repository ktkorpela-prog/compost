"""Canonical-content hashing for Experiment 02 artifacts.

Experiment 02's confirmatory run stopped on §10 condition 3 — a lexicon hash
mismatch. The anchor content was identical; what differed was line endings.
``core.autocrlf=true`` rewrites CRLF on checkout, so a raw-byte SHA-256 of a
working-copy text file is platform-dependent and cannot serve as an integrity
guarantee.

The fix is to hash **canonical content** rather than raw bytes. Two functions,
one per artifact class, both platform-independent by construction:

``canonical_text_sha256``  decode UTF-8, normalise CRLF/CR to LF, apply
                           deterministic final-newline handling, hash the
                           canonical UTF-8 bytes.
``canonical_json_sha256``  hash a deterministic canonical JSON serialisation:
                           sorted keys, fixed separators, no incidental
                           whitespace, so formatting cannot move the hash.

``.gitattributes`` pins the repository's text formats to LF as hygiene, but the
integrity guarantee is these functions, not the checkout settings. Hygiene can
be misconfigured on a contributor's machine; canonical hashing cannot.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonicalise_text(text: str) -> bytes:
    """CRLF and CR collapse to LF; exactly one trailing newline on non-empty text."""
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    stripped = normalised.rstrip("\n")
    if not stripped:
        return b""
    return (stripped + "\n").encode("utf-8")


def canonical_text_sha256(text: str) -> str:
    """SHA-256 of canonical text content.

    Takes text, never a path. Sniffing whether a string is a filename would make
    the hash depend on the filesystem — a short single-line document could be
    mistaken for a path — so callers read files themselves via
    :func:`canonical_text_file_sha256`.
    """
    if isinstance(text, Path):
        raise TypeError("pass text, not a Path; use canonical_text_file_sha256")
    return hashlib.sha256(canonicalise_text(text)).hexdigest()


def canonical_text_file_sha256(path: str | Path) -> str:
    """SHA-256 of a text file's canonical content."""
    return canonical_text_sha256(Path(path).read_text(encoding="utf-8"))


def canonicalise_json(obj) -> bytes:
    """Deterministic serialisation: sorted keys, no incidental whitespace."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def canonical_json_sha256(obj) -> str:
    """SHA-256 of canonical JSON. Reformatting the file cannot change this."""
    return hashlib.sha256(canonicalise_json(obj)).hexdigest()


def canonical_json_file_sha256(path: str | Path) -> str:
    """Load a JSON file and hash its canonical form, ignoring how it was written."""
    return canonical_json_sha256(json.loads(Path(path).read_text(encoding="utf-8")))
