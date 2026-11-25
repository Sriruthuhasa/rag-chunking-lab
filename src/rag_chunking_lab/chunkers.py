"""Three chunking strategies. Every chunk keeps its source, index and char offsets.

The invariant for all strategies: ``text[chunk.start:chunk.end] == chunk.text``.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

_SENTENCE_END = re.compile(r"[.!?]+[\"')\]]*(?=\s|$)")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str
    index: int
    start: int
    end: int
    strategy: str
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _strip_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Shrink [start, end) so it has no leading or trailing whitespace."""
    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def _make(text, spans, source, strategy, metas=None):
    chunks = []
    for i, (s, e) in enumerate(spans):
        meta = metas[i] if metas else {}
        chunks.append(Chunk(text[s:e], source, len(chunks), s, e, strategy, dict(meta)))
    return chunks


def chunk_fixed(text: str, size: int = 500, overlap: int = 50, source: str = "<text>") -> list[Chunk]:
    """Fixed-size character windows; each window starts ``size - overlap`` after the last."""
    if size <= 0:
        raise ValueError("size must be > 0")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be >= 0 and smaller than size")
    spans, step, pos = [], size - overlap, 0
    while pos < len(text):
        s, e = _strip_span(text, pos, min(pos + size, len(text)))
        if s < e:
            spans.append((s, e))
        if pos + size >= len(text):
            break
        pos += step
    return _make(text, spans, source, "fixed")


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) spans of sentences. Simple rule: ends at . ! ? before whitespace."""
    spans, pos = [], 0
    for m in _SENTENCE_END.finditer(text):
        s, e = _strip_span(text, pos, m.end())
        if s < e:
            spans.append((s, e))
        pos = m.end()
    s, e = _strip_span(text, pos, len(text))
    if s < e:
        spans.append((s, e))
    return spans


def chunk_sentences(text: str, max_chars: int = 500, source: str = "<text>") -> list[Chunk]:
    """Pack whole sentences into chunks of up to ``max_chars``.

    A single sentence longer than ``max_chars`` becomes its own chunk (it is never cut).
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    spans, cur = [], None
    for s, e in split_sentences(text):
        if cur is None:
            cur = [s, e]
        elif e - cur[0] <= max_chars:
            cur[1] = e
        else:
            spans.append(tuple(cur))
            cur = [s, e]
    if cur is not None:
        spans.append(tuple(cur))
    return _make(text, spans, source, "sentence")


def chunk_markdown(text: str, max_chars: int = 1000, source: str = "<text>") -> list[Chunk]:
    """Split on markdown headings; each chunk carries its heading path in ``meta['headings']``.

    Sections longer than ``max_chars`` are split further with ``chunk_sentences``.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    matches = list(_HEADING.finditer(text))
    bounds = [0] + [m.start() for m in matches] + [len(text)]
    stack: list[tuple[int, str]] = []
    spans, metas = [], []
    for i in range(len(bounds) - 1):
        sec_start, sec_end = bounds[i], bounds[i + 1]
        if i > 0:
            m = matches[i - 1]
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
        meta = {"headings": [t for _, t in stack]}
        s, e = _strip_span(text, sec_start, sec_end)
        if s >= e:
            continue
        if e - s <= max_chars:
            spans.append((s, e))
            metas.append(meta)
        else:
            for sub in chunk_sentences(text[s:e], max_chars=max_chars):
                spans.append((s + sub.start, s + sub.end))
                metas.append(meta)
    return _make(text, spans, source, "markdown", metas)
