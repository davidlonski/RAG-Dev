import streamlit as st
import sys
import os

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from database.user_server import UserServer

st.set_page_config(page_title="Login - RAG Application", page_icon="🔐", layout="wide")

ss = st.session_state

# Initialize session state
if "user_server" not in ss:
    ss.user_server = UserServer()
if "current_user" not in ss:
    ss.current_user = None
if "login_page" not in ss:
    ss.login_page = "login"  # login, register

def login_page():
    """Display the login form"""
    st.title("🔐 Login to RAG Application")
    st.write("Please enter your credentials to access the system.")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Login", type="primary")
        with col2:
            if st.form_submit_button("Register New Account"):
                ss.login_page = "register"
                st.rerun()
        
        if submit_button:
            if username and password:
                user = ss.user_server.authenticate_user(username, password)
                if user:
                    ss.current_user = user
                    st.success(f"✅ Welcome back, {user['first_name']} {user['last_name']}!")
                    st.info(f"You are logged in as a {user['role']}.")
                    
                    # Redirect based on role
                    if user['role'] == 'teacher':
                        st.switch_page("teacher.py")
                    else:
                        st.switch_page("student.py")
                else:
                    st.error("❌ Invalid username or password. Please try again.")
            else:
                st.warning("⚠️ Please enter both username and password.")

def register_page():
    """Display the registration form"""
    st.title("📝 Register New Account")
    st.write("Create a new account to access the system.")
    
    with st.form("register_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            first_name = st.text_input("First Name", placeholder="Enter your first name")
            last_name = st.text_input("Last Name", placeholder="Enter your last name")
            email = st.text_input("Email (Optional)", placeholder="Enter your email")
        
        with col2:
            username = st.text_input("Username", placeholder="Choose a username")
            password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        role = st.selectbox("Role", ["student", "teacher"], help="Select your role in the system")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_button = st.form_submit_button("Register", type="primary")
        with col2:
            if st.form_submit_button("Back to Login"):
                ss.login_page = "login"
                st.rerun()
        
        if submit_button:
            # Validate form
            if not all([first_name, last_name, username, password, confirm_password]):
                st.error("❌ Please fill in all required fields.")
            elif password != confirm_password:
                st.error("❌ Passwords do not match.")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters long.")
            else:
                # Create user
                user_data = {
                    'username': username,
                    'password': password,
                    'email': email if email else None,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role
                }
                
                user_id = ss.user_server.create_user(user_data)
                if user_id:
                    st.success("✅ Account created successfully! You can now login.")
                    ss.login_page = "login"
                    st.rerun()
                else:
                    st.error("❌ Failed to create account. Username may already exist.")

def create_default_accounts():
    """Create default accounts if they don't exist"""
    if st.button("Create Default Accounts (for testing)"):
        success = ss.user_server.create_default_users()
        if success:
            st.success("✅ Default accounts created!")
            st.info("Teacher: username='teacher', password='teacher123'")
            st.info("Student: username='student', password='student123'")
        else:
            st.error("❌ Failed to create default accounts.")

# Main app logic
if ss.login_page == "login":
    login_page()
else:
    register_page()

# Footer with default account creation
st.markdown("---")
with st.expander("🔧 Development Tools"):
    create_default_accounts()
