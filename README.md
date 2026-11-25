# rag-chunking-lab

A small Python library and CLI that splits documents into chunks for RAG
(retrieval-augmented generation) and tells you how good those chunks are.

Pure Python standard library. No network, no API keys, no dependencies.

## What it does

Three chunking strategies:

| Strategy   | Function           | How it splits                                                        |
|------------|--------------------|----------------------------------------------------------------------|
| `fixed`    | `chunk_fixed`      | Fixed-size character windows with overlap                            |
| `sentence` | `chunk_sentences`  | Packs whole sentences up to a max size; never cuts a sentence        |
| `markdown` | `chunk_markdown`   | Splits on `#` headings, keeps the heading path, splits long sections |

Every chunk keeps metadata: `source`, `index`, `start` / `end` character offsets
(`text[start:end] == chunk.text` always holds), `strategy`, and `meta`
(for markdown: `meta["headings"]`, e.g. `["Guide", "Install", "Windows"]`).

A small evaluation helper, `evaluate_chunks`, reports chunk count, mean / max / min
length and how many chunks break in the middle of a sentence.

## Install

```bash
git clone https://github.com/Sriruthuhasa/rag-chunking-lab.git
cd rag-chunking-lab
pip install -e ".[dev]"
```

Python 3.9 or newer.

## Usage

```python
from rag_chunking_lab import chunk_fixed, chunk_sentences, chunk_markdown, evaluate_chunks

text = open("examples/sample.md", encoding="utf-8").read()

chunks = chunk_markdown(text, max_chars=200, source="sample.md")
for c in chunks:
    print(c.index, c.start, c.end, c.meta["headings"])

print(evaluate_chunks(chunk_fixed(text, size=120, overlap=20)))
# ChunkReport(count=5, mean_len=110.2, max_len=120, min_len=71, mid_sentence_breaks=4)
print(evaluate_chunks(chunk_sentences(text, max_chars=120)))
# ChunkReport(count=6, mean_len=77.3, max_len=90, min_len=61, mid_sentence_breaks=0)
```

## CLI

Compare all three strategies on one file:

```bash
rag-chunk examples/sample.md --size 120 --overlap 20
```

```text
strategy   chunks    mean   max   min  mid-sentence
fixed           5   110.2   120    71             4
sentence        6    77.3    90    61             0
markdown        6    77.2   111    35             0
```

Print the chunks themselves as JSON lines (ready to load into a vector store):

```bash
rag-chunk examples/sample.md --strategy markdown --size 200 --json
```

```json
{"text": "## Fixed size\n\nFixed windows are fast and simple. ...", "source": "sample.md", "index": 1, "start": 128, "end": 239, "strategy": "markdown", "meta": {"headings": ["RAG notes", "Fixed size"]}}
```

Options: `--strategy fixed|sentence|markdown|all`, `--size N` (max chars, default 500),
`--overlap N` (fixed only, default 50), `--json`. Use `-` as the file to read stdin.
Without installing, run `python -m rag_chunking_lab` from the `src` folder or with `PYTHONPATH=src`.

## Run tests

```bash
pip install pytest
python -m pytest -q
```

## Notes

- Sentence splitting is rule based (`.`, `!`, `?` followed by whitespace), so abbreviations
  like "e.g." can end a sentence early. That keeps it fast and dependency free.
- The mid-sentence check treats headings, list items, code fences and table rows as clean
  endings, since they are not prose.

## License

MIT. See [LICENSE](LICENSE).
