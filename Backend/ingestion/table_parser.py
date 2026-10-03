import logging
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_tables(pdf_path):
    """
    ✅ Robust Table Extraction using PyMuPDF (fitz)
    
    Extracts tables without requiring Ghostscript, OpenCV, or external binaries,
    preventing runtime crashes on Render / Linux containers.

    Returns table blocks:
    {
        "type": "table",
        "page": X,
        "caption": "...",
        "table_data": [[rows]],
        "content": "..."
    }
    """
    logger.info("Running table extraction using PyMuPDF...")

    table_blocks = []
    table_counter = 1

    try:
        with fitz.open(pdf_path) as doc:
            for page_index in range(len(doc)):
                page = doc[page_index]
                page_num = page_index + 1

                try:
                    tabs = page.find_tables()
                    for tab in tabs.tables:
                        data = tab.extract()
                        if data and any(any(cell for cell in row) for row in data):
                            table_blocks.append(
                                {
                                    "type": "table",
                                    "page": page_num,
                                    "caption": f"Extracted Table {table_counter} (Page {page_num})",
                                    "table_data": data,
                                    "content": str(data),
                                }
                            )
                            table_counter += 1
                except Exception as page_err:
                    logger.debug("Table detection error on page %d: %s", page_num, page_err)

    except Exception as e:
        logger.warning("PyMuPDF table extraction encountered an issue: %s", e)

    # Optional Camelot fallback if Ghostscript happens to be installed
    if not table_blocks:
        try:
            import camelot
            logger.info("Attempting Camelot fallback...")
            camelot_tables = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
            for i, table in enumerate(camelot_tables):
                data = table.df.values.tolist()
                table_blocks.append(
                    {
                        "type": "table",
                        "page": table.page,
                        "caption": f"Extracted Table {i+1}",
                        "table_data": data,
                        "content": str(data),
                    }
                )
        except Exception:
            logger.debug("Camelot not available or failed; skipping.")

    logger.info("Total extracted tables: %d", len(table_blocks))
    return table_blocks

