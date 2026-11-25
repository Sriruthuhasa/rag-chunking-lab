import json

import pytest

from rag_chunking_lab import (
    chunk_fixed,
    chunk_markdown,
    chunk_sentences,
    evaluate_chunks,
    split_sentences,
)
from rag_chunking_lab.cli import main
from rag_chunking_lab.evaluate import ends_mid_sentence

PROSE = (
    "Retrieval needs good chunks. Small chunks lose context! Large chunks waste tokens? "
    "A balanced size often works best. Overlap can help keep ideas together."
)

MARKDOWN = """# Guide

Intro text for the guide.

## Install

Run pip install. Then import the package.

### Windows

Use py -m pip on Windows.

## Usage

Call chunk_markdown on your text.
"""


def assert_offsets(text, chunks):
    for c in chunks:
        assert text[c.start:c.end] == c.text


# ---------- fixed ----------

def test_fixed_offsets_and_indexes():
    chunks = chunk_fixed(PROSE, size=40, overlap=10, source="doc.txt")
    assert_offsets(PROSE, chunks)
    assert [c.index for c in chunks] == list(range(len(chunks)))
    assert all(c.source == "doc.txt" and c.strategy == "fixed" for c in chunks)
    assert all(len(c.text) <= 40 for c in chunks)


def test_fixed_overlap_shares_text():
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = chunk_fixed(text, size=10, overlap=4)
    assert [c.text for c in chunks] == ["abcdefghij", "ghijklmnop", "mnopqrstuv", "stuvwxyz"]


def test_fixed_rejects_bad_args():
    with pytest.raises(ValueError):
        chunk_fixed("x", size=0)
    with pytest.raises(ValueError):
        chunk_fixed("x", size=10, overlap=10)


def test_empty_text_gives_no_chunks():
    assert chunk_fixed("") == []
    assert chunk_sentences("   \n ") == []
    assert chunk_markdown("") == []


# ---------- sentences ----------

def test_split_sentences():
    spans = split_sentences(PROSE)
    sentences = [PROSE[s:e] for s, e in spans]
    assert sentences[0] == "Retrieval needs good chunks."
    assert sentences[2] == "Large chunks waste tokens?"
    assert len(sentences) == 5


def test_split_sentences_keeps_decimals_together():
    spans = split_sentences("Version 3.12 is out. It is fast.")
    assert len(spans) == 2


def test_sentence_chunks_never_cut_sentences():
    chunks = chunk_sentences(PROSE, max_chars=70)
    assert_offsets(PROSE, chunks)
    assert len(chunks) > 1
    assert all(c.text.endswith((".", "!", "?")) for c in chunks)
    assert evaluate_chunks(chunks).mid_sentence_breaks == 0


def test_long_sentence_becomes_own_chunk():
    text = "Short one. " + "word " * 40 + "end."
    chunks = chunk_sentences(text, max_chars=50)
    assert chunks[0].text == "Short one."
    assert len(chunks[1].text) > 50


# ---------- markdown ----------

def test_markdown_heading_paths():
    chunks = chunk_markdown(MARKDOWN, max_chars=500, source="guide.md")
    assert_offsets(MARKDOWN, chunks)
    paths = [c.meta["headings"] for c in chunks]
    assert paths == [
        ["Guide"],
        ["Guide", "Install"],
        ["Guide", "Install", "Windows"],
        ["Guide", "Usage"],
    ]
    assert chunks[2].text.startswith("### Windows")


def test_markdown_text_before_first_heading():
    text = "Preface line.\n\n# Title\n\nBody."
    chunks = chunk_markdown(text)
    assert chunks[0].text == "Preface line."
    assert chunks[0].meta["headings"] == []
    assert chunks[1].meta["headings"] == ["Title"]


def test_markdown_splits_long_sections():
    body = " ".join(f"Sentence number {i} is here." for i in range(30))
    text = f"# Big\n\n{body}\n"
    chunks = chunk_markdown(text, max_chars=120)
    assert_offsets(text, chunks)
    assert len(chunks) > 1
    assert all(c.meta["headings"] == ["Big"] for c in chunks)
    assert all(len(c.text) <= 120 for c in chunks)


# ---------- evaluation ----------

def test_evaluate_report_numbers():
    chunks = chunk_fixed("abcdefghij", size=5, overlap=0)
    r = evaluate_chunks(chunks)
    assert (r.count, r.mean_len, r.max_len, r.min_len) == (2, 5.0, 5, 5)
    assert r.mid_sentence_breaks == 2


def test_evaluate_empty():
    assert evaluate_chunks([]).to_dict() == {
        "count": 0, "mean_len": 0.0, "max_len": 0, "min_len": 0, "mid_sentence_breaks": 0,
    }


def test_ends_mid_sentence_rules():
    assert ends_mid_sentence("This stops in the mid")
    assert not ends_mid_sentence("This is done.")
    assert not ends_mid_sentence('He said "yes."')
    assert not ends_mid_sentence("## A heading")
    assert not ends_mid_sentence("Items:\n- first item")


def test_fixed_breaks_more_than_sentence():
    fixed = evaluate_chunks(chunk_fixed(PROSE, size=60, overlap=0))
    sent = evaluate_chunks(chunk_sentences(PROSE, max_chars=60))
    assert fixed.mid_sentence_breaks > sent.mid_sentence_breaks


# ---------- CLI ----------

def test_cli_table(tmp_path, capsys):
    f = tmp_path / "guide.md"
    f.write_text(MARKDOWN, encoding="utf-8")
    assert main([str(f), "--size", "80"]) == 0
    out = capsys.readouterr().out
    assert "strategy" in out
    for name in ("fixed", "sentence", "markdown"):
        assert name in out


def test_cli_json(tmp_path, capsys):
    f = tmp_path / "notes.txt"
    f.write_text(PROSE, encoding="utf-8")
    assert main([str(f), "--strategy", "sentence", "--size", "70", "--json"]) == 0
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert rows and all(r["source"] == "notes.txt" for r in rows)
    assert rows[0]["start"] == 0
