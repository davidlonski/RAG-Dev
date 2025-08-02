import streamlit as st
import io
import base64
import json
from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.quiz_master import QuizMaster
from pptx_rag_quizzer.Image_server import ImageServer

# Page configuration
st.set_page_config(
    page_title="Quiz Master Test",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if 'rag_core' not in st.session_state:
    st.session_state.rag_core = None
if 'quiz_master' not in st.session_state:
    st.session_state.quiz_master = None
if 'collection_id' not in st.session_state:
    st.session_state.collection_id = None
if 'presentation' not in st.session_state:
    st.session_state.presentation = None
if 'image_server' not in st.session_state:
    st.session_state.image_server = None

def create_test_collection():
    """Create a test collection from uploaded PowerPoint file"""
    try:
        uploaded_file = st.file_uploader(
            "Upload PowerPoint file (.pptx)",
            type=['pptx'],
            help="Select a PowerPoint file to create a collection from"
        )
        
        if uploaded_file is not None:
            with st.spinner("Parsing PowerPoint file..."):
                # Parse the PowerPoint file
                file_bytes = uploaded_file.read()
                file_object = io.BytesIO(file_bytes)
                presentation = parse_powerpoint(file_object)
                
                # Store presentation in session state
                st.session_state.presentation = presentation
                
                # Display presentation info
                st.success(f"✅ PowerPoint file parsed successfully!")
                st.write(f"**Presentation ID:** {presentation.id}")
                st.write(f"**Number of slides:** {len(presentation.slides)}")
                
                # Count text and image items
                total_text = sum(len([item for item in slide.items if item.type.value == 'text']) for slide in presentation.slides)
                total_images = sum(len([item for item in slide.items if item.type.value == 'image']) for slide in presentation.slides)
                
                st.write(f"**Total text items:** {total_text}")
                st.write(f"**Total images:** {total_images}")
                
                # Show slide preview
                st.write("**Slide Preview:**")
                for i, slide in enumerate(presentation.slides[:3]):  # Show first 3 slides
                    slide_texts = [item.content for item in slide.items if item.type.value == 'text']
                    slide_images = [item for item in slide.items if item.type.value == 'image']
                    
                    with st.expander(f"Slide {slide.slide_number} ({len(slide_texts)} texts, {len(slide_images)} images)"):
                        for j, text in enumerate(slide_texts[:2]):  # Show first 2 texts
                            st.write(f"Text {j+1}: {text[:100]}{'...' if len(text) > 100 else ''}")
                        if slide_images:
                            st.write(f"Contains {len(slide_images)} image(s)")
                
                if len(presentation.slides) > 3:
                    st.write(f"... and {len(presentation.slides) - 3} more slides")
                
                return presentation
                
    except Exception as e:
        st.error(f"❌ Error parsing PowerPoint file: {e}")
        return None

def setup_rag_and_quiz_master(presentation):
    """Setup RAG core and quiz master with the presentation"""
    try:
        with st.spinner("Setting up RAG core and creating collection..."):
            # Initialize RAG core
            rag_core = RAGCore()
            st.session_state.rag_core = rag_core
            
            # Create collection from presentation
            collection_id = rag_core.create_collection(presentation)
            st.session_state.collection_id = collection_id
            
            # Initialize quiz master
            quiz_master = QuizMaster(rag_core)
            st.session_state.quiz_master = quiz_master
            
            # Initialize image server
            image_server = ImageServer()
            st.session_state.image_server = image_server
            
            st.success(f"✅ Collection created successfully!")
            st.write(f"**Collection ID:** {collection_id}")
            
            return True
            
    except Exception as e:
        st.error(f"❌ Error setting up RAG and Quiz Master: {e}")
        return False

def test_text_question_generation():
    """Test text question generation"""
    st.subheader("📝 Text Question Generation Test")
    
    if st.button("🎲 Generate Text Question", key="generate_text"):
        if st.session_state.quiz_master and st.session_state.collection_id:
            with st.spinner("Generating text question..."):
                try:
                    question_data = st.session_state.quiz_master.generate_text_question(
                        st.session_state.collection_id
                    )
                    
                    if question_data:
                        st.success("✅ Text question generated successfully!")
                        
                        # Display question data
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Question:**")
                            st.write(question_data['question'])
                            
                            st.write("**Answer:**")
                            st.write(question_data['answer'])
                        
                        with col2:
                            st.write("**Question Type:**")
                            st.write(question_data['type'])
                            
                            st.write("**Context (first 200 chars):**")
                            context = question_data['context']
                            if isinstance(context, str):
                                st.write(context[:200] + "..." if len(context) > 200 else context)
                            else:
                                st.write(str(context)[:200] + "...")
                        
                        # Show full context in expander
                        with st.expander("📄 Full Context"):
                            st.write(question_data['context'])
                            
                    else:
                        st.error("❌ Failed to generate text question")
                        
                except Exception as e:
                    st.error(f"❌ Error generating text question: {e}")
        else:
            st.error("❌ Quiz master or collection not initialized")

def test_image_question_generation():
    """Test image question generation"""
    st.subheader("🖼️ Image Question Generation Test")
    
    if st.button("🎲 Generate Image Question", key="generate_image"):
        if st.session_state.quiz_master and st.session_state.collection_id:
            with st.spinner("Generating image question..."):
                try:
                    question_data = st.session_state.quiz_master.generate_image_question(
                        st.session_state.collection_id
                    )
                    
                    if question_data:
                        st.success("✅ Image question generated successfully!")
                        
                        # Display question data
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Question:**")
                            st.write(question_data['question'])
                            
                            st.write("**Answer:**")
                            st.write(question_data['answer'])
                        
                        with col2:
                            st.write("**Question Type:**")
                            st.write(question_data['type'])
                            
                            st.write("**Image Extension:**")
                            st.write(question_data['image_extension'])
                            
                            st.write("**Image Size:**")
                            image_bytes = base64.b64decode(question_data['image_bytes'])
                            st.write(f"{len(image_bytes):,} bytes")
                        
                        # Display the image
                        st.write("**Question Image:**")
                        try:
                            image_bytes = base64.b64decode(question_data['image_bytes'])
                            st.image(image_bytes, caption="Question Image", use_container_width=True)
                        except Exception as e:
                            st.error(f"❌ Error displaying image: {e}")
                        
                        # Show context in expander
                        with st.expander("📄 Context"):
                            st.write(question_data['context'])
                            
                    else:
                        st.error("❌ Failed to generate image question")
                        
                except Exception as e:
                    st.error(f"❌ Error generating image question: {e}")
        else:
            st.error("❌ Quiz master or collection not initialized")

def test_batch_question_generation():
    """Test batch question generation"""
    st.subheader("📚 Batch Question Generation Test")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_text_questions = st.number_input(
            "Number of text questions",
            min_value=1,
            max_value=10,
            value=3,
            key="num_text"
        )
        
        num_image_questions = st.number_input(
            "Number of image questions", 
            min_value=0,
            max_value=10,
            value=2,
            key="num_image"
        )
    
    with col2:
        if st.button("🎲 Generate Batch Questions", key="generate_batch"):
            if st.session_state.quiz_master and st.session_state.collection_id:
                with st.spinner("Generating batch questions..."):
                    try:
                        all_questions = []
                        
                        # Generate text questions
                        for i in range(num_text_questions):
                            with st.spinner(f"Generating text question {i+1}/{num_text_questions}..."):
                                question_data = st.session_state.quiz_master.generate_text_question(
                                    st.session_state.collection_id
                                )
                                if question_data:
                                    all_questions.append(question_data)
                        
                        # Generate image questions
                        for i in range(num_image_questions):
                            with st.spinner(f"Generating image question {i+1}/{num_image_questions}..."):
                                question_data = st.session_state.quiz_master.generate_image_question(
                                    st.session_state.collection_id
                                )
                                if question_data:
                                    all_questions.append(question_data)
                        
                        if all_questions:
                            st.success(f"✅ Generated {len(all_questions)} questions successfully!")
                            
                            # Display all questions
                            for i, question in enumerate(all_questions):
                                with st.expander(f"Question {i+1} ({question['type']})"):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write("**Question:**")
                                        st.write(question['question'])
                                        
                                        st.write("**Answer:**")
                                        st.write(question['answer'])
                                    
                                    with col2:
                                        st.write("**Type:**")
                                        st.write(question['type'])
                                        
                                        if question['type'] == 'image':
                                            st.write("**Image Extension:**")
                                            st.write(question['image_extension'])
                                            
                                            # Display image
                                            try:
                                                image_bytes = base64.b64decode(question['image_bytes'])
                                                st.image(image_bytes, caption=f"Question {i+1} Image", width=200)
                                            except Exception as e:
                                                st.error(f"Error displaying image: {e}")
                                    
                                    # Show context
                                    with st.expander("📄 Context"):
                                        st.write(question['context'])
                            
                            # Download JSON
                            quiz_json = {
                                "quiz_info": {
                                    "total_questions": len(all_questions),
                                    "text_questions": len([q for q in all_questions if q['type'] == 'text']),
                                    "image_questions": len([q for q in all_questions if q['type'] == 'image']),
                                    "generated_at": str(st.session_state.get('generated_at', 'unknown'))
                                },
                                "questions": all_questions
                            }
                            
                            st.download_button(
                                label="📥 Download Quiz JSON",
                                data=json.dumps(quiz_json, indent=2),
                                file_name="quiz_questions.json",
                                mime="application/json"
                            )
                            
                        else:
                            st.error("❌ Failed to generate any questions")
                            
                    except Exception as e:
                        st.error(f"❌ Error generating batch questions: {e}")
            else:
                st.error("❌ Quiz master or collection not initialized")

def test_collection_info():
    """Test and display collection information"""
    st.subheader("📊 Collection Information")
    
    if st.session_state.collection_id and st.session_state.rag_core:
        try:
            # Get collection info
            collection = st.session_state.rag_core.chroma_client.get_collection(
                st.session_state.collection_id
            )
            
            # Get collection count
            count = collection.count()
            
            st.write(f"**Collection ID:** {st.session_state.collection_id}")
            st.write(f"**Total documents:** {count}")
            
            # Test random slide context
            if st.button("🎲 Test Random Slide Context", key="test_context"):
                with st.spinner("Getting random slide context..."):
                    try:
                        context_data = st.session_state.rag_core.get_random_slide_context(
                            st.session_state.collection_id
                        )
                        
                        if context_data:
                            st.success("✅ Random slide context retrieved!")
                            
                            with st.expander("📄 Random Slide Context"):
                                if isinstance(context_data, dict):
                                    st.write("**Document:**")
                                    st.write(context_data.get('documents', []))
                                    
                                    st.write("**Metadata:**") 
                                    st.json(context_data.get('metadatas', []))
                                else:
                                    st.write(context_data)
                        else:
                            st.error("❌ Failed to get random slide context")
                            
                    except Exception as e:
                        st.error(f"❌ Error getting random slide context: {e}")
            
            # Test random slide with image
            if st.button("🎲 Test Random Slide with Image", key="test_image_context"):
                with st.spinner("Getting random slide with image..."):
                    try:
                        image_context_data = st.session_state.rag_core.get_random_slide_with_image(
                            st.session_state.collection_id
                        )
                        
                        if image_context_data:
                            st.success("✅ Random slide with image retrieved!")
                            
                            with st.expander("📄 Random Slide with Image"):
                                if isinstance(image_context_data, dict):
                                    st.write("**Document:**")
                                    st.write(image_context_data.get('documents', []))
                                    
                                    st.write("**Metadata:**")
                                    st.json(image_context_data.get('metadatas', []))
                                else:
                                    st.write(image_context_data)
                        else:
                            st.error("❌ Failed to get random slide with image")
                            
                    except Exception as e:
                        st.error(f"❌ Error getting random slide with image: {e}")
                            
        except Exception as e:
            st.error(f"❌ Error getting collection info: {e}")
    else:
        st.warning("⚠️ No collection initialized")

# Main app
st.title("🎓 Quiz Master Test Application")
st.write("Upload a PowerPoint file and test the quiz master functions!")

# Sidebar for setup
with st.sidebar:
    st.header("⚙️ Setup")
    
    if st.button("🔄 Reset All", key="reset"):
        st.session_state.rag_core = None
        st.session_state.quiz_master = None
        st.session_state.collection_id = None
        st.session_state.presentation = None
        st.session_state.image_server = None
        st.rerun()
    
    st.write("**Current Status:**")
    if st.session_state.presentation:
        st.write("✅ Presentation loaded")
    else:
        st.write("❌ No presentation")
        
    if st.session_state.collection_id:
        st.write("✅ Collection created")
    else:
        st.write("❌ No collection")
        
    if st.session_state.quiz_master:
        st.write("✅ Quiz master ready")
    else:
        st.write("❌ Quiz master not ready")

# Main content
if not st.session_state.presentation:
    st.header("📁 Step 1: Upload PowerPoint File")
    presentation = create_test_collection()
    
    if presentation:
        st.session_state.presentation = presentation
        st.rerun()

elif not st.session_state.collection_id:
    st.header("🔧 Step 2: Setup RAG and Quiz Master")
    if st.button("🚀 Setup RAG and Quiz Master"):
        success = setup_rag_and_quiz_master(st.session_state.presentation)
        if success:
            st.rerun()

else:
    st.header("🎯 Step 3: Test Quiz Master Functions")
    
    # Create tabs for different test functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Text Questions", 
        "🖼️ Image Questions", 
        "📚 Batch Generation",
        "📊 Collection Info"
    ])
    
    with tab1:
        test_text_question_generation()
    
    with tab2:
        test_image_question_generation()
    
    with tab3:
        test_batch_question_generation()
    
    with tab4:
        test_collection_info()

# Footer
st.markdown("---")
st.write("**Quiz Master Test Application** - Test all quiz master functions with your PowerPoint files!")
