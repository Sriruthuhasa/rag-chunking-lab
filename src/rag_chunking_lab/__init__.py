"""Split documents into chunks for retrieval-augmented generation (RAG)."""

from .chunkers import Chunk, chunk_fixed, chunk_markdown, chunk_sentences, split_sentences
from .evaluate import ChunkReport, evaluate_chunks

__all__ = [
    "Chunk",
    "ChunkReport",
    "chunk_fixed",
    "chunk_markdown",
    "chunk_sentences",
    "evaluate_chunks",
    "split_sentences",
]
__version__ = "0.1.0"
