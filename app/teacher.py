import streamlit as st
import io
import sys
import os
import base64
from PIL import Image

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(__file__))

from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.quiz_master import QuizMaster
from database.image_server import ImageServer
from pptx_rag_quizzer.image_magic import ImageMagic
from database.homework_server import HomeworkServer

# Page configuration
st.set_page_config(
    page_title="Teacher Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

ss = st.session_state

# Initialize session state
if "teacher_id" not in ss:
    ss.teacher_id = None  # set via login
if "rag_core" not in ss:
    ss.rag_core = None
if "homework_server" not in ss:
    ss.homework_server = None
if "image_server" not in ss:
    ss.image_server = None
if "image_magic" not in ss:
    ss.image_magic = None
if "app_stage" not in ss:
    ss.app_stage = "dashboard"
if "presentation" not in ss:
    ss.presentation = None
if "generated_questions" not in ss:
    ss.generated_questions = []


# Simple login
def login_panel():
    st.header("🔐 Login (Teacher)")
    with st.form("teacher_login_form"):
        teacher_id = st.text_input("Teacher ID", value=ss.get("teacher_id") or "")
        submitted = st.form_submit_button("Login")
        if submitted:
            if not teacher_id.strip():
                st.error("Please enter a Teacher ID")
            else:
                ss.teacher_id = teacher_id.strip()
                st.success("Logged in")
                st.rerun()


def initialize_services():
    try:
        if ss.image_server is None:
            ss.image_server = ImageServer()
        if ss.homework_server is None:
            ss.homework_server = HomeworkServer()
        if ss.rag_core is None:
            ss.rag_core = RAGCore()
        if ss.image_magic is None:
            ss.image_magic = ImageMagic(ss.rag_core)
        return True
    except Exception as e:
        st.error(f"❌ Error initializing services: {e}")
        return False


def upload_and_process_pptx():
    st.header("📁 Upload PPTX")
    uploaded_file = st.file_uploader("Upload PowerPoint file (.pptx)", type=["pptx"])

    if uploaded_file is not None:
        with st.spinner("Processing PowerPoint file..."):
            try:
                file_bytes = uploaded_file.read()
                file_object = io.BytesIO(file_bytes)
                presentation = parse_powerpoint(file_object, uploaded_file.name)
                ss.presentation = presentation
                st.success("✅ PowerPoint file processed successfully!")

                st.write("**Presentation Details:**")
                st.write(f"**ID:** {presentation.id}")
                st.write(f"**Slides:** {len(presentation.slides)}")

                total_text = sum(
                    len([item for item in slide.items if item.type.value == "text"]) for slide in presentation.slides
                )
                total_images = sum(
                    len([item for item in slide.items if item.type.value == "image"]) for slide in presentation.slides
                )
                st.write(f"**Text Items:** {total_text}")
                st.write(f"**Images:** {total_images}")

                if st.button("🚀 Next: Describe Images", type="primary"):
                    ss.app_stage = "describe_images"
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error processing PowerPoint file: {e}")


def describe_images():
    st.header("📋 Describe Images")
    if ss.presentation is None:
        st.error("No presentation found. Please upload a presentation first.")
        ss.app_stage = "upload_pptx"
        st.rerun()
        return

    if not initialize_services():
        return

    all_images = [item for slide in ss.presentation.slides for item in slide.items if item.type.value == "image"]
    total = len(all_images)
    if total == 0:
        st.info("No images found in the presentation.")
        ss.app_stage = "generate_homework"
        st.rerun()
        return

    if "current_image_index" not in ss:
        ss.current_image_index = 0

    idx = ss.current_image_index

    # batch processing for >6 images
    if total > 6:
        batch_start = idx
        batch_end = min(idx + 5, total)
        current_batch = all_images[batch_start:batch_end]

        # Generate missing descriptions
        if any((not it.content or it.content.lower() in ["none", "", "null"]) for it in current_batch):
            st.write(f"**Generating descriptions for images {batch_start + 1} to {batch_end}...**")
            with st.spinner("AI analyzing images..."):
                for i, img_item in enumerate(current_batch):
                    if not img_item.content or img_item.content.lower() in ["none", "", "null"]:
                        try:
                            desc = ss.image_magic.describe_image(
                                img_item.image_bytes, img_item.extension, img_item.slide_number, None
                            )
                            img_item.content = desc if desc and desc != "None" else "No description available"
                        except Exception as e:
                            img_item.content = f"Error: {e}"
            st.success("Descriptions generated. Review below.")
            st.rerun()
        else:
            st.write(
                f"**Batch {batch_start // 5 + 1}: Images {batch_start + 1} to {batch_end} of {total}**"
            )
            for i, img_item in enumerate(current_batch):
                st.write(
                    f"**Image {batch_start + i + 1} of {total}** (Slide {img_item.slide_number})"
                )
                st.image(Image.open(io.BytesIO(img_item.image_bytes)), use_container_width=True)
                img_item.content = st.text_area(
                    f"What is important about image {batch_start + i + 1}?",
                    key=f"desc_{img_item.id}",
                    value=img_item.content or "",
                )
                st.write("---")

            col1, col2, col3 = st.columns(3)
            with col1:
                if batch_start > 0 and st.button("Previous Batch"):
                    ss.current_image_index = max(0, batch_start - 5)
                    st.rerun()
            with col2:
                if st.button("Save Batch"):
                    st.success("Batch saved")
            with col3:
                if batch_end < total:
                    if st.button("Next Batch"):
                        ss.current_image_index = batch_end
                        st.rerun()
                else:
                    if st.button("Finish Descriptions"):
                        ss.app_stage = "generate_homework"
                        st.rerun()
    else:
        # <=6 images
        if idx < total:
            img_item = all_images[idx]
            st.write(f"Image {idx + 1} of {total} (Slide {img_item.slide_number})")
            st.image(Image.open(io.BytesIO(img_item.image_bytes)), use_container_width=True)
            if not img_item.content or img_item.content.lower() in ["none", "", "null"]:
                try:
                    desc = ss.image_magic.describe_image(
                        img_item.image_bytes, img_item.extension, img_item.slide_number, None
                    )
                    img_item.content = desc if desc and desc != "None" else "No description available"
                except Exception as e:
                    img_item.content = f"Error: {e}"
            img_item.content = st.text_area(
                "What is important about this image?",
                key=f"desc_{img_item.id}",
                value=img_item.content or "",
            )
            if st.button("Submit Description"):
                ss.current_image_index += 1
                st.rerun()
        else:
            st.success("All images described!")
            ss.app_stage = "generate_homework"
            st.rerun()


def generate_homework():
    st.header("📋 Generate Homework")
    if ss.presentation is None:
        st.info("Please upload a presentation first.")
        ss.app_stage = "upload_pptx"
        st.rerun()
        return

    if not initialize_services():
        return

    st.write("Specify how many questions to generate:")
    num_text_questions = st.number_input("Text questions", min_value=0, max_value=20, value=3)
    num_image_questions = st.number_input("Image questions", min_value=0, max_value=20, value=2)

    if st.button("🎯 Generate"):
        try:
            quiz_master = QuizMaster(ss.rag_core)
            questions = []
            for _ in range(num_text_questions):
                q = quiz_master.generate_text_question(None)
                if q:
                    questions.append(q)
            for _ in range(num_image_questions):
                q = quiz_master.generate_image_question(None)
                if q:
                    questions.append(q)
            ss.generated_questions = questions
            st.success(f"Generated {len(questions)} questions")
        except Exception as e:
            st.error(f"Error generating questions: {e}")

    if ss.generated_questions:
        st.subheader("Preview")
        for i, q in enumerate(ss.generated_questions, 1):
            st.write(f"{i}. {q['question']}")
            if q["type"] == "image" and "image_bytes" in q:
                try:
                    st.image(base64.b64decode(q["image_bytes"]))
                except Exception:
                    st.warning("Could not render image preview")
            with st.expander("Answer & Context"):
                st.write(q.get("answer"))
                ctx = q.get("context", "")
                st.write(ctx[:300] + ("..." if len(ctx) > 300 else ""))
        st.write("---")
        name = st.text_input("Assignment name", value=ss.presentation.name)
        if st.button("💾 Save to Database") and name:
            payload = {
                "collection_id": None,
                "questions": ss.generated_questions,
                "num_text_questions": sum(1 for q in ss.generated_questions if q["type"] == "text"),
                "num_image_questions": sum(1 for q in ss.generated_questions if q["type"] == "image"),
                "status": "active",
                "name": name,
            }
            assignment_id = ss.homework_server.create_assignment(payload)
            if assignment_id:
                ss.generated_questions = []
                st.success("Assignment saved")

    if st.button("← Back to Dashboard"):
        ss.app_stage = "dashboard"
        st.rerun()


def manage_assignments():
    st.header("📚 Manage Assignments")
    if not initialize_services():
        return
    assignments = ss.homework_server.list_assignments()
    if not assignments:
        st.info("No assignments yet.")
        return

    for a in assignments:
        with st.expander(f"{a['name']} — {a['num_questions']} questions"):
            st.write(f"Created: {a.get('created_at','')}")
            st.write(
                f"Text: {a['num_text_questions']}, Image: {a['num_image_questions']}"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 View Results", key=f"view_{a['id']}"):
                    st.info("Results viewing coming soon")
            with col2:
                if st.button("🗑️ Delete", key=f"del_{a['id']}"):
                    ss.homework_server.delete_assignment(a["id"])
                    st.success("Deleted")
                    st.rerun()


def dashboard():
    st.header("📋 Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Upload PPTX"):
            ss.app_stage = "upload_pptx"
            st.rerun()
    with col2:
        if st.button("Generate Homework"):
            ss.app_stage = "generate_homework"
            st.rerun()
    with col3:
        if st.button("Manage Assignments"):
            ss.app_stage = "manage_assignments"
            st.rerun()


# Main app
st.title("🎓 Teacher Dashboard")

with st.sidebar:
    st.header("🧭 Navigation")
    if ss.teacher_id:
        st.write(f"Teacher: {ss.teacher_id}")
        if st.button("Logout"):
            ss.teacher_id = None
            ss.app_stage = "dashboard"
            st.rerun()
    else:
        st.info("Please login to continue")

# Guard: require login
if not ss.teacher_id:
    login_panel()
else:
    st.write(f"**Current Stage:** {ss.app_stage.replace('_', ' ').title()}")
    if ss.app_stage == "dashboard":
        dashboard()
    elif ss.app_stage == "upload_pptx":
        upload_and_process_pptx()
    elif ss.app_stage == "describe_images":
        describe_images()
    elif ss.app_stage == "generate_homework":
        generate_homework()
    elif ss.app_stage == "manage_assignments":
        manage_assignments()