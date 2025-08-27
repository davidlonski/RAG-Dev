import streamlit as st
import sys
import os

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from database.user_server import UserServer
from database.homework_server import HomeworkServer

st.set_page_config(page_title="User System Test", page_icon="🧪", layout="wide")

ss = st.session_state

# Initialize servers
if "user_server" not in ss:
    ss.user_server = UserServer()
if "homework_server" not in ss:
    ss.homework_server = HomeworkServer()

st.title("🧪 User System Test")
st.write("Test the user authentication and database integration.")

# Test user creation
st.header("👤 User Management Tests")

# Create default users
if st.button("Create Default Users"):
    success = ss.user_server.create_default_users()
    if success:
        st.success("✅ Default users created successfully!")
    else:
        st.error("❌ Failed to create default users.")

# Test authentication
st.subheader("🔐 Authentication Test")
with st.form("auth_test"):
    test_username = st.text_input("Test Username", value="teacher")
    test_password = st.text_input("Test Password", value="teacher123", type="password")
    
    if st.form_submit_button("Test Authentication"):
        user = ss.user_server.authenticate_user(test_username, test_password)
        if user:
            st.success(f"✅ Authentication successful!")
            st.json(user)
        else:
            st.error("❌ Authentication failed.")

# List users
st.subheader("📋 User List")
if st.button("List All Users"):
    users = ss.user_server.list_users()
    if users:
        st.write(f"Found {len(users)} users:")
        for user in users:
            st.write(f"- {user['username']} ({user['role']}) - {user['first_name']} {user['last_name']}")
    else:
        st.info("No users found.")

# Test assignment creation with teacher
st.header("📚 Assignment Tests")

# Get teachers
teachers = ss.user_server.get_teachers()
if teachers:
    st.subheader("Create Test Assignment")
    with st.form("assignment_test"):
        teacher = st.selectbox("Select Teacher", teachers, format_func=lambda x: f"{x['first_name']} {x['last_name']}")
        assignment_name = st.text_input("Assignment Name", value="Test Assignment")
        
        if st.form_submit_button("Create Test Assignment"):
            # Create a simple test assignment
            test_assignment = {
                'name': assignment_name,
                'teacher_id': teacher['id'],
                'collection_id': 'test_collection',
                'questions': [
                    {
                        'question': 'What is 2+2?',
                        'answer': '4',
                        'context': 'Basic arithmetic',
                        'type': 'text'
                    }
                ],
                'num_text_questions': 1,
                'num_image_questions': 0,
                'status': 'active'
            }
            
            assignment_id = ss.homework_server.create_assignment(test_assignment)
            if assignment_id:
                st.success(f"✅ Test assignment created with ID: {assignment_id}")
            else:
                st.error("❌ Failed to create test assignment.")

# Test assignment retrieval
st.subheader("Assignment Retrieval")
if teachers:
    teacher = teachers[0]  # Use first teacher
    assignments = ss.homework_server.get_assignments_by_teacher(teacher['id'])
    st.write(f"Assignments for {teacher['first_name']} {teacher['last_name']}: {len(assignments)}")
    for assignment in assignments:
        st.write(f"- {assignment['name']} (ID: {assignment['id']})")

# Test student submission
st.header("📝 Submission Tests")

# Get students
students = ss.user_server.get_students()
if students and teachers:
    st.subheader("Create Test Submission")
    with st.form("submission_test"):
        student = st.selectbox("Select Student", students, format_func=lambda x: f"{x['first_name']} {x['last_name']}")
        teacher = st.selectbox("Select Teacher for Assignment", teachers, format_func=lambda x: f"{x['first_name']} {x['last_name']}")
        
        if st.form_submit_button("Create Test Submission"):
            # Get teacher's assignments
            assignments = ss.homework_server.get_assignments_by_teacher(teacher['id'])
            if assignments:
                assignment = assignments[0]  # Use first assignment
                
                # Create submission
                submission = ss.homework_server.get_or_create_active_submission(student['id'], assignment['id'])
                if submission:
                    st.success(f"✅ Test submission created with ID: {submission['id']}")
                    
                    # Record an answer
                    success = ss.homework_server.record_answer_attempt(
                        submission_id=submission['id'],
                        question_id=1,  # Assuming first question
                        attempt_number=1,
                        student_answer="4",
                        grade=2,
                        feedback="Correct answer!"
                    )
                    if success:
                        st.success("✅ Test answer recorded successfully!")
                    else:
                        st.error("❌ Failed to record test answer.")
                else:
                    st.error("❌ Failed to create test submission.")
            else:
                st.warning("⚠️ No assignments found for selected teacher.")

# Database connection test
st.header("🔌 Database Connection Test")
if st.button("Test Database Connections"):
    # Test user server connection
    user_conn = ss.user_server.get_connection()
    if user_conn:
        st.success("✅ User database connection successful")
    else:
        st.error("❌ User database connection failed")
    
    # Test homework server connection
    homework_conn = ss.homework_server.get_connection()
    if homework_conn:
        st.success("✅ Homework database connection successful")
    else:
        st.error("❌ Homework database connection failed")

st.markdown("---")
st.write("**Test completed!** Check the results above to verify the user system is working correctly.")
