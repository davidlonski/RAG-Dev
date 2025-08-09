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
from database.image_server import ImageServer
from pptx_rag_quizzer.image_magic import ImageMagic
from database.homework_server import HomeworkServer

# Page configuration
st.set_page_config(
    page_title="Teacher Dashboard - Database Integration",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

ss = st.session_state

# Initialize session state
if 'rag_core' not in ss:
    ss.rag_core = None
if 'homework_server' not in ss:
    ss.homework_server = None
if 'image_server' not in ss:
    ss.image_server = None
if 'image_magic' not in ss:
    ss.image_magic = None
if 'app_stage' not in ss:
    ss.app_stage = 'dashboard'
if 'rag_quizzer_list' not in ss:
    ss.rag_quizzer_list = []
if 'homework_assignments' not in ss:
    ss.homework_assignments = []
if 'homework_preview' not in ss:
    ss.homework_preview = None


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
            try:
                # Parse the PowerPoint file
                file_bytes = uploaded_file.read()
                file_object = io.BytesIO(file_bytes)
                presentation = parse_powerpoint(file_object, uploaded_file.name)
                
                # Display presentation info
                st.success(f"✅ PowerPoint file processed successfully!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Presentation Details:**")
                    st.write(f"**ID:** {presentation.id}")
                    st.write(f"**Slides:** {len(presentation.slides)}")
                    
                    # Count items
                    total_text = sum(len([item for item in slide.items if item.type.value == 'text']) for slide in presentation.slides)
                    total_images = sum(len([item for item in slide.items if item.type.value == 'image']) for slide in presentation.slides)
                    
                    st.write(f"**Text Items:** {total_text}")
                    st.write(f"**Images:** {total_images}")

                    # Show slide preview
                    with st.expander("📄 Slide Preview"):
                        for i, slide in enumerate(presentation.slides[:5]):  # Show first 5 slides
                            slide_texts = [item.content for item in slide.items if item.type.value == 'text']
                            slide_images = [item for item in slide.items if item.type.value == 'image']
                            
                            st.write(f"**Slide {slide.slide_number}** ({len(slide_texts)} texts, {len(slide_images)} images)")
                            for j, text in enumerate(slide_texts[:2]):  # Show first 2 texts
                                st.write(f"  Text {j+1}: {text[:100]}{'...' if len(text) > 100 else ''}")
                            if slide_images:
                                st.write(f"  Contains {len(slide_images)} image(s)")
                    
                    if len(presentation.slides) > 5:
                        st.write(f"... and {len(presentation.slides) - 5} more slides")
                
                with col2:
                    st.write("**Processing Options:**")
                    auto_describe = st.checkbox("Auto-describe images", value=True)
                    create_collection = st.checkbox("Create RAG collection", value=True)
                    
                    if st.button("🚀 Process Presentation", type="primary"):
                        process_presentation(presentation, auto_describe, create_collection)
                
                
                    
            except Exception as e:
                st.error(f"❌ Error processing PowerPoint file: {e}")

def process_presentation(presentation, auto_describe, create_collection):
    """Process the presentation and store in database"""
    try:
        
        if not initialize_services():
            return
        
        # Create RAG collection if requested
        collection_id = None
        if create_collection:
            with st.spinner("Creating RAG collection..."):
                collection_id = ss.rag_core.create_collection(presentation)
                st.success(f"✅ RAG collection created: {collection_id}")

        # Describe images
        if auto_describe:
            ss.presentation_metadata = (presentation, collection_id)
            ss.app_stage = "describe_images"
            st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error processing presentation: {e}")


def describe_images():
    """Describe images"""
    st.header("📋 Describe Images")
    
    if 'presentation_metadata' not in ss:
        st.error("No presentation metadata found. Please upload a presentation first.")
        ss.app_stage = "upload_pptx"
        st.rerun()
        return
    
    presentation, collection_id = ss.presentation_metadata

    all_images = [item for slide in presentation.slides for item in slide.items if item.type.value == 'image']
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

    if total > 6:   # Process images in batches of 5
        # Calculate the current batch
        batch_start = idx
        batch_end = min(idx + 5, total)
        current_batch = all_images[batch_start:batch_end]

        # Check if all images in current batch have descriptions
        batch_ready = all(img_item.content and img_item.content.lower() not in ['none', 'null', ''] for img_item in current_batch)

        if not batch_ready:
            # Show loading screen while generating descriptions
            st.write(f"**Processing {total} images in batches of 5**")
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
                            st.write(f"Raw description: {image_description}")
                            
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
                f"**Batch {batch_start // 5 + 1}: Images {batch_start + 1} to {batch_end} of {total}**"
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
                        ss.current_image_index = max(0, batch_start - 5)
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
    else:
        # Original single image processing for 6 or fewer images
        if idx < total:
            img_item = all_images[idx]
            st.progress((idx + 1) / total)
            st.write(
                f"**Image {idx + 1} of {total}** (from Slide {img_item.slide_number})"
            )
            st.image(
                Image.open(io.BytesIO(img_item.image_bytes)),
                use_container_width=True,
            )

            # Only generate description if it doesn't already exist
            if not img_item.content or img_item.content.lower() in ['none', 'null', '']:
                try:
                    st.write(f"Generating description for image {idx + 1}...")
                    image_description = ss.image_magic.describe_image(
                        img_item.image_bytes,
                        img_item.extension,
                        img_item.slide_number,
                        collection_id
                    )
                    st.write(f"Raw description: {image_description}")
                    
                    if image_description and image_description != "None":
                        img_item.content = image_description
                        st.success(f"✓ Description generated successfully")
                    else:
                        img_item.content = "No description available"
                        st.warning("⚠️ No description generated")
                        
                except Exception as e:
                    st.error(f"Error describing image {idx + 1}: {e}")
                    img_item.content = f"Error: {e}"
            else:
                image_description = img_item.content

            description = st.text_area(
                "What is important about this image?",
                key=f"desc_{img_item.id}",
                value=image_description,
            )

            if st.button("Submit Description", key=f"submit_{idx}"):
                if description:
                    # Update description in the image object
                    img_item.content = description
                    ss.current_image_index += 1
                    st.rerun()
                else:
                    st.warning("Please provide a description.")
        else:
            # Verify all images have descriptions before transitioning
            all_described = all(
                img.content and img.content.lower() not in ['none', 'null', ''] 
                for img in all_images
            )
            
            if all_described:
                st.success("All images described!")
                ss.app_stage = "build_quiz_rag"
                st.rerun()
            else:
                st.warning("Please ensure all images have descriptions before proceeding.")
                if st.button("Force Continue", key="force_continue"):
                    ss.app_stage = "build_quiz_rag"
                    st.rerun()

    
def process_quiz_rag():
    """Process the quiz and RAG"""
    st.header("📋 Process Quiz and RAG")
    
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
            
            ss.rag_quizzer_list.append(RAG_quizzer(
                id=str(uuid.uuid4()),
                name=name,
                collection_id=collection_id,
                presentation=presentation
            ))
            st.success(f"✅ RAG quizzer saved: {name}")
            ss.app_stage = "dashboard"
            st.rerun()

    


def generate_homework():
    """Generate homework assignments"""
    st.header("📋 Generate Homework")

    if len(ss.rag_quizzer_list) == 0:
        st.warning("⚠️ No presentations uploaded yet. Please upload a PowerPoint file first.")
        if st.button("← Back to Dashboard"):
            ss.app_stage = "dashboard"
            st.rerun()
        return
    
    # Select presentation
    st.subheader("Select Presentation")
    selected_quizzer = st.selectbox(
        "Choose a presentation to generate homework from:",
        options=ss.rag_quizzer_list,
        format_func=lambda x: x.name
    )
    
    if selected_quizzer:
        st.write(f"**Selected:** {selected_quizzer.name}")
        st.write(f"**Slides:** {len(selected_quizzer.presentation.slides)}")
        
        # Homework generation options
        st.subheader("Homework Options")
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
        if st.button("🎯 Generate Homework Assignment"):
            with st.spinner("Generating homework questions..."):
                try:
                    # Initialize QuizMaster if not already done
                    if 'quiz_master' not in ss:
                        ss.quiz_master = QuizMaster(ss.rag_core)
                    
                    # Generate questions based on specified counts
                    generated_questions = []
                    
                    # Generate text questions first
                    text_questions_generated = 0
                    for i in range(num_text_questions):
                        question = ss.quiz_master.generate_text_question(selected_quizzer.collection_id)
                        if question:
                            generated_questions.append(question)
                            text_questions_generated += 1
                    
                    # Generate image questions
                    image_questions_generated = 0
                    for i in range(num_image_questions):
                        question = ss.quiz_master.generate_image_question(selected_quizzer.collection_id)
                        if question:
                            generated_questions.append(question)
                            image_questions_generated += 1
                    
                    # Show generation summary
                    st.info(f"📊 Generated {text_questions_generated} text questions and {image_questions_generated} image questions")
                    
                    if generated_questions:
                        st.success(f"✅ Generated {len(generated_questions)} questions successfully!")
                        # Persist preview in session state for saving after rerun
                        ss.homework_preview = {
                            'collection_id': selected_quizzer.collection_id,
                            'presentation_name': selected_quizzer.name,
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
            st.write(f"**Assignment:** {preview['presentation_name']}")
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

            save_col, clear_col = st.columns(2)
            with save_col:
                st.write("**Enter a name for the homework assignment:**")
                name = st.text_input("Homework Name", value=preview['presentation_name'])
                if name:
                    if st.button("💾 Save Homework Assignment", key="save_preview"):
                        homework_assignment = {
                            'collection_id': preview['collection_id'],
                            'questions': preview['questions'],
                            'num_text_questions': preview['num_text_questions'],
                            'num_image_questions': preview['num_image_questions'],
                            'status': 'active',
                            'name': name,
                        }
                        # When saving a new assignment, store only the assignment ID
                        assignment_id = ss.homework_server.create_assignment(homework_assignment)
                        if assignment_id:
                            print(f"🔍 assignment created successfully")
                            ss.homework_assignments.append(assignment_id)
                        ss.homework_preview = None
                        st.success("✅ Homework assignment saved!")
                        st.rerun()
            with clear_col:
                if st.button("🧹 Clear Preview", key="clear_preview"):
                    ss.homework_preview = None
                    st.info("Preview cleared.")

    # Back button
    if st.button("← Back to Dashboard"):
        ss.app_stage = "dashboard"
        st.rerun()


def manage_assignments():
    """Manage homework assignments"""
    st.header("📚 Manage Assignments")
    print(f"🔍 ss.homework_assignments: {ss.homework_assignments}")
    
    if len(ss.rag_quizzer_list) == 0:
        st.warning("⚠️ No presentations uploaded yet. Please upload a PowerPoint file first.")
        if st.button("← Back to Dashboard"):
            ss.app_stage = "dashboard"
            st.rerun()
        return
    
    st.subheader("Current Assignments")
    
    if len(ss.homework_assignments) == 0:
        st.info("📝 No homework assignments created yet.")
    else:
        # Fetch assignments from DB using HomeworkServer
        assignments = []
        for assignment_id in ss.homework_assignments:
            print(f"🔍 fetching assignment_id: {assignment_id} (type: {type(assignment_id)})")
            assignment = ss.homework_server.get_assignment(assignment_id, include_questions=True)
            print(f"🔍 assignment fetched: {assignment}")
            if assignment:
                assignments.append(assignment)
            else:
                print(f"❌ Assignment with ID {assignment_id} not found in DB.")
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
                        st.info("Results viewing feature coming soon!")
                with col2:
                    if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                        # Delete from DB and session
                        ss.homework_server.delete_assignment(assignment['id'])
                        ss.homework_assignments.pop(i)
                        st.success("✅ Assignment deleted!")
                        st.rerun()
    # Back button
    if st.button("← Back to Dashboard", key="manage_back"):
        ss.app_stage = "dashboard"
        st.rerun()


def remove_powerpoint():
    """Remove PowerPoint presentations"""
    st.header("🗑️ Remove PowerPoint")
    
    if len(ss.rag_quizzer_list) == 0:
        st.warning("⚠️ No presentations to remove.")
        if st.button("← Back to Dashboard"):
            ss.app_stage = "dashboard"
            st.rerun()
        return
    
    st.subheader("Current Presentations")
    
    for i, rag_quizzer in enumerate(ss.rag_quizzer_list):
        with st.expander(f"📄 {rag_quizzer.name}"):
            st.write(f"**ID:** {rag_quizzer.id}")
            st.write(f"**Slides:** {len(rag_quizzer.presentation.slides)}")
            st.write(f"**Collection ID:** {rag_quizzer.collection_id}")
            
            # Count items
            total_text = sum(len([item for item in slide.items if item.type.value == 'text']) for slide in rag_quizzer.presentation.slides)
            total_images = sum(len([item for item in slide.items if item.type.value == 'image']) for slide in rag_quizzer.presentation.slides)
            
            st.write(f"**Text Items:** {total_text}")
            st.write(f"**Images:** {total_images}")
            
            # Warning about deletion
            st.warning("⚠️ This will permanently remove the presentation and all associated data.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    try:
                        # Remove from RAG core if collection exists
                        if ss.rag_core and rag_quizzer.collection_id:
                            ss.rag_core.remove_collection(rag_quizzer.collection_id)
                        
                        # Remove from session state
                        ss.rag_quizzer_list.pop(i)
                        
                        st.success("✅ Presentation removed successfully!")
                        st.rerun()
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
    st.header("📋 Dashboard")
    
    if st.button("Upload PPTX"):
        ss.app_stage = "upload_pptx"
        st.rerun()

    if len(ss.rag_quizzer_list) > 0:    
        if st.button(f"Generate Homework"):
            ss.app_stage = "generate_homework"
            st.rerun()
        if st.button(f"Manage Assignments"):
            ss.app_stage = "manage_assignments" 
            st.rerun()
        if st.button(f"Remove PowerPoint"):
            ss.app_stage = "remove_powerpoint"
            st.rerun()
            


# Main app
st.title("🎓 Teacher Dashboard - Database Integration")
st.write("Manage PowerPoint uploads, process images, and create homework assignments.")

# Sidebar navigation
with st.sidebar:
    st.header("🧭 Navigation")
    
    # Show current stage
    st.write(f"**Current Stage:** {ss.app_stage.replace('_', ' ').title()}")
    
    # Statistics
    st.write(f"**Uploads:** {len(ss.rag_quizzer_list)}")
    st.write(f"**Assignments:** {len(ss.homework_assignments)}")
    
    # Reset button
    if st.button("🔄 Reset All Data"):
        ss.current_uploads = []
        ss.homework_assignments = []
        ss.rag_core = None
        ss.image_server = None
        ss.image_magic = None
        st.rerun()

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
elif ss.app_stage == "remove_powerpoint":
    remove_powerpoint()

# Footer
st.markdown("---")
st.write("**Teacher Dashboard** - Database Integration Workflow")
st.write("Upload PPTX → Process Images → Create Homework → Manage Assignments")
