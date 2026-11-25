# RAG notes

Chunking decides what the retriever can find. Bad chunks split ideas in half. Good chunks keep one idea together.

## Fixed size

Fixed windows are fast and simple. They often cut a sentence in the middle, which hurts answers.

## Sentence aware

Sentence packing keeps whole sentences. Chunk sizes vary a little more.

## Heading aware

Heading splits follow the document structure. Each chunk knows its section path, which is useful metadata for citations.
