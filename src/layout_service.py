from dataclasses import dataclass
import logging
import statistics
from typing import List, Tuple
from src.ocr_service import LineOCRResult, PageOCRResult

logger = logging.getLogger(__name__)


@dataclass
class LayoutConfig:
    """
    Configuration parameters for spatial coordinate-to-text layout reconstruction.
    """
    # Multiplier for character width calculation (pixels per monospace character)
    # If None, automatically estimated from document median char width.
    char_width_px: float = None

    # Ratio used when auto-estimating char width (char_width = median_char_width * space_pixel_ratio)
    space_pixel_ratio: float = 1.0

    # Fraction of line height threshold to group items into the same horizontal line
    line_y_tolerance_ratio: float = 0.5

    # Multiplier for vertical distance to insert blank lines
    blank_line_threshold_ratio: float = 1.4

    # Minimum number of spaces between distinct horizontal text blocks
    min_horizontal_spaces: int = 1


@dataclass
class BoundingBoxMetrics:
    """Calculated metric coordinates for an OCR line item."""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    width: float
    height: float
    center_y: float
    text: str
    confidence: float
    char_width: float
    raw_item: LineOCRResult


def extract_box_metrics(line_item: LineOCRResult) -> BoundingBoxMetrics:
    """Calculates axis-aligned min/max/center metrics from 4-point bounding box."""
    xs = [pt[0] for pt in line_item.bounding_box]
    ys = [pt[1] for pt in line_item.bounding_box]

    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    width = max(1.0, x_max - x_min)
    height = max(1.0, y_max - y_min)
    center_y = (y_min + y_max) / 2.0

    text_len = max(1, len(line_item.text))
    char_w = width / text_len

    return BoundingBoxMetrics(
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
        width=width,
        height=height,
        center_y=center_y,
        text=line_item.text,
        confidence=line_item.confidence,
        char_width=char_w,
        raw_item=line_item,
    )


class LayoutService:
    """
    Reconstructs original visual text layout (spacing, columns, blank lines,
    indentation) from OCR bounding-box coordinates.
    """

    def __init__(self, config: LayoutConfig = None) -> None:
        self.config = config or LayoutConfig()

    def reconstruct_page_layout(self, page: PageOCRResult) -> str:
        """
        Reconstructs visual 2D text layout for a single page.

        Args:
            page (PageOCRResult): Page containing OCR line detections.

        Returns:
            str: Layout-preserved text content for the page.
        """
        if not page.lines:
            return ""

        # 1. Extract geometric metrics for every detected box
        metrics_list = [extract_box_metrics(line) for line in page.lines]

        # Log coordinate details for debugging
        for m in metrics_list:
            logger.debug(
                "Text: %-30s | X: %6.1f | Y: %6.1f | Width: %6.1f | Height: %5.1f | Conf: %.2f",
                m.text[:30], m.x_min, m.y_min, m.width, m.height, m.confidence
            )

        # 2. Determine base document scale metrics
        char_widths = [m.char_width for m in metrics_list if m.char_width > 0]
        heights = [m.height for m in metrics_list if m.height > 0]

        median_char_w = statistics.median(char_widths) if char_widths else 10.0
        median_line_h = statistics.median(heights) if heights else 20.0

        char_w_unit = (
            self.config.char_width_px
            if self.config.char_width_px is not None
            else (median_char_w * self.config.space_pixel_ratio)
        )
        char_w_unit = max(1.0, char_w_unit)

        # Page horizontal minimum margin
        page_x_min = min(m.x_min for m in metrics_list)

        # 3. Group bounding boxes into horizontal lines
        # Sort primarily by vertical coordinate
        sorted_by_y = sorted(metrics_list, key=lambda item: (item.y_min, item.x_min))

        grouped_lines: List[List[BoundingBoxMetrics]] = []
        y_tolerance = median_line_h * self.config.line_y_tolerance_ratio

        for item in sorted_by_y:
            assigned = False
            for group in grouped_lines:
                # Calculate vertical overlap with the group
                group_y_min = min(b.y_min for b in group)
                group_y_max = max(b.y_max for b in group)
                group_h = group_y_max - group_y_min

                overlap_min = max(item.y_min, group_y_min)
                overlap_max = min(item.y_max, group_y_max)
                overlap = max(0.0, overlap_max - overlap_min)

                # Boxes belong to the same line if they overlap significantly (> 45% of height)
                # and vertical center distance is within tolerance
                min_h = min(item.height, group_h)
                group_center_y = (group_y_min + group_y_max) / 2.0
                center_dist = abs(item.center_y - group_center_y)

                if (overlap / min_h >= 0.40) and (center_dist <= min_h * 0.6):
                    group.append(item)
                    assigned = True
                    break

            if not assigned:
                grouped_lines.append([item])

        # 4. Sort lines vertically (top to bottom)
        def line_vertical_key(line_boxes: List[BoundingBoxMetrics]) -> float:
            return min(b.y_min for b in line_boxes)

        grouped_lines.sort(key=line_vertical_key)

        # 5. Build output text lines preserving horizontal spacing & blank lines
        output_lines: List[str] = []
        prev_line_y_max: float = None

        for line_boxes in grouped_lines:
            # Sort boxes within line horizontally (left to right)
            line_boxes.sort(key=lambda b: b.x_min)

            current_line_y_min = min(b.y_min for b in line_boxes)
            current_line_y_max = max(b.y_max for b in line_boxes)

            # Insert blank lines if vertical gap exceeds threshold
            if prev_line_y_max is not None:
                vertical_gap = current_line_y_min - prev_line_y_max
                blank_threshold = median_line_h * self.config.blank_line_threshold_ratio
                if vertical_gap > blank_threshold:
                    num_blank_lines = max(1, int(round(vertical_gap / median_line_h)) - 1)
                    # Cap unreasonable blank line bursts to 5
                    num_blank_lines = min(5, num_blank_lines)
                    for _ in range(num_blank_lines):
                        output_lines.append("")

            # Assemble line text placing words at precise character columns
            line_buffer: List[str] = []
            current_col = 0

            for box in line_boxes:
                target_col = int(round((box.x_min - page_x_min) / char_w_unit))

                # Ensure at least min spaces if box is after previous text
                if current_col > 0:
                    target_col = max(target_col, current_col + self.config.min_horizontal_spaces)

                leading_spaces = max(0, target_col - current_col)
                if leading_spaces > 0:
                    line_buffer.append(" " * leading_spaces)
                    current_col += leading_spaces

                line_buffer.append(box.text)
                current_col += len(box.text)

            line_str = "".join(line_buffer).rstrip()
            output_lines.append(line_str)
            prev_line_y_max = current_line_y_max

        return "\n".join(output_lines)

    def reconstruct_document_layout(self, pages: List[PageOCRResult]) -> str:
        """
        Reconstructs full document layout separated by page headers.

        Args:
            pages (List[PageOCRResult]): List of page OCR results.

        Returns:
            str: Full reconstructed document layout string.
        """
        sections: List[str] = []
        for page in pages:
            header = f"==================== PAGE {page.page_number} ===================="
            page_content = self.reconstruct_page_layout(page)
            sections.append(f"{header}\n\n{page_content}".rstrip())

        return "\n\n".join(sections) + "\n"
