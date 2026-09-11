import io
import logging
from pathlib import Path
from typing import List, Tuple
import pymupdf as fitz
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def convert_pdf_to_images(
    pdf_path: Path, dpi: int = 200
) -> List[Tuple[int, np.ndarray]]:
    """
    Converts each page of a PDF document into an image (numpy array in RGB format).

    Args:
        pdf_path (Path): Path to the PDF file.
        dpi (int): DPI resolution for rendering pages (default: 200).

    Returns:
        List[Tuple[int, np.ndarray]]: List of tuples where each element is
        (page_number, image_numpy_array), with 1-based page numbering.

    Raises:
        ValueError: If PDF contains no pages or is password protected without access.
        RuntimeError: If PDF rendering fails.
    """
    logger.info("Converting PDF to images: %s (DPI: %d)", pdf_path.name, dpi)

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise RuntimeError(f"Failed to open PDF '{pdf_path.name}': {exc}") from exc

    try:
        if doc.is_encrypted:
            raise ValueError(f"PDF file is password-protected/encrypted: {pdf_path.name}")

        total_pages = len(doc)
        if total_pages == 0:
            raise ValueError(f"PDF contains 0 pages: {pdf_path.name}")

        logger.info("Found %d page(s) in %s", total_pages, pdf_path.name)

        # 72 DPI is base resolution in PDF
        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)

        pages_images: List[Tuple[int, np.ndarray]] = []

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            # Convert pixmap to PIL Image then RGB numpy array
            img_bytes = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img_array = np.array(pil_image)

            pages_images.append((page_num, img_array))
            logger.debug("Rendered page %d/%d (%dx%d)", page_num, total_pages, pix.width, pix.height)

        return pages_images

    finally:
        doc.close()
