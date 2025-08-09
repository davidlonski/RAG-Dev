from pptx_rag_quizzer.image_magic import ImageMagic
from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.file_parser import parse_powerpoint
import streamlit as st
import io
from PIL import Image as PILImage

st.title("Enhanced Image Magic Test")

# Initialize session state
if 'collection_id' not in st.session_state:
    st.session_state.collection_id = None
if 'rag_core' not in st.session_state:
    st.session_state.rag_core = None
if 'image_magic' not in st.session_state:
    st.session_state.image_magic = None

# Main setup button
if st.button("Setup RAG and Enhanced Image Magic"):
    try:
        # Initialize RAG core
        with open("../scrambled_eggs_guide.pptx", "rb") as file:
            presentation = parse_powerpoint(file)

        rag_core = RAGCore()
        collection_id = rag_core.create_collection(presentation)
        
        # Store in session state
        st.session_state.collection_id = collection_id
        st.session_state.rag_core = rag_core
        st.session_state.image_magic = ImageMagic(rag_core)
        
        st.write(f"Collection ID: {collection_id}")
        st.success("RAG Core and Enhanced Image Magic initialized successfully!")
        
    except Exception as e:
        st.error(f"Error setting up RAG and Image Magic: {e}")

# Only show test buttons if everything is initialized
if st.session_state.collection_id and st.session_state.rag_core and st.session_state.image_magic:
    st.subheader("Enhanced Image Magic Tests")
    
    # Create a sample image for testing
    def create_test_image():
        """Create a simple test image"""
        img = PILImage.new('RGB', (200, 200), color='red')
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer.getvalue()
    
    test_image_bytes = create_test_image()
    
    # Configuration section
    st.subheader("Configuration")
    col_config1, col_config2, col_config3 = st.columns(3)
    
    with col_config1:
        cache_ttl = st.slider("Cache TTL (seconds)", 300, 7200, 3600)
        if st.button("Set Cache TTL"):
            st.session_state.image_magic.set_cache_ttl(cache_ttl)
            st.success(f"Cache TTL set to {cache_ttl} seconds")
    
    with col_config2:
        max_history = st.slider("Max Chat History", 5, 20, 10)
        if st.button("Set Max Chat History"):
            st.session_state.image_magic.set_max_chat_history(max_history)
            st.success(f"Max chat history set to {max_history}")
    
    with col_config3:
        if st.button("Clear Chat History"):
            st.session_state.image_magic.clear_chat_history()
            st.success("Chat history cleared")
        
        if st.button("Clear Cache"):
            st.session_state.image_magic.clear_cache()
            st.success("Cache cleared")
    
    # Basic functionality tests
    st.subheader("Basic Functionality Tests")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Enhanced Image Description (with Chat)")
        if st.button("Test Enhanced Image Description"):
            try:
                description = st.session_state.image_magic.describe_image(
                    image_bytes=test_image_bytes,
                    image_format="png",
                    slide_number=1,
                    collection_id=st.session_state.collection_id,
                    use_chat=True
                )
                st.write("Enhanced Image Description:")
                st.write(description)
            except Exception as e:
                st.error(f"Error in enhanced image description: {e}")
    
    with col2:
        st.subheader("Image Description Without Chat")
        if st.button("Test Image Description Without Chat"):
            try:
                description = st.session_state.image_magic.describe_image(
                    image_bytes=test_image_bytes,
                    image_format="png",
                    slide_number=1,
                    collection_id=st.session_state.collection_id,
                    use_chat=False
                )
                st.write("Image Description (No Chat):")
                st.write(description)
            except Exception as e:
                st.error(f"Error in image description without chat: {e}")
    
    # Lambda Index tests
    st.subheader("Lambda Index Tests")
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("Test Lambda Index Context Retrieval"):
            try:
                context = st.session_state.image_magic.get_context_with_lambda_index(
                    enhanced_description="A red square image with cooking instructions",
                    collection_id=st.session_state.collection_id,
                    image_hash="test_hash",
                    n_results=3
                )
                st.write("Lambda Index Context:")
                st.write(context)
            except Exception as e:
                st.error(f"Error in Lambda Index context retrieval: {e}")
    
    with col4:
        if st.button("Test Lambda Index Stats"):
            try:
                stats = st.session_state.image_magic.get_lambda_index_stats()
                st.write("Lambda Index Statistics:")
                st.json(stats)
            except Exception as e:
                st.error(f"Error getting Lambda Index stats: {e}")
    
    # Chat functionality tests
    st.subheader("Chat Functionality Tests")
    col5, col6 = st.columns(2)
    
    with col5:
        if st.button("Test Chat History"):
            try:
                chat_history = st.session_state.image_magic.get_chat_history()
                st.write("Current Chat History:")
                for i, msg in enumerate(chat_history):
                    st.write(f"{i+1}. {msg}")
            except Exception as e:
                st.error(f"Error getting chat history: {e}")
    
    with col6:
        if st.button("Test Multiple Descriptions (Chat Continuity)"):
            try:
                # Create multiple test images
                images = []
                colors = ['red', 'blue', 'green']
                for color in colors:
                    img = PILImage.new('RGB', (200, 200), color=color)
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    images.append(img_buffer.getvalue())
                
                descriptions = []
                for i, img_bytes in enumerate(images):
                    desc = st.session_state.image_magic.describe_image(
                        image_bytes=img_bytes,
                        image_format="png",
                        slide_number=i+1,
                        collection_id=st.session_state.collection_id,
                        use_chat=True
                    )
                    descriptions.append(f"Image {i+1} ({colors[i]}): {desc}")
                
                st.write("Sequential Descriptions with Chat:")
                for desc in descriptions:
                    st.write(desc)
                    
            except Exception as e:
                st.error(f"Error in multiple descriptions test: {e}")
    
    # Database operations tests
    st.subheader("Database Operations")
    col7, col8 = st.columns(2)
    
    with col7:
        if st.button("Test Upload Image to Database"):
            try:
                image_id = st.session_state.image_magic.upload_image_to_database(test_image_bytes)
                if image_id:
                    st.success(f"Image uploaded successfully! Image ID: {image_id}")
                    st.session_state.test_image_id = image_id
                else:
                    st.error("Failed to upload image to database")
            except Exception as e:
                st.error(f"Error uploading image: {e}")
    
    with col8:
        if st.button("Test Retrieve Image from Database"):
            if hasattr(st.session_state, 'test_image_id'):
                try:
                    retrieved_image = st.session_state.image_magic.get_image_from_database(
                        st.session_state.test_image_id
                    )
                    if retrieved_image:
                        st.success("Image retrieved successfully!")
                        # Display the image
                        img = PILImage.open(io.BytesIO(retrieved_image))
                        st.image(img, caption="Retrieved Image", use_column_width=True)
                    else:
                        st.error("Failed to retrieve image from database")
                except Exception as e:
                    st.error(f"Error retrieving image: {e}")
            else:
                st.warning("Please upload an image first")
    
    # Individual method tests
    st.subheader("Individual Method Tests")
    col9, col10 = st.columns(2)
    
    with col9:
        if st.button("Test OCR Image"):
            try:
                ocr_text = st.session_state.image_magic.ocr_image(test_image_bytes)
                st.write("OCR Text:")
                st.write(ocr_text)
            except Exception as e:
                st.error(f"Error in OCR: {e}")
    
    with col10:
        if st.button("Test Enhanced Description with Chat"):
            try:
                enhanced_desc = st.session_state.image_magic.get_enhanced_description(
                    ocr_description="Sample OCR text",
                    image_bytes=test_image_bytes,
                    image_format="png",
                    slide_context="This is a test slide about cooking scrambled eggs.",
                    use_chat=True
                )
                st.write("Enhanced Description (with Chat):")
                st.write(enhanced_desc)
            except Exception as e:
                st.error(f"Error in enhanced description: {e}")
    
    # Final description test
    st.subheader("Final Description Test")
    if st.button("Test Final Description with Chat"):
        try:
            final_desc = st.session_state.image_magic.get_final_description_with_chat(
                enhanced_description="A red square image",
                context="This is retrieved context about cooking methods.",
                image_bytes=test_image_bytes,
                image_format="png",
                use_chat=True
            )
            st.write("Final Description (with Chat):")
            st.write(final_desc)
        except Exception as e:
            st.error(f"Error in final description: {e}")
    
    # Test with actual slide data
    st.subheader("Test with Real Slide Data")
    if st.button("Test with Real Slide Data (Enhanced)"):
        try:
            # Get a slide with image
            slide_data = st.session_state.rag_core.get_random_slide_with_image(
                st.session_state.collection_id
            )
            
            if slide_data:
                st.write("Found slide with image:")
                st.write(slide_data)
                
                # Extract image ID from metadata
                image_id = None
                metadata = slide_data["metadatas"]
                for key, value in metadata.items():
                    if key.endswith("_image_id"):
                        image_id = value
                        break
                
                if image_id:
                    # Get the image from database
                    image_bytes = st.session_state.image_magic.get_image_from_database(image_id)
                    if image_bytes:
                        # Describe the image with enhanced features
                        description = st.session_state.image_magic.describe_image(
                            image_bytes=image_bytes,
                            image_format="png",
                            slide_number=metadata.get("slide_number", 1),
                            collection_id=st.session_state.collection_id,
                            use_chat=True
                        )
                        st.write("Enhanced Image Description:")
                        st.write(description)
                        
                        # Display the image
                        img = PILImage.open(io.BytesIO(image_bytes))
                        st.image(img, caption="Slide Image", use_column_width=True)
                        
                        # Show Lambda Index stats
                        stats = st.session_state.image_magic.get_lambda_index_stats()
                        st.write("Lambda Index Stats:")
                        st.json(stats)
                    else:
                        st.error("Could not retrieve image from database")
                else:
                    st.error("No image ID found in metadata")
            else:
                st.error("No slide with image found")
                
        except Exception as e:
            st.error(f"Error testing with real slide data: {e}")
    
    # Performance comparison
    st.subheader("Performance Comparison")
    if st.button("Compare Performance (With vs Without Chat)"):
        try:
            import time
            
            # Test without chat
            start_time = time.time()
            desc_no_chat = st.session_state.image_magic.describe_image(
                image_bytes=test_image_bytes,
                image_format="png",
                slide_number=1,
                collection_id=st.session_state.collection_id,
                use_chat=False
            )
            time_no_chat = time.time() - start_time
            
            # Test with chat
            start_time = time.time()
            desc_with_chat = st.session_state.image_magic.describe_image(
                image_bytes=test_image_bytes,
                image_format="png",
                slide_number=1,
                collection_id=st.session_state.collection_id,
                use_chat=True
            )
            time_with_chat = time.time() - start_time
            
            st.write("Performance Comparison:")
            st.write(f"Without Chat: {time_no_chat:.2f} seconds")
            st.write(f"With Chat: {time_with_chat:.2f} seconds")
            st.write(f"Difference: {time_with_chat - time_no_chat:.2f} seconds")
            
            st.write("Description without chat:")
            st.write(desc_no_chat)
            st.write("Description with chat:")
            st.write(desc_with_chat)
            
        except Exception as e:
            st.error(f"Error in performance comparison: {e}")

# Clear button
if st.button("Clear All"):
    st.session_state.collection_id = None
    st.session_state.rag_core = None
    st.session_state.image_magic = None
    if hasattr(st.session_state, 'test_image_id'):
        del st.session_state.test_image_id
    st.rerun() 