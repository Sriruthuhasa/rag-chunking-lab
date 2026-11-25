"""Command line: rag-chunk FILE [--strategy fixed|sentence|markdown|all] [--json]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .chunkers import chunk_fixed, chunk_markdown, chunk_sentences
from .evaluate import evaluate_chunks

STRATEGIES = ["fixed", "sentence", "markdown"]


def run_strategy(name: str, text: str, size: int, overlap: int, source: str):
    if name == "fixed":
        return chunk_fixed(text, size=size, overlap=overlap, source=source)
    if name == "sentence":
        return chunk_sentences(text, max_chars=size, source=source)
    return chunk_markdown(text, max_chars=size, source=source)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="rag-chunk", description="Chunk a document and compare strategies.")
    p.add_argument("file", help="text or markdown file ('-' reads stdin)")
    p.add_argument("--strategy", choices=STRATEGIES + ["all"], default="all")
    p.add_argument("--size", type=int, default=500, help="max chunk size in characters (default 500)")
    p.add_argument("--overlap", type=int, default=50, help="overlap for the fixed strategy (default 50)")
    p.add_argument("--json", action="store_true", help="print every chunk as one JSON line")
    args = p.parse_args(argv)

    if args.file == "-":
        text, source = sys.stdin.read(), "<stdin>"
    else:
        path = Path(args.file)
        text, source = path.read_text(encoding="utf-8"), path.name

    names = STRATEGIES if args.strategy == "all" else [args.strategy]
    try:
        results = {n: run_strategy(n, text, args.size, args.overlap, source) for n in names}
    except ValueError as exc:
        p.error(str(exc))

    if args.json:
        for chunks in results.values():
            for c in chunks:
                print(json.dumps(c.to_dict(), ensure_ascii=False))
        return 0

    print(f"{'strategy':<10} {'chunks':>6} {'mean':>7} {'max':>5} {'min':>5} {'mid-sentence':>13}")
    for name, chunks in results.items():
        r = evaluate_chunks(chunks)
        print(f"{name:<10} {r.count:>6} {r.mean_len:>7} {r.max_len:>5} {r.min_len:>5} {r.mid_sentence_breaks:>13}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
