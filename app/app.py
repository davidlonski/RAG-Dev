import streamlit as st
import io
import time
import openpyxl
import base64
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Alignment, Font
from PIL import (
    Image as PILImage,
)  # Renamed to avoid conflict with openpyxl.drawing.image.Image

from PIL import Image

from pptx_rag_quizzer.rag_controller import RAGController
from pptx_rag_quizzer.quiz_master import QuizMaster
from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.image_magic import ImageMagic

# --- Page Configuration ---
st.set_page_config(page_title="RAG Homework Generator", page_icon="📚", layout="wide")

# --- Application Title ---
st.title("📚 RAG Homework Generator")
st.markdown(
    "Teachers: Upload PowerPoint, describe images, and generate homework. Students: Download and complete assignments."
)

ss = st.session_state


# --- Session State Initialization ---
def init_session_state():
    """Initialize session state variables."""
    if "app_stage" not in ss:
        ss.app_stage = "role_selection"
    if "user_role" not in ss:
        ss.user_role = None
    if "extracted_data" not in ss:
        ss.extracted_data = []
    if "images_to_describe" not in ss:
        ss.images_to_describe = []
    if "current_image_index" not in ss:
        ss.current_image_index = 0
    if "spreadsheet_list" not in ss:
        ss.spreadsheet_list = []

    # Initialize RAG components only if they don't exist
    if "rag_controller" not in ss:
        ss.rag_controller = RAGController()
    if "quiz_master" not in ss:
        ss.quiz_master = QuizMaster(ss.rag_controller)
    if "image_magic" not in ss:
        ss.image_magic = ImageMagic(ss.rag_controller)


init_session_state()


# --- Helper Functions ---
def reset_app():
    """Resets the application to its initial state."""
    st.cache_data.clear()
    st.cache_resource.clear()
    for key in list(ss.keys()):
        del ss[key]
    st.rerun()


def build_excel_quiz_spreadsheet():
    """
    Builds a spreadsheet of the quiz images, questions, and answers.
    Returns an in-memory Excel file (bytes).
    """
    all_quiz_questions = []

    count = 25

    # Generate 3 random image quiz questions
    for _ in range(count):
        try:
            question = ss.quiz_master.generate_image_question()
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
    for _ in range(count):
        try:
            question = ss.quiz_master.generate_text_question()
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
    sheet.column_dimensions["C"].width = 40
    sheet.column_dimensions["D"].width = 60
    sheet.column_dimensions["E"].width = 60  # Increased from 15 to accommodate 400px images

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

                    # Resize image to exactly 400x400 pixels
                    img = img.resize((400, 400), PILImage.Resampling.LANCZOS)

                    # Save the resized image to a byte stream
                    img_byte_arr = io.BytesIO()
                    img.save(
                        img_byte_arr, format="PNG"
                    )  # Always save as PNG for consistency
                    img_byte_arr.seek(0)  # Rewind to the beginning of the stream

                    # Create an openpyxl Image object
                    excel_img = OpenpyxlImage(img_byte_arr)

                    # Set the image size in Excel to 400x400
                    excel_img.width = 400
                    excel_img.height = 400

                    # Add the image to the sheet, anchored to cell E{row_num}
                    excel_img.anchor = f"E{row_num}"
                    sheet.add_image(excel_img)

                    # Set row height to accommodate the larger image
                    sheet.row_dimensions[row_num].height = 300  # 400 pixels = ~300 points

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


# --- Sidebar ---
with st.sidebar:
    st.header("Navigation & Control")
    if st.button("Start Over"):
        reset_app()

    if ss.user_role:
        if st.button("Logout"):
            # Just go back to role selection, don't reset everything
            ss.app_stage = "role_selection"
            ss.user_role = None
            st.rerun()

    if ss.user_role:
        st.write(f"**Current Role:** {ss.user_role.title()}")
        st.write(f"**Current Stage:** {ss.app_stage.replace('_', ' ').title()}")

# --- Main Application Flow ---

# STAGE 0: Role Selection
if ss.app_stage == "role_selection":
    st.header("👥 Select Your Role")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👨‍🏫 Teacher")
        st.write("• Upload PowerPoint presentations")
        st.write("• Describe images and content")
        st.write("• Generate homework spreadsheets")

        if st.button("I'm a Teacher"):
            ss.user_role = "teacher"
            ss.app_stage = "dashboard"
            st.rerun()

    with col2:
        st.subheader("👨‍🎓 Student")
        st.write("• View homework spreadsheets")

        if st.button("I'm a Student"):
            ss.user_role = "student"
            ss.app_stage = "dashboard"
            st.rerun()

# TEACHER FLOW
elif ss.user_role == "teacher":

    # STAGE 1: Dashboard
    if ss.app_stage == "dashboard":
        st.header("Teacher Dashboard")

        options = st.selectbox(
            "Select an option",
            [
                "Upload PowerPoint",
                "View Generated Spreadsheets",
                "Generate Quiz Spreadsheet",
            ],
        )

        if options == "Upload PowerPoint":
            st.header("Upload PowerPoint")
            if st.button("Go to Upload"):
                ss.app_stage = "upload_powerpoint"
                st.rerun()
        elif options == "View Generated Spreadsheets":
            st.header("View Generated Spreadsheets")
            if st.button("View Spreadsheets"):
                ss.app_stage = "view_spreadsheets"
                st.rerun()
        elif options == "Generate Quiz Spreadsheet":
            st.header("Generate Quiz Spreadsheet")
            if st.button("Generate Spreadsheet"):
                ss.app_stage = "build_spreadsheet"
                st.rerun()

    # STAGE 2: Upload PowerPoint
    elif ss.app_stage == "upload_powerpoint":
        st.header("Upload PowerPoint")
        uploaded_file = st.file_uploader("Choose a .pptx file", type="pptx")
        if uploaded_file:
            with st.spinner("Parsing your PowerPoint..."):
                try:
                    file_in_memory = io.BytesIO(uploaded_file.getvalue())
                    ss.extracted_data = parse_powerpoint(file_in_memory)
                    st.success(
                        f"Successfully parsed PowerPoint! Found {len(ss.extracted_data)} items."
                    )
                    ss.app_stage = "build_image_rag"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error parsing PowerPoint: {e}")
                    st.info("Please try uploading a different PowerPoint file.")
                    st.rerun()

    # STAGE 3: Building image RAG
    elif ss.app_stage == "build_image_rag":
        with st.spinner("Building image RAG..."):
            try:
                ss.rag_controller.build_collection(ss.extracted_data, "picture")
                st.success("Successfully built image RAG!")
                ss.app_stage = "describe_images"
                st.rerun()
            except Exception as e:
                st.error(f"Error building RAG: {e}")
                st.info(
                    "Please try uploading a different PowerPoint file or check if the file contains images."
                )
                ss.app_stage = "dashboard"
                st.rerun()

    # STAGE 4: Describe Images
    elif ss.app_stage == "describe_images":
        ss.images_to_describe = [
            item for item in ss.extracted_data if item["type"] == "image"
        ]

        total = len(ss.images_to_describe)
        idx = ss.current_image_index

        # If there are more than 6 images, process in batches of 5
        if total > 6:
            # Calculate the current batch
            batch_start = idx
            batch_end = min(idx + 5, total)
            current_batch = ss.images_to_describe[batch_start:batch_end]

            # Check if all images in current batch have descriptions
            batch_ready = all("description" in img_item for img_item in current_batch)

            if not batch_ready:
                # Show loading screen while generating descriptions
                st.write(f"**Processing {total} images in batches of 5**")
                st.progress((idx + 1) / total)
                st.write(
                    f"**Generating descriptions for images {batch_start + 1} to {batch_end}...**"
                )

                with st.spinner(
                    "AI is analyzing images and generating descriptions. This may take up to 1 minute per image..."
                ):
                    for i, img_item in enumerate(current_batch):
                        if "description" not in img_item:
                            try:
                                st.write(
                                    f"Describing image {batch_start + i + 1} of {total}..."
                                )
                                image_description = ss.image_magic.describe_image(
                                    img_item["content"],
                                    img_item["extension"],
                                    img_item["slide_number"],
                                )
                                img_item["description"] = image_description
                                st.write(
                                    f"✓ Image {batch_start + i + 1} described successfully"
                                )
                            except Exception as e:
                                image_description = f"Error describing image: {e}"
                                img_item["description"] = image_description
                                st.write(
                                    f"✗ Error describing image {batch_start + i + 1}: {e}"
                                )

                st.success("All descriptions generated! Displaying images...")
                st.rerun()
            else:
                # Display current batch of images with descriptions
                st.write(
                    f"**Batch {batch_start // 5 + 1}: Images {batch_start + 1} to {batch_end} of {total}**"
                )
                st.progress((batch_end) / total)

                for i, img_item in enumerate(current_batch):
                    st.write(
                        f"**Image {batch_start + i + 1} of {total}** (from Slide {img_item['slide_number']})"
                    )
                    st.image(
                        Image.open(io.BytesIO(img_item["content"])),
                        use_container_width=True,
                    )

                    # Text area for each image with pre-generated description
                    description = st.text_area(
                        f"What is important about image {batch_start + i + 1}?",
                        key=f"desc_{img_item['id']}",
                        value=img_item["description"],
                    )
                    img_item["description"] = description
                    st.write("---")

                # Navigation buttons for batch processing
                col1, col2, col3 = st.columns(3)

                with col1:
                    if batch_start > 0:
                        if st.button("Previous Batch", key="prev_batch"):
                            ss.current_image_index = max(0, batch_start - 5)
                            st.rerun()

                with col2:
                    if st.button("Save Batch", key="save_batch"):
                        # Save all descriptions in current batch
                        for img_item in current_batch:
                            if img_item.get("description"):
                                img_item["description"] = img_item["description"]
                        st.success("Batch saved!")

                with col3:
                    if batch_end < total:
                        if st.button("Next Batch", key="next_batch"):
                            ss.current_image_index = batch_end
                            st.rerun()
                    else:
                        if st.button("Finish", key="finish"):
                            ss.app_stage = "build_quiz_rag"
                            st.rerun()
        else:
            # Original single image processing for 6 or fewer images
            if idx < total:
                img_item = ss.images_to_describe[idx]
                st.progress((idx + 1) / total)
                st.write(
                    f"**Image {idx + 1} of {total}** (from Slide {img_item['slide_number']})"
                )
                st.image(
                    Image.open(io.BytesIO(img_item["content"])),
                    use_container_width=True,
                )

                # Only generate description if it doesn't already exist
                if "description" not in img_item:
                    try:
                        image_description = ss.image_magic.describe_image(
                            img_item["content"],
                            img_item["extension"],
                            img_item["slide_number"],
                        )
                        img_item["description"] = image_description
                    except Exception as e:
                        image_description = f"Error describing image: {e}"
                        img_item["description"] = image_description
                else:
                    image_description = img_item["description"]

                description = st.text_area(
                    "What is important about this image?",
                    key=f"desc_{img_item['id']}",
                    value=image_description,
                )

                if st.button("Submit Description", key=f"submit_{idx}"):
                    if description:
                        # Update description in the image object
                        img_item["description"] = description
                        ss.current_image_index += 1
                    else:
                        st.warning("Please provide a description.")
            else:
                st.success("All images described!")
                ss.app_stage = "build_quiz_rag"
                st.rerun()

    # STAGE 5: Building quiz RAG
    elif ss.app_stage == "build_quiz_rag":
        with st.spinner("Building quiz RAG..."):
            try:
                ss.rag_controller.build_collection(ss.extracted_data, "quiz")
                ss.app_stage = "dashboard"
                st.rerun()
            except Exception as e:
                st.error(f"Error building quiz RAG: {e}")
                ss.app_stage = "dashboard"
                st.rerun()

    # STAGE 6: Build Spreadsheet
    elif ss.app_stage == "build_spreadsheet":
        # Only generate spreadsheet if it hasn't been generated yet
        if "excel_file" not in ss:
            with st.spinner("Building spreadsheet..."):
                ss.excel_file = build_excel_quiz_spreadsheet()
            st.success("Spreadsheet generated successfully!")
        else:
            st.success("Spreadsheet ready for download!")

        st.download_button(
            label="Download Spreadsheet",
            data=ss.excel_file,
            file_name="quiz_questions.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        if st.button("Save Spreadsheet"):
            ss.spreadsheet_list.append(ss.excel_file)
            st.success("Spreadsheet saved successfully!")

        if st.button("Back to Dashboard"):
            ss.app_stage = "dashboard"
            st.rerun()

    # STAGE 7: View Spreadsheets
    elif ss.app_stage == "view_spreadsheets":
        st.header("View Spreadsheets")
        for spreadsheet in ss.spreadsheet_list:
            st.header(f"Homework {ss.spreadsheet_list.index(spreadsheet) + 1}")
            st.download_button(
                label="Download Spreadsheet",
                data=spreadsheet,
                file_name=f"quiz_questions_{ss.spreadsheet_list.index(spreadsheet) + 1}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.write("---")

        if st.button("Back to Dashboard"):
            ss.app_stage = "dashboard"
            st.rerun()

# STUDENT FLOW
elif ss.user_role == "student":

    # STAGE 1: Dashboard
    if ss.app_stage == "dashboard":
        st.header("Student Dashboard")

        options = st.selectbox("Select an option", ["View Homework"])
        if options == "View Homework":
            if st.button("View Homework"):
                ss.app_stage = "view_homework"
                st.rerun()

    # STAGE 2: View Homework
    elif ss.app_stage == "view_homework":
        for spreadsheet in ss.spreadsheet_list:
            st.header(f"Homework {ss.spreadsheet_list.index(spreadsheet) + 1}")
            st.download_button(
                label="Download Spreadsheet",
                data=spreadsheet,
                file_name="quiz_questions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        if st.button("Back to Dashboard"):
            ss.app_stage = "dashboard"
            st.rerun()
