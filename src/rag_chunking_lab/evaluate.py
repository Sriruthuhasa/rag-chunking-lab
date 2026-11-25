"""Small quality report for a list of chunks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .chunkers import Chunk

_CLEAN_END = re.compile(r"[.!?:][\"')\]]*$")
_NOT_PROSE = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|```|\|)")


@dataclass(frozen=True)
class ChunkReport:
    count: int
    mean_len: float
    max_len: int
    min_len: int
    mid_sentence_breaks: int

    def to_dict(self) -> dict:
        return asdict(self)


def ends_mid_sentence(chunk_text: str) -> bool:
    """True when the chunk stops in the middle of a sentence.

    Headings, list items, code fences and table rows are not prose, so they count as clean.
    """
    stripped = chunk_text.rstrip()
    if not stripped:
        return False
    last_line = stripped.splitlines()[-1]
    if _NOT_PROSE.match(last_line):
        return False
    return not _CLEAN_END.search(stripped)


def evaluate_chunks(chunks: list[Chunk]) -> ChunkReport:
    """Count, mean/max/min length, and how many chunks end in the middle of a sentence."""
    if not chunks:
        return ChunkReport(0, 0.0, 0, 0, 0)
    lengths = [len(c.text) for c in chunks]
    return ChunkReport(
        count=len(chunks),
        mean_len=round(sum(lengths) / len(lengths), 1),
        max_len=max(lengths),
        min_len=min(lengths),
        mid_sentence_breaks=sum(1 for c in chunks if ends_mid_sentence(c.text)),
    )
