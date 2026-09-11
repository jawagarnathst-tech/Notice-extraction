"""
Utility script to generate sample test files (sample.png and sample.pdf)
in the input/ folder for immediate testing.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_sample_image(output_path: Path) -> None:
    """Generates a sample insurance notice image."""
    img = Image.new("RGB", (900, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Use default font
    font = ImageFont.load_default()

    # Draw border
    draw.rectangle([(20, 20), (880, 580)], outline=(200, 200, 200), width=2)

    # Sample text content matching the scenario
    lines = [
        ("ABC Insurance Company", (50, 50)),
        ("Commercial Policy Notification", (50, 80)),
        ("--------------------------------------------------", (50, 110)),
        ("Policy Number: WC123456", (50, 150)),
        ("Insured Name: Acme Logistics Corp.", (50, 190)),
        ("Effective Date: 01/01/2026", (50, 230)),
        ("Expiration Date: 01/01/2027", (50, 270)),
        ("Total Premium: $12,450.00", (50, 310)),
        ("Notice Status: ACTIVE", (50, 350)),
        ("--------------------------------------------------", (50, 390)),
        ("For questions, please contact agent at (800) 555-0199.", (50, 430)),
    ]

    for text, (x, y) in lines:
        draw.text((x, y), text, fill=(0, 0, 0), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Created sample image: {output_path}")


def create_sample_pdf(image_path: Path, pdf_path: Path) -> None:
    """Creates a sample PDF from the sample image."""
    img = Image.open(image_path)
    img.save(pdf_path, "PDF", resolution=150.0)
    print(f"Created sample PDF: {pdf_path}")


if __name__ == "__main__":
    input_dir = Path("input")
    input_dir.mkdir(parents=True, exist_ok=True)

    sample_png = input_dir / "sample.png"
    sample_pdf = input_dir / "sample.pdf"

    create_sample_image(sample_png)
    create_sample_pdf(sample_png, sample_pdf)
