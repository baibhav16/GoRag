import os
import re
import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_figures(pdf_path: str, doc_id: str):
    """
    ✅ Extract embedded images (figures) from PDF using PyMuPDF

    Saves figures into:

        extracted/figures/<doc_id>__figure1_page3.png

    doc_id is embedded in the filename so figures from different documents
    can never collide/overwrite each other on disk.

    Returns blocks like:

    {
        type: "image",
        page: 3,
        caption: "Figure 1 extracted from page 3",
        file_path: "...",
        figure_index: 1
    }
    """

    os.makedirs("extracted/figures", exist_ok=True)

    # ✅ Re-sanitize defensively even though app.py already sanitizes doc_id,
    # so this function stays safe if ever called from elsewhere.
    safe_doc_id = re.sub(r"[^A-Za-z0-9._-]", "_", doc_id or "doc")

    figure_blocks = []
    fig_counter = 1

    logger.info("Extracting figures using PyMuPDF for %s...", doc_id)

    with fitz.open(pdf_path) as doc:
        for page_index in range(len(doc)):
            page = doc[page_index]

            images = page.get_images(full=True)

            if len(images) > 0:
                logger.info("Page %d: found %d images", page_index + 1, len(images))

            for img in images:
                xref = img[0]

                base_img = doc.extract_image(xref)
                img_bytes = base_img["image"]
                img_ext = base_img["ext"]

                page_num = page_index + 1

                img_path = (
                    f"extracted/figures/{safe_doc_id}__figure{fig_counter}_page{page_num}.{img_ext}"
                )

                with open(img_path, "wb") as f:
                    f.write(img_bytes)

                figure_blocks.append(
                    {
                        "type": "image",
                        "page": page_num,
                        "file_path": img_path,
                        "caption": f"Figure {fig_counter} extracted from page {page_num}",
                        "figure_index": fig_counter,
                    }
                )

                fig_counter += 1

    logger.info("Total extracted figures: %d", len(figure_blocks))

    return figure_blocks
