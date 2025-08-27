# Changelog

## [2024-12-19] - RAG Quizzer Persistence & User Management System

### 🎯 Major Features Added

#### **User Management System**
- **User Authentication**: Basic login/registration system with teacher and student roles
- **Database Integration**: User data stored in MySQL with proper foreign key relationships
- **Role-Based Access Control**: Separate portals for teachers and students
- **Session Management**: User state maintained across page navigation

#### **RAG Quizzer Persistence**
- **Database Persistence**: RAG quizzer data now stored in MySQL instead of session state
- **Teacher Isolation**: Each teacher sees only their own presentations and assignments
- **Data Integrity**: Foreign key relationships maintain consistency
- **Scalability**: Database can handle many presentations and assignments

### 🗄️ Database Schema Updates

#### **New Tables Added**
```sql
-- User management tables
CREATE TABLE users (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(255) NULL,
  first_name VARCHAR(255) NOT NULL,
  last_name VARCHAR(255) NOT NULL,
  role ENUM('teacher','student') NOT NULL,
  created_at DATETIME NOT NULL,
  last_login DATETIME NULL,
  status ENUM('active','inactive') NOT NULL DEFAULT 'active'
);

-- RAG Quizzer management tables
CREATE TABLE rag_quizzers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  teacher_id INT NOT NULL,
  name VARCHAR(255) NOT NULL,
  collection_id VARCHAR(255) NOT NULL,
  presentation_name VARCHAR(255) NOT NULL,
  num_slides INT NOT NULL,
  num_text_items INT NOT NULL DEFAULT 0,
  num_image_items INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL,
  status ENUM('active','archived') NOT NULL DEFAULT 'active',
  FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE rag_quizzer_slides (
  id INT PRIMARY KEY AUTO_INCREMENT,
  rag_quizzer_id INT NOT NULL,
  slide_number INT NOT NULL,
  slide_content LONGTEXT NULL,
  created_at DATETIME NOT NULL,
  FOREIGN KEY (rag_quizzer_id) REFERENCES rag_quizzers(id) ON DELETE CASCADE ON UPDATE CASCADE
);
```

#### **Updated Tables**
- **assignments**: Added `teacher_id` foreign key
- **submissions**: Added `student_id` foreign key

### 🔧 New Components

#### **Database Servers**
- **`UserServer`**: CRUD operations for user management
- **`RAGQuizzerServer`**: CRUD operations for RAG quizzer persistence
- **Updated `HomeworkServer`**: Integrated with user system

#### **Application Structure**
- **Multi-page Streamlit App**: Restructured to use Streamlit's `pages/` directory
- **`main.py`**: Login/registration entry point
- **`pages/1_Teacher_Portal.py`**: Teacher dashboard with database integration
- **`pages/2_Student_Portal.py`**: Student portal for taking assignments

### 🐛 Bug Fixes

#### **Page Navigation**
- Fixed `StreamlitAPIException` errors in page navigation
- Corrected file path references to use proper relative paths
- Ensured consistent `.py` extensions in navigation calls

#### **Homework Generation**
- Fixed `'NoneType' object has no attribute` errors in QuizMaster
- Resolved RAG core initialization issues
- Fixed collection access in question generation

#### **Assignment Management**
- Fixed logic error in manage assignments function
- Corrected database queries for teacher-specific assignments
- Resolved presentation loading from database

### 📁 File Structure Changes

```
app/
├── main.py                    # Login/registration entry point
├── pages/
│   ├── 1_Teacher_Portal.py   # Teacher dashboard
│   └── 2_Student_Portal.py   # Student portal
├── database/
│   ├── user_server.py        # User CRUD operations
│   ├── rag_quizzer_server.py # RAG quizzer CRUD operations
│   ├── homework_server.py    # Updated with user integration
│   └── migrate_rag_quizzer.py # Database migration script
└── test_rag_quizzer.py       # Test script for RAG quizzer operations
```

### 🔄 Migration Process

1. **Database Migration**: Run `python app/database/migrate_rag_quizzer.py`
2. **Default Users**: Created teacher and student accounts
3. **Data Migration**: Existing presentations saved to database

### 🧪 Testing

- **User Authentication**: Login/registration working correctly
- **RAG Quizzer Persistence**: Presentations survive app restarts
- **Homework Generation**: Questions generate successfully from database
- **Assignment Management**: Teachers can manage their assignments
- **Page Navigation**: All navigation between portals working

### 🚀 Performance Improvements

- **Persistent Storage**: No data loss on app restart
- **Scalability**: Database can handle multiple teachers and students
- **Isolation**: Teachers only see their own content
- **Reliability**: Proper error handling and validation

### 📝 Breaking Changes

- **Session State**: RAG quizzer data no longer stored in session state
- **File Structure**: Moved to multi-page Streamlit application
- **Database Schema**: New tables and foreign key relationships
- **Authentication**: Login required for all portal access

### 🔮 Future Enhancements

- **Advanced Authentication**: JWT tokens, password reset
- **Assignment Sharing**: Teachers can share assignments
- **Analytics Dashboard**: Student performance tracking
- **Bulk Operations**: Import/export assignments
- **Real-time Collaboration**: Live assignment updates
