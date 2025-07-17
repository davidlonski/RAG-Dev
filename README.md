# RAG Homework Generator

A Streamlit application that allows teachers to upload PowerPoint presentations, describe images using AI, and generate interactive homework assignments that students can download and complete.

## Overview

This application uses Retrieval-Augmented Generation (RAG) technology to create intelligent homework assignments from PowerPoint presentations. Teachers can upload presentations, have AI assist with image descriptions, and generate Excel spreadsheets with embedded images and questions for students.

## User Flow

### Teacher Workflow:
1. **Role Selection** - Choose "Teacher" role
2. **Upload PowerPoint** - Upload a .pptx document
3. **AI Image Analysis** - AI automatically describes images found in the presentation
4. **Batch Image Review** - Review and edit AI-generated descriptions in batches (5 images at a time)
5. **RAG Processing** - Content is processed through RAG for intelligent question generation
6. **Generate Excel Spreadsheet** - Creates an Excel file with embedded images and questions
7. **Download & Share** - Download the Excel file and share with students

### Student Workflow:
1. **Role Selection** - Choose "Student" role
2. **Access Homework** - View available homework assignments
3. **Download Excel File** - Download the homework Excel file
4. **Complete Assignment** - Answer questions directly in the Excel file
5. **Submit Work** - Save and submit completed homework

## Features

- **Dual Role Interface**: Separate workflows for teachers and students
- **AI-Powered Image Analysis**: Automatic image description using Google Gemini
- **Batch Processing**: Efficient handling of large presentations with batch image processing
- **RAG-Powered Questions**: Intelligent question generation from PowerPoint content
- **Excel Export with Images**: Embedded images in Excel spreadsheets for visual questions
- **Mixed Question Types**: Both text-based and image-based questions
- **Session State Management**: Maintains progress across interactions
- **Responsive Design**: Works on different screen sizes
- **Error Handling**: Robust error handling with retry mechanisms for API calls

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd RAG-Dev
```

2. Install dependencies:
```bash
pip install -r app/requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file in the app directory
cp app/.env.example app/.env
# Add your Google Gemini API key to app/.env
GOOGLE_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run app/app.py
```

## Usage

### For Teachers:
1. Select "I'm a Teacher" role
2. Upload your PowerPoint presentation (.pptx format)
3. Wait for AI to analyze and describe images automatically
4. Review and edit image descriptions in batches
5. Generate an Excel spreadsheet with questions and embedded images
6. Download and share the Excel file with your students

### For Students:
1. Select "I'm a Student" role
2. View available homework assignments
3. Download the Excel file from your teacher
4. Complete the questions directly in the Excel file
5. Save and submit your completed homework

## Technology Stack

- **Streamlit**: Web application framework
- **Google Gemini**: AI-powered image analysis and question generation
- **ChromaDB**: Vector database for RAG functionality
- **OpenPyXL**: Excel spreadsheet generation with embedded images
- **Pillow (PIL)**: Image processing and manipulation
- **python-pptx**: PowerPoint file parsing
- **Sentence Transformers**: Text embedding for RAG
- **Tesseract**: OCR for image text extraction

## File Structure

```
app/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── pptx_rag_quizzer/     # Core RAG functionality
│   ├── rag_controller.py # Main RAG controller
│   ├── rag_core.py       # RAG core implementation
│   ├── quiz_master.py    # Question generation logic
│   ├── image_magic.py    # Image processing utilities
│   ├── file_parser.py    # PowerPoint parsing
│   └── utils.py          # Utility functions
└── chroma_db/           # Vector database storage
```

## Configuration

The application requires a Google Gemini API key for AI functionality. Set this in your `.env` file:

```
GOOGLE_API_KEY=your_api_key_here
```

## Features in Detail

### AI Image Analysis
- Automatic image description generation using Google Gemini
- Batch processing for efficiency with large presentations
- Teacher review and editing capabilities
- Error handling with retry mechanisms

### RAG Question Generation
- Intelligent question generation from PowerPoint content
- Mix of text-based and image-based questions
- Context-aware question creation
- Rate limiting and quota management

### Excel Integration
- Embedded images in Excel spreadsheets
- Formatted questions with proper text wrapping
- Professional layout with headers and styling
- Direct download functionality

### Session Management
- Progress tracking across application stages
- State persistence during image processing
- Batch navigation and saving
- Role-based interface switching

## Troubleshooting

### Common Issues:
1. **API Rate Limits**: The app includes retry logic for API quota exhaustion
2. **Large Presentations**: Batch processing handles presentations with many images
3. **Image Format Issues**: Automatic image validation and conversion
4. **Memory Usage**: Efficient processing with streaming and cleanup

### Getting Help:
- Check that your Google Gemini API key is correctly set
- Ensure all dependencies are installed from `app/requirements.txt`
- Verify PowerPoint files are in .pptx format
- Check console output for detailed error messages