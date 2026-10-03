import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def parse_pdf(pdf_path):
    """
    ✅ Production PDF Parser
    Extracts clean page-wise text chunks.

    Output format:
    [
        {
            "type": "text",
            "page": 1,
            "content": "...chunk..."
        }
    ]
    """

    blocks = []

    with fitz.open(pdf_path) as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]

            text = page.get_text("text").strip()

            if text:
                chunks = text.split("\n\n")

                for chunk in chunks:
                    if len(chunk.strip()) > 50:
                        blocks.append(
                            {
                                "type": "text",
                                "page": page_num + 1,
                                "content": chunk.strip()
                            }
                        )

    logger.info("Extracted %d text chunks", len(blocks))
    return blocks
