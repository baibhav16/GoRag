import re
from qdrant_client.models import Filter, FieldCondition, MatchValue, MatchAny

from ingestion.embedder import embed_text
from storage.qdrant_client import client, COLLECTION_NAME


def retrieve(query: str, doc_id: str, top_k: int = 8):
    """
    ✅ Production Multimodal Retrieval

    Retrieves:
    ✅ Text chunks
    ✅ Table blocks
    ✅ Figures (real extracted images)

    Supports:
    ✅ Page-specific queries ("Explain page 5")
    ✅ Auto-return tables and visuals

    Returns:
        context_text (str)
        visuals (list)
        citations (list[int])
    """

    # -------------------------------
    # ✅ Step 0: Detect page query
    # -------------------------------
    match = re.search(r"page\s+(\d+)", query.lower())
    page_number = int(match.group(1)) if match else None

    # -------------------------------
    # ✅ Step 1: Embed query
    # -------------------------------
    query_vector = embed_text(query)

    # -------------------------------
    # ✅ Step 2: Build Filter
    # -------------------------------
    must_conditions = [
        FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
        # ✅ Images use CLIP vectors, incompatible with the MiniLM query vector
        # used here — exclude them so they don't waste top_k slots on a
        # meaningless cross-space similarity score. Images are fetched
        # separately below via scroll() on the relevant pages.
        FieldCondition(key="type", match=MatchAny(any=["text", "table"])),
    ]

    if page_number:
        must_conditions.append(
            FieldCondition(key="page", match=MatchValue(value=page_number))
        )

    query_filter = Filter(must=must_conditions)

    # -------------------------------
    # ✅ Step 3: Query Qdrant
    # -------------------------------
    results = client.query_points(
        collection_name=COLLECTION_NAME,   # ✅ FIXED COLLECTION
        query=query_vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True
    ).points

    context_chunks = []
    visuals = []
    citations = set()
    relevant_pages = set()

    # -------------------------------
    # ✅ Step 4: Build Context + Tables
    # -------------------------------
    for r in results:
        payload = r.payload
        page = payload.get("page", -1)
        block_type = payload.get("type")

        citations.add(page)
        relevant_pages.add(page)

        # ✅ TEXT
        if block_type == "text":
            context_chunks.append(payload.get("content", ""))

        # ✅ TABLE
        elif block_type == "table":
            table_data = payload.get("table_data", [])

            context_chunks.append(
                f"\nTABLE (Page {page}):\n{table_data}\n"
            )

            visuals.append({
                "id": str(r.id),
                "type": "table",
                "caption": payload.get("caption", "Extracted Table"),
                "page": page,
                "tableData": table_data,
            })

    # -------------------------------
    # ✅ Step 5: Fetch Figures from Same Pages
    # -------------------------------
    for page in relevant_pages:

        image_filter = Filter(
            must=[
                FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                FieldCondition(key="page", match=MatchValue(value=page)),
                FieldCondition(key="type", match=MatchValue(value="image")),
            ]
        )

        image_results, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=image_filter,
            limit=2,
            with_payload=True
        )

        for img in image_results:
            img_payload = img.payload
            file_path = img_payload.get("file_path")

            if not file_path:
                continue

            visuals.append({
                "id": str(img.id),
                "type": "image",
                "src": f"/extracted/{file_path.replace('extracted/', '')}",
                "caption": img_payload.get("caption", "Extracted Figure"),
                "page": page,
            })

    # -------------------------------
    # ✅ Final Output
    # -------------------------------
    context_text = "\n\n".join(context_chunks)

    return context_text, visuals, sorted(list(citations))
