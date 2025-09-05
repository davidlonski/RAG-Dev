import streamlit as st
import io
import json
import pandas as pd
from datetime import datetime
import sys
import os
from PIL import Image
from models import RAG_quizzer
import uuid
# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(__file__))

from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.quiz_master import QuizMaster
from database.image_db import ImageServer
from pptx_rag_quizzer.image_magic import ImageMagic
from database.homework_db import HomeworkServer
from database.user_db import UserServer


# Page configuration
st.set_page_config(
    page_title="Teacher Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ss = st.session_state

# Initialize session state
if 'rag_core' not in ss:
    ss.rag_core = None
if 'homework_server' not in ss:
    ss.homework_server = HomeworkServer()
if 'image_server' not in ss:
    ss.image_server = ImageServer()
if 'image_magic' not in ss:
    ss.image_magic = None
if 'user_server' not in ss:
    ss.user_server = UserServer()

if 'current_user' not in ss:
    ss.current_user = None
if 'app_stage' not in ss:
    ss.app_stage = 'dashboard'
if 'rag_quizzer_list' not in ss:
    ss.rag_quizzer_list = []
if 'homework_assignments' not in ss:
    ss.homework_assignments = []
if 'homework_preview' not in ss:
    ss.homework_preview = None
if 'selected_assignment_for_results' not in ss:
    ss.selected_assignment_for_results = None


def initialize_services():
    """Initialize RAG core, image server, and image magic services"""
    try:
        if ss.image_server is None:
            ss.image_server = ImageServer()
        if ss.homework_server is None:
            ss.homework_server = HomeworkServer()
        ss.rag_core = RAGCore()
        if not ss.rag_core.llm_model:
            st.error("❌ Google API key not found or invalid. Please check your .env file.")
            return False
        ss.image_magic = ImageMagic(ss.rag_core)
        return True
    except Exception as e:
        st.error(f"❌ Error initializing services: {e}")
        return False

'''
    Upload and processing PPTX, PPT
'''
def upload_and_process_pptx():
    """Upload and process PowerPoint file"""
    st.header("📁 Upload PPTX")
    
    
    uploaded_file = st.file_uploader(
        "Upload PowerPoint file (.pptx)",
        type=['pptx'],
        help="Select a PowerPoint file to process"
    )
    
    if uploaded_file is not None:
        
        with st.spinner("Processing PowerPoint file..."):
            file_bytes = uploaded_file.read()
            file_object = io.BytesIO(file_bytes)
            presentation = parse_powerpoint(file_object, uploaded_file.name)
            try:
                
                # Display presentation info
                st.success(f"✅ PowerPoint file processed successfully!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Presentation Details:**")
                    st.write(f"**Slides:** {len(presentation.slides)}")
                    
                    # Count items
                    total_text = sum(len([item for item in slide.items if item.type.value == 'text']) for slide in presentation.slides)
                    total_images = sum(len([item for item in slide.items if item.type.value == 'image']) for slide in presentation.slides)
                    
                    st.write(f"**Text Items:** {total_text}")
                    st.write(f"**Images:** {total_images}")

                    if len(presentation.slides) > 5:
                        st.write(f"... and {len(presentation.slides) - 5} more slides")
                
                with col2:
                    st.write("**Process PPTX:**")
                    
                    if st.button("🚀 Process Presentation", type="primary"):
                        process_presentation(presentation)
                
                
                    
            except Exception as e:
                st.error(f"❌ Error processing PowerPoint file: {e}")
    
    # Back button
    if st.button("← Back to Dashboard"):
        ss.app_stage = "dashboard"
        st.rerun()

def process_presentation(presentation):
    """Process the presentation and store in database"""
    try:
        
        if not initialize_services():
            return
        
        # Create RAG collection if requested
        collection_id = None
        with st.spinner("Creating RAG collection..."):
            collection_id = ss.rag_core.create_collection(presentation)
            st.success(f"✅ RAG collection created: {collection_id}")

        # Describe images
        ss.presentation_metadata = (presentation, collection_id)
        ss.app_stage = "describe_images"
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error processing presentation: {e}")


def describe_images():
    """Describe images"""
    st.header("📋 Describe Images")
    
    # Add back button
    if st.button("← Back to Upload", key="describe_back"):
        ss.app_stage = "upload_pptx"
        st.rerun()
    
    if 'presentation_metadata' not in ss:
        st.error("No presentation metadata found. Please upload a presentation first.")
        ss.app_stage = "upload_pptx"
        st.rerun()
        return
    
    presentation, collection_id = ss.presentation_metadata

    # Extract all images and sort them by slide number and order number to maintain proper sequence
    all_images = []
    for slide in presentation.slides:
        for item in slide.items:
            if item.type.value == 'image':
                all_images.append(item)
    
    # Sort images by slide number first, then by order number within each slide
    all_images.sort(key=lambda img: (img.slide_number, img.order_number))
    total = len(all_images)
    
    if total == 0:
        st.info("No images found in the presentation.")
        ss.app_stage = "upload_pptx"
        st.rerun()
        return
    
    # Initialize current image index if not set
    if 'current_image_index' not in ss:
        ss.current_image_index = 0
    
    idx = ss.current_image_index
    
    # Always use batch processing with max batch size of 10
    BATCH_SIZE = 10
    
    # Calculate the current batch
    batch_start = idx
    batch_end = min(idx + BATCH_SIZE, total)
    current_batch = all_images[batch_start:batch_end]
    
    # Calculate current batch number and total batches
    current_batch_num = (batch_start // BATCH_SIZE) + 1
    total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division

    # Check if all images in current batch have descriptions
    batch_ready = all(img_item.content and img_item.content.lower() not in ['none', 'null', ''] for img_item in current_batch)

    if not batch_ready:
        # Show loading screen while generating descriptions
        st.write(f"**Processing {total} images in batches of {BATCH_SIZE}**")
        st.progress((idx + 1) / total)
        st.write(
                f"**Generating descriptions for images {batch_start + 1} to {batch_end}...**"
        )

        with st.spinner("AI is analyzing images and generating descriptions. This may take up to 1 minute per image..."):
            for i, img_item in enumerate(current_batch):
                if not img_item.content or img_item.content.lower() in ['none', 'null', '']:
                    try:
                        st.write(
                            f"Describing image {batch_start + i + 1} of {total}..."
                        )
                        image_description = ss.image_magic.describe_image(
                            img_item.image_bytes,
                            img_item.extension,
                            img_item.slide_number,
                            collection_id
                        )
                        
                        # if image_description starts with "Description: " remove it
                        if image_description and image_description.startswith("Description: "):
                            image_description = image_description[len("Description: "):]
                        
                        if image_description and image_description != "None":
                            img_item.content = image_description
                            st.write(
                                f"✓ Image {batch_start + i + 1} described successfully"
                            )
                        else:
                            img_item.content = "No description available"
                            st.write(
                                f"⚠️ No description generated for image {batch_start + i + 1}"
                            )
                    except Exception as e:
                        image_description = f"Error describing image: {e}"
                        img_item.content = image_description
                        st.write(
                            f"✗ Error describing image {batch_start + i + 1}: {e}"
                        )

        st.success("All descriptions generated! Displaying images...")
        st.rerun()
    else:
        # Display current batch of images with descriptions
        st.write(
            f"**Batch {current_batch_num} of {total_batches}: Images {batch_start + 1} to {batch_end} of {total}**"
        )
        st.progress((batch_end) / total)

        for i, img_item in enumerate(current_batch):
            st.write(
                f"**Image {batch_start + i + 1} of {total}** (from Slide {img_item.slide_number})"
            )
            st.image(
                Image.open(io.BytesIO(img_item.image_bytes)),
                use_container_width=True,
            )

            # Text area for each image with pre-generated description
            description = st.text_area(
                f"What is important about image {batch_start + i + 1}?",
                key=f"desc_{img_item.id}",
                value=img_item.content,
            )
            img_item.content = description
            st.write("---")

        # Navigation buttons for batch processing
        col1, col2, col3 = st.columns(3)

        with col1:
            if batch_start > 0:
                if st.button("Previous Batch", key="prev_batch"):
                    ss.current_image_index = max(0, batch_start - BATCH_SIZE)
                    st.rerun()

        with col2:
            if st.button("Save Batch", key="save_batch"):
                # Save all descriptions in current batch
                for img_item in current_batch:
                    if img_item.content:
                        img_item.content = img_item.content
                st.success("Batch saved!")

        with col3:
            if batch_end < total:
                if st.button("Next Batch", key="next_batch"):
                    ss.current_image_index = batch_end
                    st.rerun()
            else:
                # Verify all images have descriptions before finishing
                all_described = all(
                    img.content and img.content.lower() not in ['none', 'null', ''] 
                    for img in all_images
                )
                
                if all_described:
                    if st.button("Finish", key="finish"):
                        ss.app_stage = "build_quiz_rag"
                        st.rerun()
                else:
                    st.warning("Please ensure all images have descriptions before finishing.")
                    if st.button("Force Finish", key="force_finish"):
                        ss.app_stage = "build_quiz_rag"
                        st.rerun()

    
def process_quiz_rag():
    """Process the quiz and RAG"""
    st.header("📋 Process Quiz and RAG")
    
    # Add back button
    if st.button("← Back to Describe Images", key="quiz_back"):
        ss.app_stage = "describe_images"
        st.rerun()
    
    if 'presentation_metadata' not in ss:
        st.error("No presentation metadata found. Please upload a presentation first.")
        ss.app_stage = "upload_pptx"
        st.rerun()
        return
    
    presentation, collection_id = ss.presentation_metadata

    


    st.write(f"**Enter a name for the presentation:**")
    name = st.text_input("Name", value=presentation.name)

    if st.button("Create"):
        # Create RAG collection
        with st.spinner("Creating RAG collection..."):
            try:
                if collection_id:
                    ss.rag_core.remove_collection(collection_id)
            except Exception:
                pass
            collection_id = ss.rag_core.create_collection(presentation)        
            st.success(f"✅ RAG collection created: {collection_id}")
            
            # Save RAG quizzer to database
            quizzer_data = {
                'teacher_id': ss.current_user['id'],
                'name': name,
                'collection_id': collection_id,
                'presentation_name': presentation.name,
                'num_slides': len(presentation.slides),
                'num_text_items': sum(len([item for item in slide.items if item.type.value == 'text']) for slide in presentation.slides),
                'num_image_items': sum(len([item for item in slide.items if item.type.value == 'image']) for slide in presentation.slides),
                'slides': [{'slide_number': slide.slide_number, 'content': [item.content for item in slide.items]} for slide in presentation.slides]
            }
            
            quizzer_id = ss.homework_server.create_rag_quizzer(quizzer_data)
            if quizzer_id:
                st.success(f"✅ RAG quizzer saved to database with ID: {quizzer_id}")
            else:
                st.error("❌ Failed to save RAG quizzer to database")
            
            ss.app_stage = "dashboard"
            st.rerun()

    


def generate_homework():
    """Generate homework assignments"""
    st.header("📋 Generate Homework")
    st.write("Welcome to the generate homework page. Here you can generate homework assignments for your students.")

    # Load RAG quizzers from database
    rag_quizzers = ss.homework_server.get_rag_quizzers_by_teacher(ss.current_user['id'])
    

    
    if not rag_quizzers:
        st.warning("⚠️ No presentations uploaded yet. Please upload a PowerPoint file first.")
        if st.button("← Back to Dashboard", key="generate_back1"):
            ss.app_stage = "dashboard"
            st.rerun()
        return
    
    # Select presentation
    st.subheader("1) Select Presentation")
    selected_quizzer = st.selectbox(
        "Choose a presentation to generate homework from:",
        options=rag_quizzers,
        format_func=lambda x: x['name']
    )
    
    if selected_quizzer:
        st.write(f"**Currently Selected:** {selected_quizzer['name']}")
        
        # Homework generation options
        st.subheader("2) Homework Options")
        col1, col2 = st.columns(2)
        
        with col1:
            # Question count controls
            st.write("**Question Count:**")
            num_text_questions = st.number_input("Text questions", min_value=0, max_value=20, value=3)
            num_image_questions = st.number_input("Image questions", min_value=0, max_value=20, value=2)
            
            total_questions = num_text_questions + num_image_questions
            if total_questions == 0:
                st.warning("⚠️ Please specify at least one question type.")
            else:
                st.success(f"📊 Total questions: {total_questions}")
        
        # Generate homework button
        st.subheader("3) Generate Homework Assignment");
        if st.button("Generate"):
            with st.spinner("Generating homework questions..."):
                try:
                    # Create fresh RAG core and QuizMaster instances
                    rag_core = RAGCore()
                    if not rag_core.llm_model:
                        st.error("❌ Google API key not found or invalid. Please check your .env file.")
                        return
                    
                    quiz_master = QuizMaster(rag_core)
                    
                    # Generate questions based on specified counts
                    generated_questions = []
                    
                    # Generate text questions first
                    text_questions_generated = 0
                    for i in range(num_text_questions):
                        question = quiz_master.generate_text_question(selected_quizzer['collection_id'])
                        if question:
                            generated_questions.append(question)
                            text_questions_generated += 1
                    
                    # Generate image questions
                    image_questions_generated = 0
                    for i in range(num_image_questions):
                        question = quiz_master.generate_image_question(selected_quizzer['collection_id'])
                        if question:
                            generated_questions.append(question)
                            image_questions_generated += 1
                    
                    # Show generation summary
                    st.info(f"📊 Generated {text_questions_generated} text questions and {image_questions_generated} image questions")
                    
                    if generated_questions:
                        st.success(f"✅ Generated {len(generated_questions)} questions successfully!")
                        # Persist preview in session state for saving after rerun
                        ss.homework_preview = {
                            'collection_id': selected_quizzer['collection_id'],
                            'presentation_name': selected_quizzer['name'],
                            'questions': generated_questions,
                            'num_text_questions': text_questions_generated,
                            'num_image_questions': image_questions_generated,
                        }
                    else:
                        st.error("❌ Failed to generate any questions. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error generating homework: {e}")
                    st.exception(e)
    
        # If there is a preview in session state, render it and offer Save/Clear
        if ss.get('homework_preview'):
            preview = ss.homework_preview
            st.subheader("Generated Homework (Preview)")
            total_q = len(preview['questions'])
            st.write(f"**Questions:** {total_q}  —  Text: {preview['num_text_questions']}, Image: {preview['num_image_questions']}")
            st.write("---")
            for i, question_data in enumerate(preview['questions'], 1):
                st.write(f"**Question {i}:**")
                st.write(question_data["question"])
                if question_data["type"] == "image" and "image_bytes" in question_data:
                    try:
                        import base64
                        image_bytes = base64.b64decode(question_data["image_bytes"])
                        st.image(image_bytes, caption="Question Image", use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not display image: {e}")
                with st.expander(f"Answer {i}"):
                    st.write(f"**Answer:** {question_data['answer']}")
                    st.write(f"**Context:** {question_data['context'][:200]}...")
                st.write("---")

            st.write("**Enter a name for the homework assignment:**")
            name = st.text_input("Homework Name", value=preview['presentation_name'])
            if name:
                if st.button("💾 Save Homework Assignment", key="save_preview"):
                    homework_assignment = {
                        'collection_id': preview['collection_id'],
                        'teacher_id': ss.current_user['id'],  # Add teacher ID
                        'questions': preview['questions'],
                        'num_text_questions': preview['num_text_questions'],
                        'num_image_questions': preview['num_image_questions'],
                        'status': 'active',
                        'name': name,
                    }
                    
                    # When saving a new assignment, store only the assignment ID
                    assignment_id = ss.homework_server.create_assignment(homework_assignment)
                    if assignment_id:
                        print(f"🔍 assignment created successfully");
                        ss.homework_assignments.append(assignment_id)
                        st.success("✅ Homework assignment saved!")
                    else:
                        st.error("❌ Failed to create assignment!")
                    ss.homework_preview = None
                    st.rerun()

    # Back button
    if st.button("← Back to Dashboard", key="generate_back2"):
        ss.app_stage = "dashboard"
        st.rerun()


def manage_assignments():
    """Manage homework assignments"""
    st.header("📚 Manage Assignments")
    
    st.subheader("Current Assignments")
    
    # Fetch assignments for this teacher from DB
    assignments = ss.homework_server.get_assignments_by_teacher(ss.current_user['id'])
    
    if not assignments:
        st.info("📝 No homework assignments created yet.")
    else:
        for i, assignment in enumerate(assignments):
            with st.expander(f"📋 Assignment {i+1}: {assignment.get('name', 'Unnamed')}"):
                st.write(f"**Created:** {assignment.get('created_at', 'Unknown')}")
                st.write(f"**Total Questions:** {assignment.get('num_questions', 0)}")
                st.write(f"**Text Questions:** {assignment.get('num_text_questions', 0)}")
                st.write(f"**Image Questions:** {assignment.get('num_image_questions', 0)}")
                
                # Display questions if available
                if 'questions' in assignment and assignment['questions']:
                    st.write("**Questions:**")
                    for j, question_data in enumerate(assignment['questions'][:3], 1):  # Show first 3 questions
                        st.write(f"{j}. {question_data['question']}")
                        if question_data['type'] == 'image':
                            st.write("   📷 (Image question)")
                        st.write("")
                    if len(assignment['questions']) > 3:
                        st.write(f"... and {len(assignment['questions']) - 3} more questions")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📊 View Results", key=f"view_{i}"):
                        ss.selected_assignment_for_results = assignment
                        ss.app_stage = "view_results"
                        st.rerun()
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                        # Delete from DB
                        success = ss.homework_server.delete_assignment(assignment['id'])
                        if success:
                            st.success("✅ Assignment deleted!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to delete assignment.")
    # Back button
    if st.button("← Back to Dashboard", key="manage_back"):
        ss.app_stage = "dashboard"
        st.rerun()


def view_assignment_results():
    """View detailed results for a specific assignment"""
    assignment = ss.selected_assignment_for_results
    if not assignment:
        st.error("No assignment selected for results viewing.")
        ss.app_stage = "dashboard"
        st.rerun()
        return
    
    st.header(f"📊 Assignment Results: {assignment['name']}")
    st.caption(f"Assignment ID: {assignment['id']} | Created: {assignment.get('created_at', 'Unknown')}")
    
    # Get all submissions for this assignment
    submissions = ss.homework_server.get_all_submissions_for_assignment(assignment['id'])
    
    if not submissions:
        st.info("📝 No students have submitted this assignment yet.")
        if st.button("← Back to Manage Assignments", key="results_back1"):
            ss.app_stage = "manage_assignments"
            st.rerun()
        return
    
    # Display summary statistics
    completed_submissions = [s for s in submissions if s['status'] == 'completed']
    in_progress_submissions = [s for s in submissions if s['status'] == 'in_progress']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Submissions", len(submissions))
    with col2:
        st.metric("Completed", len(completed_submissions))
    with col3:
        st.metric("In Progress", len(in_progress_submissions))
    
    if completed_submissions:
        avg_score = sum(s['overall_score'] for s in completed_submissions) / len(completed_submissions)
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    st.markdown("---")
    
    # Display each student's submission
    for i, submission in enumerate(submissions):
        with st.expander(f"👤 {submission['first_name']} {submission['last_name']} ({submission['username']}) - {submission['status'].upper()}"):
            
            # Basic submission info
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Submission ID:** {submission['id']}")
                st.write(f"**Started:** {submission['started_at']}")
                if submission['completed_at']:
                    st.write(f"**Completed:** {submission['completed_at']}")
                st.write(f"**Status:** {submission['status']}")
            
            with col2:
                if submission['overall_score'] is not None:
                    st.write(f"**Final Score:** {submission['overall_score']}%")
                if submission['summary']:
                    st.write(f"**AI Summary:** {submission['summary']}")
            
            # Get detailed answers for this submission
            answers_by_q = ss.homework_server.get_submission_answers(submission['id'])
            
            if answers_by_q:
                st.write("**Detailed Answers:**")
                
                # Get assignment questions for reference
                assignment_questions = ss.homework_server.get_assignment_questions(assignment['id'])
                question_lookup = {q['id']: q for q in assignment_questions}
                
                for question_index, (qid, attempts) in enumerate(answers_by_q.items(), 1):
                    question = question_lookup.get(qid, {})
                    
                    with st.expander(f"Question {question_index}: {question.get('question', 'Unknown question')[:50]}..."):
                        st.write(f"**Question:** {question.get('question', 'Unknown question')}")
                        
                        if question.get('type') == 'image':
                            st.caption("📷 Image-based question")
                        
                        for attempt_num, attempt in enumerate(attempts, 1):
                            st.write(f"**Attempt {attempt_num}:**")
                            
                            st.write(f"**Answer:** {attempt['student_answer']}")
                            st.write(f"**Grade:** {attempt['grade']}/2")
                            if attempt['feedback']:
                                st.info(f"**Feedback:** {attempt['feedback']}")
                            st.write("---")
            else:
                st.info("No answers recorded for this submission.")
    
    # Back button
    if st.button("← Back to Manage Assignments", key="results_back2"):
        ss.app_stage = "manage_assignments"
        st.rerun()


def remove_powerpoint():
    """Remove PowerPoint presentations"""
    st.header("🗑️ Remove PowerPoint")
    
    # Load RAG quizzers from database
    rag_quizzers = ss.homework_server.get_rag_quizzers_by_teacher(ss.current_user['id'])
    
    if not rag_quizzers:
        st.warning("⚠️ No presentations to remove.")
        if st.button("← Back to Dashboard", key="remove_back1"):
            ss.app_stage = "dashboard"
            st.rerun()
        return
    
    st.subheader("Current Presentations")
    
    for i, rag_quizzer in enumerate(rag_quizzers):
        with st.expander(f"📄 {rag_quizzer['name']}"):
            st.write(f"**Slides:** {rag_quizzer['num_slides']}")
            st.write(f"**Text Items:** {rag_quizzer['num_text_items']}")
            st.write(f"**Images:** {rag_quizzer['num_image_items']}")
            
            # Warning about deletion
            st.warning("⚠️ This will permanently remove the presentation and all associated data.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    try:
                        # Remove from RAG core if collection exists
                        if ss.rag_core and rag_quizzer['collection_id']:
                            ss.rag_core.remove_collection(rag_quizzer['collection_id'])
                        
                        # Remove from database
                        success = ss.homework_server.delete_rag_quizzer(rag_quizzer['id'])
                        
                        if success:
                            st.success("✅ Presentation removed successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to remove presentation from database!")
                    except Exception as e:
                        st.error(f"❌ Error removing presentation: {e}")
            
            with col2:
                if st.button(f"📋 View Details", key=f"details_{i}"):
                    st.write("**Slide Details:**")
                    for slide in rag_quizzer.presentation.slides[:3]:  # Show first 3 slides
                        slide_texts = [item.content for item in slide.items if item.type.value == 'text']
                        slide_images = [item for item in slide.items if item.type.value == 'image']
                        st.write(f"Slide {slide.slide_number}: {len(slide_texts)} texts, {len(slide_images)} images")
    
    # Back button
    if st.button("← Back to Dashboard", key="remove_back"):
        ss.app_stage = "dashboard"
        st.rerun()

def dashboard():
    """Display the dashboard"""

    st.set_page_config(initial_sidebar_state="collapsed")

    st.header("📋 Dashboard")
    
    if st.button("Upload PPTX"):
        ss.app_stage = "upload_pptx"
        st.rerun()

    # Get count of presentations from database
    rag_quizzers = ss.homework_server.get_rag_quizzers_by_teacher(ss.current_user['id'])
    presentation_count = len(rag_quizzers)
    

    
    if presentation_count > 0:    
        if st.button(f"Generate Homework"):
            ss.app_stage = "generate_homework"
            st.rerun()
        if st.button(f"Manage Assignments"):
            ss.app_stage = "manage_assignments" 
            st.rerun()
        if st.button(f"Remove PowerPoint"):
            ss.app_stage = "remove_powerpoint"
            st.rerun()
    
    
    if st.button("🚪 Logout"):
        ss.current_user = None
        st.switch_page("main.py")
            


# Check if user is logged in and is a teacher
if not ss.current_user:
    st.error("❌ Please login first.")
    st.info("Redirecting to login page...")
    st.switch_page("main.py")
    st.stop()

if ss.current_user['role'] != 'teacher':
    st.error("❌ Access denied. This page is for teachers only.")
    st.info("Redirecting to login page...")
    st.switch_page("main.py")
    st.stop()



# Main app
st.title("🎓 Teacher Dashboard")
st.write(f"Welcome, {ss.current_user['first_name']} {ss.current_user['last_name']}!")


    

# Main content based on selected page
if ss.app_stage == "dashboard":
    dashboard()
elif ss.app_stage == "upload_pptx":
    upload_and_process_pptx()
elif ss.app_stage == "describe_images":
    describe_images()
elif ss.app_stage == "build_quiz_rag":
    process_quiz_rag()
elif ss.app_stage == "generate_homework":
    generate_homework()
elif ss.app_stage == "manage_assignments":
    manage_assignments()
elif ss.app_stage == "view_results":
    view_assignment_results()
elif ss.app_stage == "remove_powerpoint":
    remove_powerpoint()

# Footer
st.markdown("---")
st.write("**THIS PROJECT IS STILL IN DEVELOPMENT**")