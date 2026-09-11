import logging
from pathlib import Path
from typing import Set

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS: Set[str] = {".pdf", ".png", ".jpg", ".jpeg"}


def validate_input_file(file_path: Path) -> Path:
    """
    Validates that the input file exists and has a supported extension.

    Args:
        file_path (Path): Path to the input file.

    Returns:
        Path: Resolved absolute path to the valid input file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or the path is a directory.
    """
    resolved_path = file_path.resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Input file not found at: {resolved_path}")

    if not resolved_path.is_file():
        raise ValueError(f"Path is not a regular file: {resolved_path}")

    ext = resolved_path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported_str = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported extensions are: {supported_str}"
        )

    logger.debug("Validated input file: %s (type: %s)", resolved_path, ext)
    return resolved_path


def is_pdf(file_path: Path) -> bool:
    """
    Checks if a given file path is a PDF.

    Args:
        file_path (Path): Path to the file.

    Returns:
        bool: True if PDF, False otherwise.
    """
    return file_path.suffix.lower() == ".pdf"
