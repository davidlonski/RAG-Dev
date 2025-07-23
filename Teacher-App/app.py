import streamlit as st
import io
import json
import os
import time
import openpyxl
import base64
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Alignment, Font
from PIL import Image as PILImage
from PIL import Image
from pptx_rag_quizzer.utils import build_excel_quiz_spreadsheet

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
        ss.app_stage = "dashboard"
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
    if "image_magic" not in ss:
        ss.image_magic = ImageMagic(ss.rag_controller)
    if "quiz_master" not in ss:
        ss.quiz_master = QuizMaster(ss.rag_controller)


init_session_state()


# --- Helper Functions ---
def reset_app():
    """Resets the application to its initial state."""
    st.cache_data.clear()
    st.cache_resource.clear()
    for key in list(ss.keys()):
        del ss[key]
    st.rerun()

def make_homework_data():

    image_question_list = []
    text_question_list = []

    for _ in range(3):
        image_question = ss.quiz_master.generate_image_question()
        text_question = ss.quiz_master.generate_text_question()
        image_question_list.append(image_question)
        text_question_list.append(text_question)
    
    return image_question_list, text_question_list

def save_homework_data(image_question_list, text_question_list):
    with open("homework_data.json", "w") as f:
        json.dump({"image_question_list": image_question_list, "text_question_list": text_question_list}, f, indent=4)


# --- Sidebar ---
with st.sidebar:
    st.header("Navigation & Control")
    if st.button("Start Over"):
        reset_app()

    if st.button("Dashboard"):
        ss.app_stage = "dashboard"
        st.rerun()


# --- Main Application Flow ---

# STAGE 1: Dashboard
if ss.app_stage == "dashboard":
    st.header("Teacher Dashboard")

    options = st.selectbox(
        "Select an option",
        [
            "Upload PowerPoint",
            "Generate Homework",
        ],
    )

    if options == "Upload PowerPoint":
        st.header("Upload PowerPoint")
        if st.button("Go to Upload"):
            ss.app_stage = "upload_powerpoint"
            st.rerun()
    elif options == "Generate Homework":
        st.header("Generate Homework")
        if st.button("Generate Homework"):
            ss.app_stage = "generate_homework"
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
                ss.app_stage = "dashboard"
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
        try:
            with st.spinner("Building quiz RAG..."):
                ss.rag_controller.build_collection(ss.extracted_data, "quiz")
            ss.app_stage = "dashboard"
            st.rerun()
        except Exception as e:
            st.error(f"Error building quiz RAG: {e}")
            ss.app_stage = "dashboard"
            st.rerun()

# STAGE 6: Generate Homework
elif ss.app_stage == "generate_homework":
    st.header("Generate Homework")

    # Initialize session state for homework generation
    if "questions_generated" not in ss:
        ss.questions_generated = False
    if "all_questions" not in ss:
        ss.all_questions = []
    if "current_batch_index" not in ss:
        ss.current_batch_index = 0
    if "approved_questions" not in ss:
        ss.approved_questions = []

    BATCH_SIZE = 5

    if not ss.questions_generated:
        if st.button("Generate Homework"):
            image_question_list, text_question_list = make_homework_data()
            # Combine image and text questions into a single sequence
            ss.all_questions = image_question_list + text_question_list
            ss.current_batch_index = 0
            ss.approved_questions = [None] * len(ss.all_questions)
            ss.questions_generated = True
            st.rerun()
    else:
        total = len(ss.all_questions)
        batch_start = ss.current_batch_index * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, total)
        st.write(f"Questions {batch_start+1} to {batch_end} of {total}")
        for idx in range(batch_start, batch_end):
            question = ss.all_questions[idx]
            st.markdown(f"**Question {idx+1}**")
            edited_question = st.text_area("Question", value=question.get("question", ""), key=f"q_{idx}")
            edited_answer = st.text_area("Answer", value=question.get("answer", ""), key=f"a_{idx}")
            edited_context = st.text_area("Context", value=question.get("context", ""), key=f"c_{idx}")
            # If image question, show image
            if question.get("type") == "image" and question.get("image_bytes"):
                try:
                    import base64, io
                    img_data = base64.b64decode(question["image_bytes"])
                    st.image(Image.open(io.BytesIO(img_data)), caption="Image for this question")
                except Exception as e:
                    st.warning(f"Could not display image: {e}")
            # Approve/save this question
            if st.button("Approve & Save This Question", key=f"approve_{idx}"):
                ss.approved_questions[idx] = {
                    "question": edited_question,
                    "answer": edited_answer,
                    "context": edited_context,
                    "type": question.get("type"),
                    "image_bytes": question.get("image_bytes") if question.get("type") == "image" else None,
                }
                st.success(f"Question {idx+1} approved!")
        # Navigation for batches
        col1, col2 = st.columns(2)
        with col1:
            if ss.current_batch_index > 0:
                if st.button("Previous Batch"):
                    ss.current_batch_index -= 1
                    st.rerun()
        with col2:
            if batch_end < total:
                if st.button("Next Batch"):
                    ss.current_batch_index += 1
                    st.rerun()
        # If all questions are approved, show save button
        if all(q is not None for q in ss.approved_questions):
            if st.button("Save All Approved Questions"):
                image_questions = [q for q in ss.approved_questions if q["type"] == "image"]
                text_questions = [q for q in ss.approved_questions if q["type"] == "text"]
                save_homework_data(image_questions, text_questions)
                st.success("All approved questions saved!")
                # Optionally, reset state
                del ss.questions_generated
                del ss.all_questions
                del ss.current_batch_index
                del ss.approved_questions
                st.rerun()
    st.write("---")
    if st.button("Back to Dashboard"):
        ss.app_stage = "dashboard"
        st.rerun()
