# RAG Workflows Description

This document describes the three Retrieval-Augmented Generation (RAG) workflows implemented in the RAG-Dev project, as defined in the workflow.drawio file under the "Lang chain, Llamraindex" page.

## Overview

The project implements three distinct RAG workflows that handle different types of input data and processing requirements:

1. **Unified Text-Image RAG Workflow** - Handles both text and image inputs with unified vector space
2. **Text-Only RAG Workflow** - Processes text-only inputs with separate image query handling
3. **Multi-Modal RAG Workflow** - Advanced workflow with OCR, slide context, and image data integration

---

## Workflow 1: Unified Text-Image RAG Workflow

### Purpose
This workflow creates a unified vector space that can handle both text and image inputs, allowing for seamless retrieval regardless of input type.

### Process Flow

1. **Input Data Processing**
   - Input data is split into two streams: text and images
   - Text data goes directly to text embedding
   - Images are processed through image-to-text conversion

2. **Image Processing Pipeline**
   - Images → Image to Text conversion
   - Image to Text → Gemini API for description
   - Gemini API → Text Description
   - Text Description → Text Embedding

3. **Text Processing Pipeline**
   - Text → Text Embedding
   - Text Embedding → Unified Text Vector Space

4. **Unified Vector Space**
   - Both image descriptions and text content are embedded into the same vector space
   - This allows for cross-modal retrieval

5. **Query Processing**
   - User Query → Query Embedding
   - Query Embedding → Retrieval
   - Retrieval → Retrieved Content

6. **Response Generation**
   - Retrieved Content → Type Classification (MLLM vs LLM)
   - Based on content type:
     - MLLM → Generated Response
     - LLM → Generated Response

### Key Features
- **Unified Vector Space**: Both text and image content share the same embedding space
- **Multi-Modal Retrieval**: Can retrieve relevant content regardless of whether the query relates to text or images
- **Flexible Response Generation**: Uses different LLM types based on retrieved content

---

## Workflow 2: Text-Only RAG Workflow

### Purpose
This workflow is optimized for text-only processing with separate handling for image queries, providing a more streamlined approach for text-heavy applications.

### Process Flow

1. **Input Data Processing**
   - Input data is split into text and images
   - Text data is processed through the main pipeline
   - Images are handled separately for query processing

2. **Text Processing Pipeline**
   - Text → Text Embedding
   - Text Embedding → Text Vector Space
   - Text Vector Space → Retrieval

3. **Image Query Processing**
   - Images → Image Query
   - Image Query → Gemini API
   - Gemini API → Query Embedding
   - Query Embedding → Retrieval

4. **Retrieval and Response**
   - Retrieval → Retrieved Content
   - Retrieved Content → LLM
   - LLM → Generated Response

5. **Image Metadata Processing**
   - Generated Response → Image Metadata
   - Image Metadata → Text Description
   - Text Description → Text Embedding
   - Text Embedding → Unified Text Vector Space

### Key Features
- **Separate Image Handling**: Images are processed separately from the main text pipeline
- **Text-Optimized**: Primary focus on text processing with image support as secondary
- **Metadata Integration**: Image descriptions are converted to text and added to the vector space

---

## Workflow 3: Multi-Modal RAG Workflow

### Purpose
This is the most advanced workflow that integrates OCR, slide context, and image data to provide comprehensive multi-modal understanding and retrieval.

### Process Flow

1. **Input Data Processing**
   - Input data is split into text and images
   - Text data follows the standard embedding pipeline
   - Images undergo advanced processing

2. **Text Processing Pipeline**
   - Text → Text Embedding
   - Text Embedding → Text Vector Space
   - Text Vector Space → Retrieval

3. **Advanced Image Processing**
   - Images → Slide Number identification
   - Images → OCR processing
   - OCR → Query Embedding
   - Query Embedding → Retrieval

4. **Context Integration**
   - Combined OCR, Full Slide Context, and Image Data → Query Embedding
   - Query Embedding → Retrieval

5. **Response Generation**
   - Retrieved Content → LLM
   - LLM → Generated Response

6. **Multi-Modal Response Processing**
   - Generated Response → Combined Context (slide context, OCR, image data)
   - Combined Context → Gemini API
   - Gemini API → Response
   - Response → Text Description
   - Text Description → Text Embedding
   - Text Embedding → Unified Text Vector Space

7. **Query Processing**
   - User Query → Query Embedding
   - Query Embedding → Retrieval
   - Retrieval → Retrieved Content
   - Retrieved Content → LLM
   - LLM → Generated Response

### Key Features
- **OCR Integration**: Extracts text from images for better understanding
- **Slide Context**: Incorporates slide-specific context for better relevance
- **Multi-Layer Processing**: Combines multiple data sources for comprehensive understanding
- **Advanced Context Integration**: Merges OCR, slide context, and image data for rich retrieval

---

## Technical Implementation Details

### Common Components Across Workflows

1. **Embedding Generation**
   - All workflows use text embedding for vector space creation
   - Unified vector spaces allow cross-modal retrieval

2. **Retrieval Mechanism**
   - Vector similarity search for content retrieval
   - Support for both text and image-based queries

3. **Response Generation**
   - LLM-based response generation
   - Support for both MLLM and standard LLM based on content type

4. **Gemini API Integration**
   - Used for image description and analysis
   - Provides multi-modal understanding capabilities

### Workflow Selection Criteria

- **Workflow 1**: Use when you need unified handling of text and images with equal importance
- **Workflow 2**: Use when text is primary and images are secondary
- **Workflow 3**: Use when you need comprehensive multi-modal understanding with OCR and context

### Performance Considerations

- **Workflow 1**: Balanced performance with unified processing
- **Workflow 2**: Optimized for text-heavy applications
- **Workflow 3**: Most comprehensive but computationally intensive

---

## Integration with RAG-Dev Project

These workflows are implemented in the RAG-Dev project using:

- **ChromaDB**: For vector storage and retrieval
- **Gemini LLM API**: For multi-modal understanding and response generation
- **Streamlit**: For user interface and interaction
- **Python**: Primary implementation language

The workflows support the project's educational focus, enabling teachers to create interactive quizzes and students to receive personalized assistance based on presentation content. 