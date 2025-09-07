# Changelog

## [2025-01-27] - UI Improvements and Bug Fixes

### 🐛 Bug Fixes
- **Fixed Division by Zero Error**: Resolved crash when all images are deleted during description phase
- **Progress Bar Protection**: Added checks to prevent division by zero in progress calculations
- **Graceful Error Handling**: Application now handles edge cases when no images remain

### 🎨 UI/UX Improvements
- **Fixed Button Width**: Set consistent 200px width for all action buttons using custom CSS
- **Cross-Portal Consistency**: Applied same button styling to both teacher and student portals
- **Selective Full-Width Buttons**: Kept full-width styling only for navigation and back buttons where appropriate
- **Better Visual Balance**: Improved button proportions for better user experience
- **Consistent Sizing**: All action buttons now have uniform width regardless of text length

### 📊 Teacher Portal Enhancements
- **Show Correct Answers**: Added correct answer display in assignment results view for better grading context
- **Improved Answer Comparison**: Teachers can now see both correct answers and student responses side by side
- **Enhanced Grading Experience**: Better visibility into question expectations and student performance
- **Student Feedback Display**: Teachers can now view student feedback about assignments in the results view

### 🎓 Student Portal Enhancements
- **Assignment Feedback System**: Students can now provide feedback after completing assignments
- **Editable Feedback**: Students can view and edit their previous feedback submissions
- **Improved Learning Experience**: Feedback collection helps improve future assignment design

### 🔐 Authentication Improvements
- **Default Student Role**: Registration now automatically assigns "student" role to new users
- **Simplified Registration**: Removed role selection dropdown for cleaner user experience
- **Streamlined Onboarding**: New users are automatically directed to student portal
- **Enhanced Field Validation**: Added comprehensive validation for all registration fields
- **Required Email**: Email is now mandatory for account creation
- **Input Sanitization**: All fields are trimmed and validated before account creation
- **Email-Based Authentication**: Removed username field, users now login with email
- **Auto-Generated Usernames**: Usernames are automatically generated from email addresses

## [2025-01-27] - Enhanced Image Description Batch Processing

### 🎯 Major Features Added

#### **Improved Image Description Workflow**
- **Always Batch Processing**: Removed one-by-one image description mode for better usability
- **Increased Batch Size**: Changed from batches of 5 to maximum batch size of 10 images
- **Unified Experience**: All image descriptions now use consistent batch interface regardless of image count
- **Better Navigation**: Enhanced batch navigation with clear batch numbering (e.g., "Batch 1 of 3")
- **Improved Progress Tracking**: More accurate progress indicators and batch status display
- **Proper Image Ordering**: Images are now presented in correct sequence based on slide number and order within slides
- **Image Deletion Feature**: Teachers can now delete unwanted images from the presentation model
- **Smart Filtering**: Deleted images are excluded from RAG collection creation and question generation
- **Restore Functionality**: "Restore All" button allows teachers to bring back deleted images
- **Image Size Optimization**: Images are now displayed at fixed widths (400px for description, 300px for questions) for better UI layout

### 🔧 Technical Improvements

#### **Code Simplification**
- **Removed Conditional Logic**: Eliminated complex if/else branching between single and batch modes
- **Consistent Processing**: All images now follow the same batch processing workflow
- **Better User Experience**: Teachers can now process any number of images using the same intuitive interface
- **Enhanced Batch Calculations**: Improved batch numbering and total batch count display
- **Image Sorting Logic**: Added proper sorting by slide number and order number to maintain presentation sequence
- **Efficient Deletion Marking**: Images are marked as deleted by setting content to "__DELETED__" marker instead of rebuilding objects
- **Direct Presentation Modification**: Deleted images are marked directly in the presentation model for better performance

### 📁 Files Modified

- **`app/pages/1_Teacher_Portal.py`**: 
  - Updated `describe_images()` function to always use batch processing with max batch size of 10
  - Added image deletion functionality with delete buttons for each image
  - Created `mark_image_as_deleted()` function to mark images as deleted using "__DELETED__" content marker
  - Updated image filtering to check for deletion markers instead of session state
  - Added deletion status display and "Restore All" functionality
- **`app/pptx_rag_quizzer/rag_core.py`**: 
  - Updated `create_collection()` to skip images marked with "__DELETED__" content
- **`app/pages/2_Student_Portal.py`**: 
  - Updated image display to use fixed width (300px) for better UI layout

### 🎯 User Impact

#### **Teacher Experience**
- **Consistent Interface**: Same workflow whether processing 3 images or 30 images
- **Better Efficiency**: Larger batch sizes reduce navigation overhead
- **Clearer Progress**: Better understanding of current position in the image description process
- **Simplified Workflow**: No more switching between different modes based on image count
- **Image Control**: Teachers can remove irrelevant or problematic images from their presentations
- **Quality Assurance**: Deleted images won't appear in generated questions or RAG collections
- **Flexible Editing**: Easy restoration of accidentally deleted images with "Restore All" button
- **Better UI Layout**: Images are now displayed at reasonable sizes for improved readability and interface organization

### 🔄 Configuration Updates

- **Batch Size**: Increased from 5 to 10 images per batch
- **Processing Mode**: Always batch processing regardless of total image count
- **Navigation**: Enhanced batch navigation with proper batch numbering

---

## [2025-08-26] - Unified Image Storage System & Database Consolidation

### 🎯 Major Features Added

#### **Unified Image Storage System**
- **Database Consolidation**: Moved from multiple databases to single homework database
- **Normalized Image Storage**: Created unified images table with proper metadata tracking
- **Schema Migration**: Successfully migrated from BLOB storage to normalized image references
- **Enhanced Metadata**: File size, content type, and creation timestamp tracking
- **Production Ready**: System fully operational with clean database schema

#### **Database Consolidation**
- **RAG Quizzer Integration**: Consolidated RAG quizzer functionality into homework database
- **Code Simplification**: Removed separate rag_quizzer_db.py and migrate_rag_quizzer.py files
- **Unified Database Access**: All database operations now use single homework database
- **Reduced Complexity**: Eliminated duplicate database connections and migration scripts

#### **Navigation Improvements**
- **Back Button Navigation**: Added consistent back buttons to all teacher portal screens
- **Improved User Flow**: Fixed navigation between upload, describe images, and process quiz screens
- **Better UX**: Users can now easily navigate back to dashboard from any screen
- **Consistent Interface**: Standardized back button placement across all screens
- **Bug Fix**: Resolved Streamlit duplicate button ID errors by adding unique keys to all navigation buttons

#### **Teacher Assignment Results Viewing**
- **Comprehensive Results Display**: Complete assignment results viewing for teachers
- **Student Submission Tracking**: Detailed view of all student submissions and attempts
- **Performance Analytics**: Assignment statistics including completion rates and average scores
- **Question-by-Question Analysis**: Detailed breakdown of each student's answers and grades

#### **Student Assignment Flow Restructure**
- **Attempt-Based System**: Implemented proper first and second attempt tracking
- **Dynamic Button States**: Buttons change based on attempt progress and completion status
- **Completed Assignment Viewing**: Students can view finished assignments with full results
- **Assignment Status Tracking**: Real-time status display (Not Started, In Progress, Completed)

### 🔧 Technical Improvements

#### **Database Enhancements**
- **New Functions**: Added `get_completed_submission()`, `get_active_submission()`, and `get_all_submissions_for_assignment()`
- **Status Tracking**: Proper submission status management (in_progress, completed)
- **Attempt Validation**: Ensures all questions are attempted before final submission
- **Student Data Integration**: JOIN operations to retrieve student information with submissions
- **Image Storage Consolidation**: Unified images table with metadata and foreign key relationships
- **Migration System**: Automated migration script for existing image data
- **Database Consolidation**: Integrated RAG quizzer functionality into homework database
- **Code Cleanup**: Removed unnecessary files and consolidated database operations

#### **Code Quality**
- **State Management**: Proper session state handling for attempt tracking and results viewing
- **Error Handling**: Comprehensive validation and user feedback
- **Database Integration**: Efficient queries for submission status checking and results retrieval
- **UI Organization**: Clear, expandable interface for detailed results viewing

#### **Documentation Standards**
- **Commit Message Standards**: Added comprehensive commit message guidelines to cursor rules
- **GitHub Summary System**: Created `github-summary.md` for tracking changes
- **Changelog Integration**: Automated changelog updates for all future changes

### 📁 Files Modified

- **`app/database/homework_schema.sql`**: Added images table and updated questions table structure
- **`app/database/image_db.py`**: Updated to use homework database and enhanced metadata
- **`app/database/homework_db.py`**: Updated to use image_id references and added submission tracking functions
- **`app/pptx_rag_quizzer/quiz_master.py`**: Updated to handle new image data format
- **`app/pptx_rag_quizzer/image_magic.py`**: Updated image upload and retrieval functions
- **`app/pptx_rag_quizzer/rag_core.py`**: Updated image upload calls
- **`app/database/migrate_images.py`**: Created migration script for existing data
- **`app/pages/1_Teacher_Portal.py`**: Added view_assignment_results function and navigation
- **`app/pages/2_Student_Portal.py`**: Complete restructure of assignment taking flow
- **`.cursor/rules/general.mdc`**: Added commit message and changelog standards
- **`.gitignore`**: Added `github-summary.md` to temporary files section
- **`github-summary.md`**: Created for change tracking (gitignored)
- **`CHANGELOG.md`**: Updated with current changes

### 🎯 User Impact

#### **Teacher Experience**
- **Comprehensive Results**: Complete view of all student submissions and performance
- **Performance Analytics**: Assignment statistics and average scores for assessment
- **Detailed Analysis**: Question-by-question breakdown of student performance
- **AI Feedback Review**: Access to all AI-generated feedback for quality assessment

#### **Student Experience**
- **Intuitive Flow**: Students follow clear attempt-based progression
- **Better Feedback**: Real-time grading and attempt history display
- **Status Awareness**: Clear indication of assignment progress and completion
- **Complete Tracking**: All attempts, grades, and feedback properly stored for teacher review

### 🔄 Configuration Updates

- **Cursor Rules**: Enhanced with commit message and changelog requirements
- **File Management**: Temporary files properly excluded from version control
- **Change Tracking**: Automated documentation system implemented

### 📊 Data Tracking

- **Complete Attempt History**: Both attempts stored with grades and AI feedback
- **Student Information**: Full tracking of who took each assignment
- **Submission Status**: Proper completion marking and status management
- **Teacher Review**: All data available for comprehensive teacher analysis

---

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
- **`HomeworkServer`**: Integrated homework and RAG quizzer management

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
│   ├── user_db.py            # User CRUD operations
│   └── homework_db.py        # Homework and RAG quizzer management

```

### 🔄 Migration Process


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
