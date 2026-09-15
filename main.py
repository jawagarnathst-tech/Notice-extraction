import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="paddle.*")

from src.ai_extraction_service import AIExtractionService
from src.file_service import is_pdf, validate_input_file
from src.layout_service import LayoutConfig
from src.models import NoticeExtractionResult
from src.ocr_service import DocumentOCRResult, OCRService, PageOCRResult
from src.output_service import OutputService
from src.pdf_service import convert_pdf_to_images


def configure_logging(verbose: bool = False) -> None:
    """Configures application-wide logging format and level."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def load_image_file(image_path: Path) -> List[Tuple[int, np.ndarray]]:
    """
    Loads a single image file as a single-page document.

    Args:
        image_path (Path): Path to the image file.

    Returns:
        List[Tuple[int, np.ndarray]]: List containing [(1, image_rgb_array)].
    """
    try:
        pil_img = Image.open(image_path).convert("RGB")
        img_array = np.array(pil_img)
        return [(1, img_array)]
    except Exception as exc:
        raise RuntimeError(f"Failed to read image '{image_path.name}': {exc}") from exc


def run_pipeline(
    file_path: Path,
    conf_threshold: float = 0.80,
    save_debug: bool = False,
    save_raw_ocr: bool = False,
    lang: str = "en",
    layout_config: Optional[LayoutConfig] = None,
    print_coordinates: bool = False,
    run_ai: bool = True,
    ai_model: str = "gpt-4o-mini",
) -> Tuple[DocumentOCRResult, Optional[NoticeExtractionResult]]:
    """
    Executes Phase 1 (OCR & Layout Reconstruction) and Phase 2 (OpenAI Field Extraction).

    Args:
        file_path (Path): Path to the input PDF or image file.
        conf_threshold (float): Confidence threshold for low-confidence warnings.
        save_debug (bool): Whether to generate debug visual images.
        save_raw_ocr (bool): Whether to save raw OCR JSON (default: False).
        lang (str): PaddleOCR language code.
        layout_config (LayoutConfig): Configuration parameters for spatial reconstruction.
        print_coordinates (bool): Whether to print bounding box metrics to console.
        run_ai (bool): Whether to execute Phase 2 OpenAI field extraction.
        ai_model (str): OpenAI model name.

    Returns:
        Tuple[DocumentOCRResult, Optional[NoticeExtractionResult]]: Complete OCR results and extracted fields.
    """
    validated_path = validate_input_file(file_path)
    base_name = validated_path.stem

    # -------------------------------------------------------------
    # PHASE 1: PaddleOCR Extraction & Visual Layout Reconstruction
    # -------------------------------------------------------------
    if is_pdf(validated_path):
        page_images = convert_pdf_to_images(validated_path)
    else:
        page_images = load_image_file(validated_path)

    if not page_images:
        raise ValueError(f"No pages could be processed from '{validated_path.name}'")

    ocr_service = OCRService(lang=lang, confidence_threshold=conf_threshold)

    pages_results: List[PageOCRResult] = []
    total_lines = 0
    total_conf_sum = 0.0

    for page_num, img_array in page_images:
        page_result = ocr_service.process_image(
            image=img_array,
            page_number=page_num,
            create_debug_image=save_debug,
        )
        pages_results.append(page_result)
        total_lines += page_result.total_lines
        total_conf_sum += sum(line.confidence for line in page_result.lines)

    avg_conf = (total_conf_sum / total_lines) if total_lines > 0 else 0.0

    doc_result = DocumentOCRResult(
        file_name=validated_path.name,
        total_pages=len(pages_results),
        total_lines=total_lines,
        average_confidence=round(avg_conf, 4),
        pages=pages_results,
    )

    # Save Phase 1 outputs (only layout text by default)
    output_service = OutputService(layout_config=layout_config)
    output_service.display_console_summary(doc_result, print_coordinates=print_coordinates)
    saved_paths = output_service.save_all(
        result=doc_result,
        base_name=base_name,
        save_debug=save_debug,
        save_raw_ocr=save_raw_ocr,
    )

    # -------------------------------------------------------------
    # PHASE 2: OpenAI Structured Field Extraction
    # -------------------------------------------------------------
    ai_result: Optional[NoticeExtractionResult] = None

    if run_ai:
        try:
            # Read layout-preserved text
            layout_text_path = saved_paths["layout_text"]
            layout_text = layout_text_path.read_text(encoding="utf-8")

            ai_service = AIExtractionService(model=ai_model)
            ai_result = ai_service.extract_fields(layout_text=layout_text)

            if ai_result:
                output_service.display_extracted_fields(ai_result, base_name=base_name)
                output_service.save_extracted_fields(ai_result, base_name=base_name)
            else:
                logging.error("OpenAI field extraction returned empty or invalid result.")

        except Exception as exc:
            logging.error("Failed to perform OpenAI extraction: %s", exc)
            print(f"\n[WARNING] Phase 2 AI Extraction failed: {exc}\n", file=sys.stderr)

    return doc_result, ai_result


def main() -> None:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="PaddleOCR Document Text Extraction & OpenAI Field Extraction."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the document or image file (PDF, PNG, JPG, JPEG).",
    )
    parser.add_argument(
        "--conf-threshold",
        type=float,
        default=0.80,
        help="Confidence score threshold for low-confidence warnings (default: 0.80).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Generate visual bounding box debug images in output/debug/.",
    )
    parser.add_argument(
        "--save-raw-ocr",
        action="store_true",
        help="Save raw OCR coordinates JSON file (output/<name>_raw_ocr.json).",
    )
    parser.add_argument(
        "--print-coords",
        action="store_true",
        help="Print X, Y, Width, and Height coordinates for each detected OCR line.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="en",
        help="OCR language model (default: 'en').",
    )
    parser.add_argument(
        "--skip-ai",
        action="store_true",
        help="Skip Phase 2 OpenAI field extraction and run OCR only.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="OpenAI model for structured field extraction (default: 'gpt-4o-mini').",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable detailed debug logging.",
    )

    # Layout Tuning Parameters
    layout_group = parser.add_argument_group("Layout Reconstruction Options")
    layout_group.add_argument(
        "--space-ratio",
        type=float,
        default=1.0,
        help="Multiplier for character spacing estimation (default: 1.0).",
    )
    layout_group.add_argument(
        "--line-y-tolerance",
        type=float,
        default=0.5,
        help="Fraction of line height used to group items into the same line (default: 0.5).",
    )
    layout_group.add_argument(
        "--blank-threshold",
        type=float,
        default=1.4,
        help="Multiplier of line height to insert blank lines (default: 1.4).",
    )
    layout_group.add_argument(
        "--char-width",
        type=float,
        default=None,
        help="Explicit character width in pixels (overrides auto-estimation).",
    )

    args = parser.parse_args()
    configure_logging(verbose=args.verbose)

    layout_config = LayoutConfig(
        char_width_px=args.char_width,
        space_pixel_ratio=args.space_ratio,
        line_y_tolerance_ratio=args.line_y_tolerance,
        blank_line_threshold_ratio=args.blank_threshold,
    )

    try:
        run_pipeline(
            file_path=Path(args.file_path),
            conf_threshold=args.conf_threshold,
            save_debug=args.debug,
            save_raw_ocr=args.save_raw_ocr,
            lang=args.lang,
            layout_config=layout_config,
            print_coordinates=args.print_coords or args.verbose,
            run_ai=not args.skip_ai,
            ai_model=args.model,
        )
    except FileNotFoundError as fnf_err:
        print(f"\n[ERROR] File Error: {fnf_err}", file=sys.stderr)
        sys.exit(1)
    except ValueError as val_err:
        print(f"\n[ERROR] Input Error: {val_err}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as rt_err:
        print(f"\n[ERROR] Runtime Error: {rt_err}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Unexpected Error: {exc}", file=sys.stderr)
        logging.exception("Fatal unexpected exception:")
        sys.exit(1)


if __name__ == "__main__":
    main()
