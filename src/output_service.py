import json
import logging
from pathlib import Path
from typing import Optional
from PIL import Image

from src.layout_service import LayoutConfig, LayoutService, extract_box_metrics
from src.models import NoticeExtractionResult
from src.ocr_service import DocumentOCRResult, PageOCRResult

logger = logging.getLogger(__name__)


class OutputService:
    """Service responsible for console formatting and persistence of layout, OCR, and AI outputs."""

    def __init__(self, output_dir: Path = Path("output"), layout_config: LayoutConfig = None) -> None:
        """
        Initialize output directory and layout reconstruction engine.

        Args:
            output_dir (Path): Base output directory.
            layout_config (LayoutConfig): Configuration parameters for spatial reconstruction.
        """
        self.output_dir = output_dir
        self.debug_dir = output_dir / "debug"
        self.layout_service = LayoutService(config=layout_config)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Creates output and debug directories if they do not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def display_console_summary(self, result: DocumentOCRResult, print_coordinates: bool = False) -> None:
        """
        Prints formatted OCR results to standard output.

        Args:
            result (DocumentOCRResult): Complete OCR results for the document.
            print_coordinates (bool): If True, prints X, Y, Width, and Confidence for each box.
        """
        print(f"\nProcessing file: {result.file_name}\n")

        print(f"Total Pages: {result.total_pages}")
        print(f"Total Text Lines Detected: {result.total_lines}")
        print(f"Average OCR Confidence: {result.average_confidence:.4f}\n")
        print("OCR extraction completed successfully.\n")

    def display_extracted_fields(self, fields: NoticeExtractionResult, base_name: str) -> None:
        """
        Displays OpenAI extracted business fields in the console.

        Args:
            fields (NoticeExtractionResult): Validated extraction result.
            base_name (str): Document base name.
        """
        print("Extracting required fields using OpenAI...\n")
        print(f"Account       : {fields.account}")
        print(f"Country       : {fields.country}")
        print(f"Agency        : {fields.agency}")
        print(f"Agency Type   : {fields.agency_type}")
        print(f"Department    : {fields.department}")
        print(f"Classification: {fields.classification}")
        print(f"Notice Type   : {fields.notice_type}\n")
        print("Structured extraction completed successfully.\n")
        print(f"Saved:\noutput/{base_name}_extracted_fields.json\n")

    def save_layout_text(self, result: DocumentOCRResult, base_name: str) -> Path:
        """
        Saves layout-preserved text file where columns, spaces, and blank lines
        are reconstructed from OCR bounding-box coordinates.

        Output file: output/<base_name>_layout.txt
        """
        out_path = self.output_dir / f"{base_name}_layout.txt"
        logger.info("Saving layout-preserved text to: %s", out_path)

        layout_content = self.layout_service.reconstruct_document_layout(result.pages)
        out_path.write_text(layout_content, encoding="utf-8")
        return out_path

    def save_json(self, result: DocumentOCRResult, base_name: str) -> Path:
        """
        Saves detailed raw OCR output including bounding boxes and confidence scores to JSON.

        Output file: output/<base_name>_raw_ocr.json
        """
        out_path = self.output_dir / f"{base_name}_raw_ocr.json"
        logger.info("Saving raw OCR JSON output to: %s", out_path)

        json_data = result.to_dict()
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        return out_path

    def save_extracted_fields(self, fields: NoticeExtractionResult, base_name: str) -> Path:
        """
        Saves the OpenAI structured fields to JSON.

        Output file: output/<base_name>_extracted_fields.json
        """
        out_path = self.output_dir / f"{base_name}_extracted_fields.json"
        logger.info("Saving AI extracted fields to: %s", out_path)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(fields.to_strict_dict(), f, indent=2, ensure_ascii=False)

        return out_path

    def save_debug_images(self, page: PageOCRResult, base_name: str) -> None:
        """Saves raw page image and OCR bounding box debug image."""
        if page.raw_image is not None:
            raw_path = self.debug_dir / f"{base_name}_page_{page.page_number}.png"
            Image.fromarray(page.raw_image).save(raw_path)
            logger.debug("Saved raw debug image: %s", raw_path)

        if page.debug_image is not None:
            annotated_path = self.debug_dir / f"{base_name}_page_{page.page_number}_ocr.png"
            Image.fromarray(page.debug_image).save(annotated_path)
            logger.debug("Saved annotated debug image: %s", annotated_path)

    def save_all(
        self,
        result: DocumentOCRResult,
        base_name: str,
        save_debug: bool = False,
        save_raw_ocr: bool = False,
    ) -> dict:
        """
        Saves outputs: layout text, optional raw JSON, and optional debug images.

        Args:
            result (DocumentOCRResult): The complete OCR results.
            base_name (str): Base filename.
            save_debug (bool): Whether to save debug visual images.
            save_raw_ocr (bool): Whether to save raw OCR JSON (default False).

        Returns:
            dict: Dictionary with paths to created files.
        """
        layout_path = self.save_layout_text(result, base_name)
        raw_json_path = None

        if save_raw_ocr:
            raw_json_path = self.save_json(result, base_name)

        if save_debug:
            for page in result.pages:
                self.save_debug_images(page, base_name)

        return {
            "layout_text": layout_path,
            "raw_json": raw_json_path,
            "debug_dir": self.debug_dir if save_debug else None,
        }
