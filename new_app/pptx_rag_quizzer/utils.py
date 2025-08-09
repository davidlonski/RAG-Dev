import streamlit as st
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import pytesseract
from PIL import Image
import io


def ExtractText_OCR(img_bytes):
    """
    Extracts text from an image using OCR (Tesseract).

    Args:
        img_bytes (bytes): The image data in bytes.

    Returns:
        str: The extracted text from the image.
    """
    try:
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
    """
    return "\n".join(line for line in text.splitlines() if line.strip())


def clean_text_with_llm(text, model):
    """
    Cleans the text by removing any non-essential information using LLM (Gemini-2.0-flash-lite).
    """
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
