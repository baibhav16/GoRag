def chunk_text(text: str, chunk_size=500):
    """
    Breaks long text into smaller pieces.

    Why chunking is required:
    - Embeddings work best on smaller text
    - Retrieval becomes accurate
    - LLM context window is limited
    """

    chunks = []
    current = ""

    for sentence in text.split("."):

        if len(current) + len(sentence) < chunk_size:
            current += sentence + "."
        else:
            chunks.append(current)
            current = sentence + "."

    if current:
        chunks.append(current)

    return chunks
