from pptx_rag_quizzer.rag_core import RAGCore
from pptx_rag_quizzer.file_parser import parse_powerpoint
from pptx_rag_quizzer.presentation_model import Presentation
import streamlit as st

st.title("RAG Test")

# Initialize session state
if 'collection_id' not in st.session_state:
    st.session_state.collection_id = None
if 'rag_core' not in st.session_state:
    st.session_state.rag_core = None

# Main test button
if st.button("Run Tests"):
    # Initialize RAG core
    with open("../scrambled_eggs_guide.pptx", "rb") as file:
        presentation = parse_powerpoint(file)

    rag_core = RAGCore()
    collection_id = rag_core.create_collection(presentation)
    
    # Store in session state
    st.session_state.collection_id = collection_id
    st.session_state.rag_core = rag_core
    
    st.write(f"Collection ID: {collection_id}")
    st.success("Collection created successfully!")

# Only show test buttons if collection exists
if st.session_state.collection_id and st.session_state.rag_core:
    st.subheader("Test Collection Functions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Test Collection Query"):
            results = st.session_state.rag_core.query_collection(
                collection_id=st.session_state.collection_id, 
                query_text="What is the main topic of the presentation?"
            )
            st.write("Query Results:")
            st.write(results["documents"][0])
    
    with col2:
        if st.button("Test Image Collection"):
            try:
                results = st.session_state.rag_core.get_random_slide_with_image(
                    collection_id=st.session_state.collection_id
                )
                st.write("Image Slide Results:")
                st.write(results["documents"])
            except Exception as e:
                st.error(f"Error getting image slide: {e}")
    
    with col3:
        if st.button("Test Text Collection"):
            results = st.session_state.rag_core.get_random_slide_context(
                collection_id=st.session_state.collection_id
            )
            st.write("Text Slide Results:")
            st.write(results["documents"][0])

    with col4:
        if st.button("Test Image Collection fd"):
            try:
                results = st.session_state.rag_core.get_context_from_slide_number(
                    collection_id=st.session_state.collection_id,
                    slide_number=1
                )
                st.write("Slide Results:")
                st.write(results["documents"])
            except Exception as e:
                st.error(f"Error getting slide: {e}")

# Clear button
if st.button("Clear Collection"):
    st.session_state.collection_id = None
    st.session_state.rag_core = None
    st.rerun()


        