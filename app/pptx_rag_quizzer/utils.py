import io
import re


def ExtractText_OCR(img_bytes):
    """
    Extracts text from an image using OCR (Tesseract).

    Args:
        img_bytes (bytes): The image data in bytes.

    Returns:
        str: The extracted text from the image.
    """
    try:
        # Lazy imports to avoid hard dependency at module import time
        import pytesseract
        from PIL import Image

        # Extract text using OCR (Tesseract)
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip()

    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return ""


def clean_text(text):
    """
    Cleans the text by removing any non-essential information.
    - trims whitespace
    - removes empty lines
    - collapses multiple spaces/newlines
    - normalizes quotes
    """
    if not isinstance(text, str):
        return ""

    # Normalize smart quotes to straight quotes for consistency
    normalized = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201C", '"')
        .replace("\u201D", '"')
    )

    # Strip trailing/leading whitespace per line and drop empties
    lines = [line.strip() for line in normalized.splitlines()]
    lines = [line for line in lines if line]

    # Collapse excessive internal whitespace to single spaces per line
    cleaned_lines = [re.sub(r"\s+", " ", line) for line in lines]

    # Join with single newlines
    cleaned = "\n".join(cleaned_lines).strip()

    return cleaned


def clean_text_with_llm(text, model=None):
    """
    Cleans the text by removing any non-essential information using LLM (Gemini-2.0-flash-lite).
    If a model is not provided, attempts to initialize one.
    """
    # Lazy import to avoid top-level dependency
    try:
        from google.generativeai.types import GenerationConfig
        import google.generativeai as genai
    except Exception as e:
        print(f"LLM dependencies not available: {e}")
        return clean_text(text)

    if model is None:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
        except Exception as e:
            print(f"Failed to initialize LLM model: {e}")
            return clean_text(text)

    generation_config = GenerationConfig(max_output_tokens=100)

    result = model.generate_content(
        contents=[
            text,
            "\n",
            "given the following text, remove any non-essential information and return the text in a clean format. "
            "Only return the text in a clean format. Nothing else!",
        ],
        generation_config=generation_config,
    )
    return result.text.strip()


def format_context_entries(documents, metadatas=None, heading=None):
    """
    Formats a list of retrieved documents (and optional metadatas) into a readable context string.

    Args:
        documents (list[str]): The retrieved document snippets.
        metadatas (list[dict] | None): Optional metadata per document.
        heading (str | None): Optional heading to prepend.

    Returns:
        str: A clean, human-readable context block.
    """
    if not documents:
        return ""

    formatted_rows = []
    for idx, doc in enumerate(documents):
        slide_info = ""
        if metadatas and idx < len(metadatas):
            slide_num = metadatas[idx].get("slide_number")
            if slide_num is not None and slide_num != "":
                slide_info = f"[Slide {slide_num}] "
        formatted_rows.append(f"- {slide_info}{clean_text(doc)}")

    body = "\n".join(formatted_rows)
    if heading:
        return f"{heading}\n{body}"
    return body
