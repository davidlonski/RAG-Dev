import streamlit as st
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import pytesseract
from PIL import Image
import io
import time
import base64
import openpyxl
from openpyxl.styles import Font, Alignment
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PILImage
from pptx_rag_quizzer.quiz_master import QuizMaster

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


def build_excel_quiz_spreadsheet(rag_controller):
    """
    Builds a spreadsheet of the quiz images, questions, and answers.
    Returns an in-memory Excel file (bytes).
    """
    quiz_master = QuizMaster(rag_controller=rag_controller)

    all_quiz_questions = []

    # Generate 3 random image quiz questions
    for _ in range(3):
        try:
            question = quiz_master.generate_image_question()
            if question:  # Only add if not None
                all_quiz_questions.append(question)
                time.sleep(2)  # Add delay between API calls
        except Exception as e:
            st.error(f"Error generating image question: {e}")
            # Add a placeholder question
            all_quiz_questions.append(
                {
                    "question": "Error generating question",
                    "answer": "Error generating answer",
                    "context": "Error generating context",
                    "type": "image",
                    "image_bytes": None,
                }
            )

    # Generate 3 random text quiz questions
    for _ in range(3):
        try:
            question = quiz_master.generate_text_question()
            if question:  # Only add if not None
                all_quiz_questions.append(question)
                time.sleep(2)  # Add delay between API calls
        except Exception as e:
            st.error(f"Error generating text question: {e}")
            # Add a placeholder question
            all_quiz_questions.append(
                {
                    "question": "Error generating question",
                    "answer": "Error generating answer",
                    "context": "Error generating context",
                    "type": "text",
                }
            )

    # If no questions were generated, create a basic one
    if not all_quiz_questions:
        all_quiz_questions.append(
            {
                "question": "No questions could be generated due to API errors",
                "answer": "Please try again later",
                "context": "API rate limit exceeded",
                "type": "text",
            }
        )

    # 1. Create a new workbook and select the active sheet
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Quiz Questions"

    # Define headers for the columns
    headers = ["Question No.", "Question", "Answer", "Context", "Image/Type"]
    sheet.append(headers)

    # Format headers
    header_font = Font(bold=True)
    for cell in sheet[1]:
        cell.font = header_font
        cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Set column widths for better readability
    sheet.column_dimensions["A"].width = 15
    sheet.column_dimensions["B"].width = 40
    sheet.column_dimensions["C"].width = 25
    sheet.column_dimensions["D"].width = 50
    sheet.column_dimensions["E"].width = 15

    # Write the quiz questions to the sheet
    for i, question in enumerate(all_quiz_questions):
        row_num = i + 2  # Start from row 2 after headers

        # Make titles for each question
        sheet[f"A{row_num}"] = f"Question {i+1}"

        # Question column with text wrapping
        sheet[f"B{row_num}"] = question.get("question", "Error: No question")
        sheet[f"B{row_num}"].alignment = Alignment(wrap_text=True, vertical="top")

        # Answer column with text wrapping
        sheet[f"C{row_num}"] = question.get("answer", "Error: No answer")
        sheet[f"C{row_num}"].alignment = Alignment(wrap_text=True, vertical="top")

        # Context column with text wrapping
        sheet[f"D{row_num}"] = question.get("context", "Error: No context")
        sheet[f"D{row_num}"].alignment = Alignment(wrap_text=True, vertical="top")

        if question.get("type") == "image":
            try:
                # Check if image_bytes exists and is valid
                if question.get("image_bytes"):
                    # Decode the base64 image bytes
                    img_data = base64.b64decode(question["image_bytes"])
                    img = PILImage.open(io.BytesIO(img_data))

                    # Resize image to exactly 100x100 pixels
                    img = img.resize((100, 100), PILImage.Resampling.LANCZOS)

                    # Save the resized image to a byte stream
                    img_byte_arr = io.BytesIO()
                    img.save(
                        img_byte_arr, format="PNG"
                    )  # Always save as PNG for consistency
                    img_byte_arr.seek(0)  # Rewind to the beginning of the stream

                    # Create an openpyxl Image object
                    excel_img = OpenpyxlImage(img_byte_arr)

                    # Set the image size in Excel to 100x100
                    excel_img.width = 100
                    excel_img.height = 100

                    # Add the image to the sheet, anchored to cell E{row_num}
                    excel_img.anchor = f"E{row_num}"
                    sheet.add_image(excel_img)

                    # Set row height to accommodate the image
                    sheet.row_dimensions[row_num].height = 75  # 100 pixels = ~75 points

                    sheet[f"E{row_num}"] = "Image (see embedded)"
                else:
                    sheet[f"E{row_num}"] = "No image available"
            except Exception as e:
                sheet[f"E{row_num}"] = f"Error loading image: {e}"
                print(f"Error processing image for question {i+1}: {e}")

        elif question.get("type") == "text":
            sheet[f"E{row_num}"] = "Text Question"

        # Set row height for text rows to accommodate wrapped text
        if question.get("type") == "text":
            sheet.row_dimensions[row_num].height = 60  # Allow for wrapped text

    # Save the workbook to an in-memory byte stream
    excel_file = io.BytesIO()
    workbook.save(excel_file)
    excel_file.seek(0)  # Rewind to the beginning of the stream

    return excel_file.getvalue()