import streamlit as st
import io
import json
import pandas as pd
from datetime import datetime
import sys
import os
from PIL import Image

# Add the current directory to the path to import our modules
sys.path.append(os.path.dirname(__file__))

from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.quiz_master import QuizMaster
from pptx_rag_quizzer.Image_server import ImageServer
from pptx_rag_quizzer.image_magic import ImageMagic

# Page configuration
st.set_page_config(
    page_title="Teacher Dashboard - Database Integration",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

ss = st.session_state

# Initialize session state
if 'current_uploads' not in ss:
    ss.current_uploads = []
if 'homework_assignments' not in ss:
    ss.homework_assignments = []
if 'rag_core' not in ss:
    ss.rag_core = None
if 'image_server' not in ss:
    ss.image_server = None
if 'image_magic' not in ss:
    ss.image_magic = None
if 'app_stage' not in ss:
    ss.app_stage = 'upload_pptx'

def initialize_services():
    """Initialize RAG core, image server, and image magic services"""
    try:
        if ss.rag_core is None:
            ss.rag_core = RAGCore()
            # Test if the LLM model is working
            if not ss.rag_core.llm_model:
                st.error("❌ Google API key not found or invalid. Please check your .env file.")
                return False
        if ss.image_server is None:
            ss.image_server = ImageServer()
        if ss.image_magic is None:
            # ImageMagic requires a RAGCore instance
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
                presentation = parse_powerpoint(file_object)
                
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
        # Initialize services if needed
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
        batch_ready = all(hasattr(img_item, 'content') and img_item.content for img_item in current_batch)

        if not batch_ready:
            # Show loading screen while generating descriptions
            st.write(f"**Processing {total} images in batches of 5**")
            st.progress((idx + 1) / total)
            st.write(
                    f"**Generating descriptions for images {batch_start + 1} to {batch_end}...**"
            )

            with st.spinner("AI is analyzing images and generating descriptions. This may take up to 1 minute per image..."):
                for i, img_item in enumerate(current_batch):
                        if not hasattr(img_item, 'content') or not img_item.content:
                            try:
                                st.write(
                                    f"Describing image {batch_start + i + 1} of {total}..."
                                )
                                image_description = ss.image_magic.describe_image(
                                    img_item.image_bytes,
                                    img_item.extension,
                                    img_item.slide_number
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
                    if st.button("Finish", key="finish"):
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
            if not hasattr(img_item, 'content') or not img_item.content:
                try:
                    st.write(f"Generating description for image {idx + 1}...")
                    image_description = ss.image_magic.describe_image(
                        img_item.image_bytes,
                        img_item.extension,
                        img_item.slide_number
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
            st.success("All images described!")
            ss.app_stage = "build_quiz_rag"
            st.rerun()



def current_uploads():  
    """Display current uploads"""
    st.header("📋 Current Uploads")
    
    if not ss.current_uploads:
        st.write("No uploads found")
        return

# Main app
st.title("🎓 Teacher Dashboard - Database Integration")
st.write("Manage PowerPoint uploads, process images, and create homework assignments.")

# Sidebar navigation
with st.sidebar:
    st.header("🧭 Navigation")
    
    page = st.radio(
        "Select Page:",
        [
            "📁 Upload PPTX",
            "📋 Current Uploads",
        ]
    )
    
    st.markdown("---")
    st.write("**System Status:**")
    
    # Service status
    if ss.rag_core:
        st.write("✅ RAG Core: Ready")
    else:
        st.write("❌ RAG Core: Not initialized")
    
    if ss.image_server:
        st.write("✅ Image Server: Ready")
    else:
        st.write("❌ Image Server: Not initialized")
    
    # Statistics
    st.write(f"**Uploads:** {len(ss.current_uploads)}")
    st.write(f"**Homework:** {len(ss.homework_assignments)}")
    
    # Reset button
    if st.button("🔄 Reset All Data"):
        ss.current_uploads = []
        ss.homework_assignments = []
        ss.rag_core = None
        ss.image_server = None
        ss.image_magic = None
        st.rerun()

# Main content based on selected page
if ss.app_stage == "upload_pptx":
    upload_and_process_pptx()
elif ss.app_stage == "describe_images":
    describe_images()
elif ss.app_stage == "current_uploads":
    current_uploads()

# Footer
st.markdown("---")
st.write("**Teacher Dashboard** - Database Integration Workflow")
st.write("Upload PPTX → Process Images → Create Homework → Manage Assignments")
