import fitz
from PIL import Image
import pytesseract
import io


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract embedded text from a PDF document.
    """
    extracted_text = []

    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            extracted_text.append(page.get_text("text"))

    return "\n".join(extracted_text).strip()


def extract_text_from_image(file_bytes: bytes) -> str:
    """
    Extract text from an image using Tesseract OCR.
    """
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")

    return pytesseract.image_to_string(image).strip()


def extract_document_text(
    file_bytes: bytes,
    file_type: str
) -> str:
    """
    Route documents to the appropriate extraction method.
    """
    if file_type == "pdf":
        text = extract_text_from_pdf(file_bytes)

        if text:
            return text

        # The caller can use OCR for scanned PDF pages.
        return ""

    if file_type in {"png", "jpg", "jpeg"}:
        return extract_text_from_image(file_bytes)

    raise ValueError("Unsupported document format.")