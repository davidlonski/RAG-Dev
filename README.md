# RAG-Dev: Retrieval-Augmented Generation Quiz Application

A comprehensive RAG (Retrieval-Augmented Generation) application built with Python, using ChromaDB as the vector store, Google's Gemini LLM API for response generation, and Streamlit for the frontend. The application features a complete user management system with teacher and student portals, powered by Supabase for database operations.

## 🎯 Features

### **User Management System**
- **Multi-User Authentication**: Login/registration system with teacher and student roles
- **Role-Based Access Control**: Separate portals for different user types
- **Database Persistence**: User data stored in Supabase (managed PostgreSQL) with proper relationships
- **Session Management**: Secure user state across application sessions

### **RAG Quizzer System**
- **PowerPoint Processing**: Upload and process PPTX files with text and image extraction
- **AI-Powered Question Generation**: Generate text and image-based questions using Gemini LLM
- **Database Persistence**: RAG quizzer data stored in Supabase (no more session state loss)
- **Teacher Isolation**: Each teacher sees only their own presentations and assignments

### **Homework Management**
- **Assignment Creation**: Teachers can create homework assignments from presentations
- **Question Types**: Support for text-based and image-based questions
- **Student Submissions**: Students can take assignments with multiple attempts
- **Grading System**: AI-powered grading with feedback

### **Technical Features**
- **ChromaDB Integration**: Vector database for document embeddings (HTTP client)
- **Gemini LLM API**: Advanced question generation and grading
- **Supabase Integration**: Managed PostgreSQL database with RESTful API access
- **Image Storage**: Base64 encoding with automatic hex conversion handling
- **Connection Resilience**: Retry logic with automatic reconnection for network issues
- **Streamlit UI**: Modern, responsive web interface

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Supabase Account (for database)
- ChromaDB Server (HTTP mode)
- Google Gemini API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd RAG-Dev
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the root directory:
   
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

   # ChromaDB Configuration
   CHROMA_SERVER_HOST=localhost
   CHROMA_SERVER_HTTP_PORT=8000

   # Google Gemini API
   GOOGLE_API_KEY=your_gemini_api_key
   ```

5. **Start ChromaDB Server**
   ```bash
   chroma run --host localhost --port 8000
   ```

6. **Set up Supabase database**
   - Create a new project in Supabase
   - Run the SQL schema from `app/database/homework_schema.sql` in your Supabase SQL editor
   - Get your project URL and service role key from Supabase settings

7. **Start the application**
   ```bash
   cd app
   streamlit run main.py
   ```

## 👥 User Roles

### **Teacher Portal**
- Upload PowerPoint presentations
- Process and describe images
- Generate homework assignments
- Manage assignments and view results
- Remove presentations

### **Student Portal**
- View available assignments
- Take assignments with multiple attempts
- Receive AI-powered grading and feedback
- Track progress and scores

## 📁 Project Structure

```
RAG-Dev/
├── app/
│   ├── main.py                    # Login/registration entry point
│   ├── pages/
│   │   ├── 1_Teacher_Portal.py   # Teacher dashboard
│   │   └── 2_Student_Portal.py   # Student portal
│   ├── database/
│   │   ├── db.py                 # MySQL database manager
│   │   ├── db_psql.py            # PostgreSQL database manager
│   │   ├── homework_schema.sql   # MySQL schema
│   │   └── homework_schema_psql.sql # PostgreSQL schema
│   ├── pptx_rag_quizzer/
│   │   ├── rag_core.py           # Core RAG functionality
│   │   ├── quiz_master.py        # Question generation
│   │   ├── image_magic.py        # Image processing
│   │   ├── file_parser.py        # PowerPoint parsing
│   │   └── presentation_model.py # Data models
│   └── requirements.txt
├── tests/                        # Test files
├── CHANGELOG.md                  # Change history
└── README.md                     # This file
```

## 🔧 Database Schema

### **Core Tables**
- **users**: User accounts with roles (teacher/student)
- **rag_quizzers**: PowerPoint presentations and metadata
- **rag_quizzer_slides**: Slide content and structure
- **assignments**: Homework assignments linked to teachers
- **questions**: Individual questions within assignments
- **submissions**: Student assignment attempts
- **submission_answers**: Individual question responses

### **Key Relationships**
- Teachers own presentations and assignments
- Students submit assignments
- Questions belong to assignments
- Answers belong to submissions

## 🧪 Testing

### **Default Accounts**
After running migrations, default accounts are created:
- **Teacher**: username=`teacher`, password=`teacher123`
- **Student**: username=`student`, password=`student123`

### **Test Scripts**
```bash

```

## 🔄 Workflow

### **Teacher Workflow**
1. **Login** as teacher
2. **Upload PowerPoint** file
3. **Process images** (auto-describe or manual)
4. **Generate homework** with questions
5. **Save assignment** to database
6. **Manage assignments** and view results

### **Student Workflow**
1. **Login** as student
2. **View available assignments**
3. **Take assignment** with multiple attempts
4. **Receive grading** and feedback
5. **Track progress** and scores

## 🐛 Troubleshooting

### **Common Issues**

1. **Database Connection Errors**
   - Verify Supabase project is active and accessible
   - Check Supabase URL and service role key in `.env`
   - Ensure database schema is created in Supabase
   - Verify Supabase service role key has proper permissions

2. **ChromaDB Connection Issues**
   - Verify ChromaDB server is running on HTTP mode
   - Check host and port in `.env` (default: localhost:8000)
   - Start ChromaDB server: `chroma run --host localhost --port 8000`
   - Restart ChromaDB if needed

3. **API Key Issues**
   - Verify Google Gemini API key is valid
   - Check API quota and limits
   - Ensure key has proper permissions

4. **Page Navigation Errors**
   - Clear browser cache
   - Restart Streamlit application
   - Check file paths in navigation

### **Debug Mode**
Enable debug information by setting environment variables:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Roadmap

- [ ] Advanced authentication (JWT, OAuth)
- [ ] Assignment sharing between teachers
- [ ] Analytics dashboard
- [ ] Bulk import/export
- [ ] Real-time collaboration
- [ ] Mobile-responsive design
- [ ] API endpoints for external integration
- [ ] Advanced question types (multiple choice, matching)
- [ ] Student performance analytics
- [ ] Assignment templates and libraries