from dataclasses import dataclass, field
import logging
from typing import Any, List, Optional
import cv2
import numpy as np
from paddleocr import PaddleOCR

# Suppress verbose internal PaddleOCR output
logging.getLogger("ppocr").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)


@dataclass
class LineOCRResult:
    """Represents a single detected line of text."""
    text: str
    confidence: float
    bounding_box: List[List[float]]
    is_low_confidence: bool = False

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "confidence": round(self.confidence, 4),
            "boundingBox": self.bounding_box,
            "lowConfidence": self.is_low_confidence,
        }


@dataclass
class PageOCRResult:
    """Represents OCR results for a single page."""
    page_number: int
    lines: List[LineOCRResult] = field(default_factory=list)
    raw_image: Optional[np.ndarray] = None
    debug_image: Optional[np.ndarray] = None

    @property
    def total_lines(self) -> int:
        return len(self.lines)

    @property
    def average_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(line.confidence for line in self.lines) / len(self.lines)

    def to_dict(self) -> dict:
        return {
            "pageNumber": self.page_number,
            "totalLines": self.total_lines,
            "averageConfidence": round(self.average_confidence, 4),
            "lines": [line.to_dict() for line in self.lines],
        }


@dataclass
class DocumentOCRResult:
    """Represents full OCR results for a document."""
    file_name: str
    total_pages: int
    total_lines: int
    average_confidence: float
    pages: List[PageOCRResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "fileName": self.file_name,
            "totalPages": self.total_pages,
            "totalLines": self.total_lines,
            "averageConfidence": round(self.average_confidence, 4),
            "pages": [
                {
                    "pageNumber": page.page_number,
                    "lines": [
                        {
                            "text": line.text,
                            "confidence": round(line.confidence, 4),
                            "boundingBox": line.bounding_box,
                        }
                        for line in page.lines
                    ],
                }
                for page in self.pages
            ],
        }


class OCRService:
    """Service wrapping PaddleOCR engine initialization and inference."""

    def __init__(
        self,
        lang: str = "en",
        use_angle_cls: bool = True,
        confidence_threshold: float = 0.80,
    ) -> None:
        """
        Initialize the PaddleOCR engine for CPU inference.

        Args:
            lang (str): OCR language model (default 'en').
            use_angle_cls (bool): Enable text orientation classification.
            confidence_threshold (float): Score below which lines are flagged.
        """
        self.confidence_threshold = confidence_threshold
        logger.info(
            "Initializing PaddleOCR (lang='%s', angle_cls=%s, CPU mode)...",
            lang,
            use_angle_cls,
        )

        try:
            # Initialize PaddleOCR engine
            self.ocr = PaddleOCR(
                use_angle_cls=use_angle_cls,
                lang=lang,
                use_gpu=False,
            )
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception as exc:
            logger.error("Failed to initialize PaddleOCR engine: %s", exc)
            raise RuntimeError(
                f"Failed to initialize PaddleOCR: {exc}. Please verify PaddlePaddle installation."
            ) from exc

    def process_image(
        self,
        image: np.ndarray,
        page_number: int = 1,
        create_debug_image: bool = True,
    ) -> PageOCRResult:
        """
        Runs OCR on a single image array and returns structured page results.

        Args:
            image (np.ndarray): Image in RGB format.
            page_number (int): The 1-based page number.
            create_debug_image (bool): Whether to render bounding box annotations.

        Returns:
            PageOCRResult: The parsed OCR results for this page.
        """
        logger.info("Processing OCR for page %d...", page_number)

        try:
            # PaddleOCR accepts numpy arrays directly (RGB/BGR)
            raw_ocr_result = self.ocr.ocr(image, cls=True)
        except Exception as exc:
            logger.error("Error during OCR inference on page %d: %s", page_number, exc)
            raise RuntimeError(f"OCR inference failed on page {page_number}: {exc}") from exc

        parsed_lines: List[LineOCRResult] = []

        # PaddleOCR returns a list of results (one per image input)
        # E.g. raw_ocr_result = [ [ [box, (text, conf)], [box, (text, conf)] ] ]
        # If no text is detected, it may return [None] or [] or None
        if raw_ocr_result and len(raw_ocr_result) > 0 and raw_ocr_result[0] is not None:
            for item in raw_ocr_result[0]:
                try:
                    box_points = item[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    text, conf = item[1]  # (text_str, confidence_float)

                    # Ensure box points are standard float numbers
                    cleaned_box = [[float(coord) for coord in pt] for pt in box_points]
                    confidence_float = float(conf)
                    is_low = confidence_float < self.confidence_threshold

                    parsed_lines.append(
                        LineOCRResult(
                            text=str(text),
                            confidence=confidence_float,
                            bounding_box=cleaned_box,
                            is_low_confidence=is_low,
                        )
                    )
                except (IndexError, ValueError, TypeError) as parse_err:
                    logger.warning("Skipping malformed OCR item on page %d: %s (Error: %s)", page_number, item, parse_err)

        logger.info(
            "Page %d completed: detected %d line(s).",
            page_number,
            len(parsed_lines),
        )

        debug_img = None
        if create_debug_image:
            debug_img = self._render_debug_overlay(image, parsed_lines)

        return PageOCRResult(
            page_number=page_number,
            lines=parsed_lines,
            raw_image=image,
            debug_image=debug_img,
        )

    def _render_debug_overlay(
        self,
        image: np.ndarray,
        lines: List[LineOCRResult],
    ) -> np.ndarray:
        """
        Draws visual bounding boxes and confidence flags on an image copy.

        Args:
            image (np.ndarray): Original image (RGB).
            lines (List[LineOCRResult]): Detected lines with coordinates.

        Returns:
            np.ndarray: Annotated image (RGB).
        """
        # Create a deep copy to annotate
        annotated = image.copy()

        for idx, line in enumerate(lines, start=1):
            pts = np.array(line.bounding_box, dtype=np.int32).reshape((-1, 1, 2))

            # Color: Green for normal confidence, Red/Amber for low confidence
            # RGB format: Green is (46, 204, 113), Red is (231, 76, 60)
            box_color = (231, 76, 60) if line.is_low_confidence else (46, 204, 113)

            # Draw polygon bounding box
            cv2.polylines(annotated, [pts], isClosed=True, color=box_color, thickness=2)

            # Draw small index badge near top-left point
            top_left = line.bounding_box[0]
            badge_x = int(top_left[0])
            badge_y = max(int(top_left[1]) - 4, 12)

            label_text = f"#{idx} ({line.confidence:.2f})"
            cv2.putText(
                annotated,
                label_text,
                (badge_x, badge_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                box_color,
                1,
                cv2.LINE_AA,
            )

        return annotated
