# RAG Application with User Management

This is a Retrieval-Augmented Generation (RAG) application with user authentication and role-based access control.

## 🚀 Quick Start

### 1. Run the Application
```bash
cd app
streamlit run main.py
```

### 2. Create Default Accounts
- Open the application in your browser
- Scroll down to "Development Tools" 
- Click "Create Default Accounts (for testing)"

### 3. Login with Default Accounts
- **Teacher Account**: username=`teacher`, password=`teacher123`
- **Student Account**: username=`student`, password=`student123`

## 📁 Application Structure

```
app/
├── main.py                    # Main entry point (login/register)
├── pages/
│   ├── 1_Teacher_Portal.py   # Teacher dashboard
│   └── 2_Student_Portal.py   # Student portal
├── database/
│   ├── user_server.py        # User management
│   ├── homework_server.py    # Assignment management
│   └── homework_schema.sql   # Database schema
├── pptx_rag_quizzer/         # RAG core functionality
└── test_user_system.py       # Testing utilities
```

## 🔐 User Management Features

### Authentication
- **Login/Register**: Simple form-based authentication
- **Password Security**: SHA-256 hashing
- **Role-based Access**: Teachers and students have separate portals

### User Roles
- **Teachers**: Can upload PPTX, create assignments, manage content
- **Students**: Can take assignments, receive AI grading and feedback

### Database Integration
- **User Tables**: Stores user accounts with roles and metadata
- **Assignment Ownership**: Assignments linked to creating teachers
- **Submission Tracking**: Student submissions linked to their accounts

## 🎓 Teacher Portal Features

1. **Upload PowerPoint**: Process PPTX files with text and image extraction
2. **Image Description**: AI-powered image analysis and description
3. **RAG Collection**: Create vector embeddings for content retrieval
4. **Assignment Generation**: Generate quizzes using AI
5. **Assignment Management**: View, delete, and manage created assignments

## 🧑‍🎓 Student Portal Features

1. **Assignment Access**: View available assignments
2. **Question Taking**: Answer text and image-based questions
3. **AI Grading**: Real-time grading with detailed feedback
4. **Attempt Tracking**: Up to 2 attempts per question
5. **Progress Monitoring**: Track completion and scores

## 🛠️ Development

### Testing
Run the test suite to verify functionality:
```bash
streamlit run test_user_system.py
```

### Database Setup
Ensure your MySQL database is configured with the schema in `database/homework_schema.sql`

### Environment Variables
Set up your `.env` file with:
- Database connection details
- Google API key for Gemini LLM
- ChromaDB connection settings

## 🔧 Troubleshooting

### Page Navigation Issues
- Ensure you're running `main.py` as the entry point
- Check that pages are in the `pages/` directory
- Verify file naming follows Streamlit conventions

### Database Connection
- Check your `.env` file configuration
- Ensure MySQL server is running
- Verify database schema is properly set up

### Authentication Issues
- Use the "Create Default Accounts" feature to set up test users
- Check database connection if user creation fails
- Verify password requirements (minimum 6 characters)

## 📝 Notes

- This is a development version with basic authentication
- No password recovery or advanced security features
- Session state is maintained in Streamlit's session state
- Database connections use singleton pattern for efficiency
