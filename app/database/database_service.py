import os
import hashlib
import secrets
import uuid
import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client


class DatabaseManagerSupabase:
    """
    Unified Supabase database manager that combines all database operations.
    Singleton class for managing Supabase connections and CRUD operations.
    Handles user authentication, homework assignments, submissions, and image storage.
    """

    _instance = None
    _supabase: Optional[Client] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManagerSupabase, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._supabase = self._configure_supabase()
            self._initialized = True

    def _configure_supabase(self) -> Optional[Client]:
        """Configure and return a Supabase client connection."""
        load_dotenv()
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for full access
        
        if not url or not key:
            print("Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
            return None

        try:
            supabase = create_client(url, key)
            print("Supabase client connection established successfully")
            return supabase
        except Exception as exc:
            print(f"Error connecting to Supabase: {exc}")
            return None

    @property
    def supabase(self) -> Optional[Client]:
        """Return the underlying Supabase client object, or None if not connected."""
        return self._supabase

    def get_connection(self) -> Optional[Client]:
        """Return an active Supabase client connection."""
        if self._supabase:
            return self._supabase
        print("Reconnecting to Supabase...")
        self._supabase = self._configure_supabase()
        return self._supabase
    
    def force_reconnect(self):
        """Force a reconnection to Supabase."""
        print("Forcing Supabase reconnection...")
        self._supabase = None
        self._supabase = self._configure_supabase()
        return self._supabase

    def close_connection(self):
        """Close the Supabase connection if open."""
        try:
            if self._supabase:
                # Supabase client doesn't have an explicit close method
                self._supabase = None
                print("Supabase client connection closed")
        except Exception as exc:
            print(f"Error closing Supabase connection: {exc}")

    def __del__(self):
        self.close_connection()

    # =============================================================================
    # USER MANAGEMENT METHODS
    # =============================================================================

    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self._hash_password(password) == hashed_password

    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new user account.

        user_data: dict with the following structure:
        {
            'username': str,
            'password': str,
            'email': str (optional),
            'first_name': str,
            'last_name': str,
            'role': 'teacher' | 'student'
        }

        Returns the user id if successful, None otherwise.
        """
        supabase = self.get_connection()
        if not supabase:
            print("❌ No Supabase connection available")
            return None

        try:
            # Validate required fields
            required_fields = ['username', 'password', 'first_name', 'last_name', 'role']
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    print(f"❌ Missing required field: {field}")
                    return None

            # Validate role
            if user_data['role'] not in ['teacher', 'student']:
                print("❌ Invalid role. Must be 'teacher' or 'student'")
                return None

            # Check if username already exists
            if self.get_user_by_username(user_data['username']):
                print("❌ Username already exists")
                return None

            # Hash password
            password_hash = self._hash_password(user_data['password'])

            # Prepare data for insertion
            insert_data = {
                'username': user_data['username'],
                'password_hash': password_hash,
                'email': user_data.get('email'),
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'role': user_data['role'],
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }

            # Insert user
            result = supabase.table('users').insert(insert_data).execute()
            
            if result.data and len(result.data) > 0:
                user_id = result.data[0]['id']
                print(f"✅ User created successfully with ID: {user_id}")
                return user_id
            else:
                print("❌ Failed to create user - no data returned")
                return None

        except Exception as exc:
            print(f"❌ Unexpected error during user creation: {exc}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.

        Returns user data if authentication successful, None otherwise.
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            # Query user by username and status
            result = supabase.table('users').select(
                'id, username, password_hash, email, first_name, last_name, role, created_at, last_login, status'
            ).eq('username', username).eq('status', 'active').execute()

            if not result.data or len(result.data) == 0:
                return None

            user = result.data[0]

            # Verify password
            if not self._verify_password(password, user['password_hash']):
                return None

            # Update last login
            self.update_last_login(user['id'])

            # Return user data without password hash
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role'],
                'created_at': user['created_at'],
                'last_login': user['last_login'],
                'status': user['status'],
            }

        except Exception as exc:
            print(f"❌ Unexpected error during authentication: {exc}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            result = supabase.table('users').select(
                'id, username, email, first_name, last_name, role, created_at, last_login, status'
            ).eq('id', user_id).execute()

            if not result.data or len(result.data) == 0:
                return None

            user = result.data[0]
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role'],
                'created_at': user['created_at'],
                'last_login': user['last_login'],
                'status': user['status'],
            }

        except Exception as exc:
            print(f"❌ Unexpected error during user fetch: {exc}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            result = supabase.table('users').select(
                'id, username, email, first_name, last_name, role, created_at, last_login, status'
            ).eq('username', username).execute()

            if not result.data or len(result.data) == 0:
                return None

            user = result.data[0]
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role'],
                'created_at': user['created_at'],
                'last_login': user['last_login'],
                'status': user['status'],
            }

        except Exception as exc:
            print(f"❌ Unexpected error during user fetch: {exc}")
            return None

    def list_users(self, role: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List users, optionally filtered by role.

        Args:
            role: Optional filter for 'teacher' or 'student'
            limit: Optional limit on number of results
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            query = supabase.table('users').select(
                'id, username, email, first_name, last_name, role, created_at, last_login, status'
            ).eq('status', 'active').order('created_at', desc=True)

            if role and role in ['teacher', 'student']:
                query = query.eq('role', role)

            if limit and isinstance(limit, int) and limit > 0:
                query = query.limit(limit)

            result = query.execute()

            return result.data if result.data else []

        except Exception as exc:
            print(f"❌ Unexpected error during users list: {exc}")
            return []

    def update_user(self, user_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update user information.

        Args:
            user_id: ID of user to update
            updates: Dict of fields to update (username, email, first_name, last_name, role, status)
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            # Validate updates
            allowed_fields = ['username', 'email', 'first_name', 'last_name', 'role', 'status']
            valid_updates = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}

            if not valid_updates:
                print("❌ No valid fields to update")
                return False

            # Check if username already exists (if updating username)
            if 'username' in valid_updates:
                existing_user = self.get_user_by_username(valid_updates['username'])
                if existing_user and existing_user['id'] != user_id:
                    print("❌ Username already exists")
                    return False

            # Validate role if updating
            if 'role' in valid_updates and valid_updates['role'] not in ['teacher', 'student']:
                print("❌ Invalid role. Must be 'teacher' or 'student'")
                return False

            # Validate status if updating
            if 'status' in valid_updates and valid_updates['status'] not in ['active', 'inactive']:
                print("❌ Invalid status. Must be 'active' or 'inactive'")
                return False

            # Update user
            result = supabase.table('users').update(valid_updates).eq('id', user_id).execute()

            if result.data:
                print(f"✅ User {user_id} updated successfully")
                return True
            else:
                print(f"❌ Failed to update user {user_id}")
                return False

        except Exception as exc:
            print(f"❌ Unexpected error during user update: {exc}")
            return False

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password."""
        try:
            if not new_password:
                print("❌ New password cannot be empty")
                return False

            password_hash = self._hash_password(new_password)
            
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            result = supabase.table('users').update({'password_hash': password_hash}).eq('id', user_id).execute()
            
            if result.data:
                print(f"✅ Password updated successfully for user {user_id}")
                return True
            else:
                print(f"❌ Failed to update password for user {user_id}")
                return False

        except Exception as exc:
            print(f"❌ Unexpected error during password update: {exc}")
            return False

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            result = supabase.table('users').update({'last_login': datetime.now().isoformat()}).eq('id', user_id).execute()
            return bool(result.data)

        except Exception as exc:
            print(f"❌ Unexpected error during last login update: {exc}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """
        Soft delete a user by setting status to 'inactive'.
        Note: This preserves data integrity for foreign key relationships.
        """
        try:
            return self.update_user(user_id, {'status': 'inactive'})
        except Exception as exc:
            print(f"❌ Unexpected error during user deletion: {exc}")
            return False

    def get_teachers(self) -> List[Dict[str, Any]]:
        """Get all active teachers."""
        return self.list_users(role='teacher')

    def get_students(self) -> List[Dict[str, Any]]:
        """Get all active students."""
        return self.list_users(role='student')


    # =============================================================================
    # HOMEWORK/ASSIGNMENT MANAGEMENT METHODS
    # =============================================================================

    def create_assignment(self, assignment: Dict[str, Any]) -> Optional[str]:
        """
        Insert an assignment and its questions.

        assignment: dict shaped like the session-state homework assignment, e.g.:
          {
            'collection_id': str,
            'teacher_id': int,  # Required: ID of the teacher creating the assignment
            'questions': List[Dict[str, Any]]
            [
                {
                    'question': str,
                    'answer': str,
                    'context': str,
                    'type': 'text'|'image',
                    'image_extension': str?,
                    'image_bytes': str?,    
                }
            ],
            'num_text_questions': int,
            'num_image_questions': int,
            'status': 'active',
            'name': str,
          }

        Returns the assignment id if successful, None otherwise.
        """
        supabase = self.get_connection()
        if not supabase:
            print("❌ No Supabase connection available")
            return None

        try:
            created_at = datetime.now().isoformat()
            name = assignment.get("name")
            collection_id = assignment.get("collection_id")
            teacher_id = assignment.get("teacher_id")
            status = assignment.get("status", "active")
            questions: List[Dict[str, Any]] = assignment.get("questions", [])
            
            # Validate teacher_id is provided
            if not teacher_id:
                print("❌ teacher_id is required for assignment creation")
                return None
            
            num_questions = len(questions)
            num_text_questions = sum(1 for q in questions if q.get("type") == "text")
            num_image_questions = sum(1 for q in questions if q.get("type") == "image")

            # Insert assignment
            assignment_data = {
                'name': name,
                'collection_id': collection_id,
                'teacher_id': teacher_id,
                'created_at': created_at,
                'num_questions': num_questions,
                'num_text_questions': num_text_questions,
                'num_image_questions': num_image_questions,
                'status': status
            }

            result = supabase.table('assignments').insert(assignment_data).execute()
            
            if not result.data or len(result.data) == 0:
                print("❌ Failed to create assignment")
                return None

            assignment_id = result.data[0]['id']

            # Insert questions
            for idx, q in enumerate(questions, start=1):
                qtype = q.get("type")
                qtext = q.get("question")
                ans = q.get("answer")
                ctx = q.get("context")
                if isinstance(ctx, list):
                    ctx = "\n".join(ctx)
                
                image_id = None
                if qtype == "image" and q.get("image_bytes") and q.get("image_extension"):
                    # Upload image to images table and get image_id
                    try:
                        # Get image data for processing
                        image_bytes_data = q.get("image_bytes")
                        
                        # image_bytes should be base64 encoded from question generation
                        if isinstance(image_bytes_data, str):
                            # It's already base64 encoded, decode it to bytes
                            img_bytes = base64.b64decode(image_bytes_data)
                        elif isinstance(image_bytes_data, bytes):
                            # It's already bytes, use directly
                            img_bytes = image_bytes_data
                        else:
                            print(f"❌ Unexpected image_bytes type: {type(image_bytes_data)}")
                            img_bytes = None
                        
                        if img_bytes:
                            image_id = self.upload_image(img_bytes, q["image_extension"])
                        else:
                            print(f"Could not process image_bytes for question {idx}")
                            image_id = None
                            
                    except Exception as img_error:
                        print(f"Error uploading image for question {idx}: {img_error}")
                        # Continue without the image rather than failing the entire assignment
                        image_id = None

                question_data = {
                    'assignment_id': assignment_id,
                    'type': qtype,
                    'question': qtext,
                    'answer': ans,
                    'context': ctx,
                    'image_id': image_id,
                    'created_at': created_at
                }

                supabase.table('questions').insert(question_data).execute()

            print(f"✅ Assignment created successfully with ID: {assignment_id}")
            return assignment_id

        except Exception as exc:
            print(f"❌ Unexpected error during assignment create: {exc}")
            return None

    def get_assignment(self, assignment_id: str, include_questions: bool = True, include_image_bytes: bool = False) -> Optional[Dict[str, Any]]:
        """Fetch a single assignment by id. Optionally include its questions."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            # Get assignment
            result = supabase.table('assignments').select('*').eq('id', assignment_id).execute()
            
            if not result.data or len(result.data) == 0:
                return None

            assignment = result.data[0]

            if include_questions:
                # Get questions for this assignment
                questions_result = supabase.table('questions').select('*').eq('assignment_id', assignment_id).order('id').execute()
                
                questions = []
                if questions_result.data:
                    for q in questions_result.data:
                        ctx = q.get("context")
                        if ctx is not None and not isinstance(ctx, str):
                            ctx = str(ctx)
                        qdict = {
                            "id": q["id"],
                            "assignment_id": q["assignment_id"],
                            "type": q["type"],
                            "question": q["question"],
                            "answer": q["answer"],
                            "context": ctx,
                            "image_id": q.get("image_id"),
                            "created_at": q["created_at"],
                        }
                        if include_image_bytes and q.get("image_id") is not None:
                            # Get image data from images table
                            image_data = self.get_image_as_base64(q["image_id"])
                            if image_data:
                                qdict["image_bytes"] = image_data
                        questions.append(qdict)
                
                assignment["questions"] = questions

            return assignment

        except Exception as exc:
            print(f"❌ Unexpected error during assignment fetch: {exc}")
            return None

    def list_assignments(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List assignments ordered by created_at desc. Optionally limit the number of rows."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            query = supabase.table('assignments').select('*').order('created_at', desc=True)
            
            if limit and isinstance(limit, int) and limit > 0:
                query = query.limit(limit)

            result = query.execute()
            return result.data if result.data else []

        except Exception as exc:
            print(f"❌ Unexpected error during assignments list: {exc}")
            return []

    def get_assignment_questions(self, assignment_id: str, include_image_bytes: bool = False) -> List[Dict[str, Any]]:
        """Fetch questions for a specific assignment id, ordered by id."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            result = supabase.table('questions').select('*').eq('assignment_id', assignment_id).order('id').execute()
            
            questions = []
            if result.data:
                for q in result.data:
                    ctx = q.get("context")
                    if ctx is not None and not isinstance(ctx, str):
                        ctx = str(ctx)
                    item = {
                        "id": q["id"],
                        "assignment_id": q["assignment_id"],
                        "type": q["type"],
                        "question": q["question"],
                        "answer": q["answer"],
                        "context": ctx,
                        "image_id": q.get("image_id"),
                        "created_at": q["created_at"],
                    }
                    if include_image_bytes and q.get("image_id") is not None:
                        # Get image data from images table
                        image_data = self.get_image_as_base64(q["image_id"])
                        if image_data:
                            item["image_bytes"] = image_data
                    questions.append(item)
            
            return questions

        except Exception as exc:
            print(f"❌ Unexpected error during questions fetch: {exc}")
            return []

    def delete_assignment(self, assignment_id: str) -> bool:
        """Delete an assignment by id. Questions are deleted via ON DELETE CASCADE."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            result = supabase.table('assignments').delete().eq('id', assignment_id).execute()
            return bool(result.data)

        except Exception as exc:
            print(f"❌ Unexpected error during assignment delete: {exc}")
            return False

    def update_assignment_status(self, assignment_id: str, status: str) -> bool:
        """Update the status of an assignment to 'active' or 'archived'."""
        try:
            if status not in ("active", "archived"):
                print("❌ Invalid status value")
                return False

            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            result = supabase.table('assignments').update({'status': status}).eq('id', assignment_id).execute()
            return bool(result.data)

        except Exception as exc:
            print(f"❌ Unexpected error during status update: {exc}")
            return False

    def get_assignments_by_teacher(self, teacher_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get assignments created by a specific teacher."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            query = supabase.table('assignments').select('*').eq('teacher_id', teacher_id).order('created_at', desc=True)
            
            if limit and isinstance(limit, int) and limit > 0:
                query = query.limit(limit)

            result = query.execute()
            return result.data if result.data else []

        except Exception as exc:
            print(f"❌ Unexpected error during teacher assignments fetch: {exc}")
            return []


    # =============================================================================
    # SUBMISSION MANAGEMENT METHODS
    # =============================================================================

    def get_completed_submission(self, student_id: int, assignment_id: int):
        """Return the completed submission for a student/assignment if it exists."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            result = supabase.table('submissions').select('*').eq('student_id', student_id).eq('assignment_id', assignment_id).eq('status', 'completed').order('id', desc=True).limit(1).execute()
            
            return result.data[0] if result.data and len(result.data) > 0 else None

        except Exception as exc:
            print(f"❌ Unexpected error during completed submission fetch: {exc}")
            return None

    def get_active_submission(self, student_id: int, assignment_id: int):
        """Return the active (in-progress) submission for a student/assignment if it exists."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            result = supabase.table('submissions').select('*').eq('student_id', student_id).eq('assignment_id', assignment_id).eq('status', 'in_progress').order('id', desc=True).limit(1).execute()
            
            return result.data[0] if result.data and len(result.data) > 0 else None

        except Exception as exc:
            print(f"❌ Unexpected error during active submission fetch: {exc}")
            return None

    def get_all_submissions_for_assignment(self, assignment_id: int):
        """Get all submissions (completed and in-progress) for a specific assignment."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            # First get submissions
            result = supabase.table('submissions').select(
                'id, student_id, assignment_id, started_at, completed_at, overall_score, summary, status, student_feedback'
            ).eq('assignment_id', assignment_id).order('completed_at', desc=True).order('started_at', desc=True).execute()
            
            if not result.data:
                return []
            
            # Then get user information for each submission
            submissions_with_users = []
            for submission in result.data:
                student_id = submission['student_id']
                user_result = supabase.table('users').select('first_name, last_name, username').eq('id', student_id).execute()
                
                if user_result.data and len(user_result.data) > 0:
                    user_data = user_result.data[0]
                    # Flatten the user data into the submission
                    submission['first_name'] = user_data['first_name']
                    submission['last_name'] = user_data['last_name']
                    submission['username'] = user_data['username']
                    submissions_with_users.append(submission)
                else:
                    # Handle case where user data is missing
                    submission['first_name'] = 'Unknown'
                    submission['last_name'] = 'User'
                    submission['username'] = f'user_{student_id}'
                    submissions_with_users.append(submission)
            
            return submissions_with_users

        except Exception as exc:
            print(f"❌ Unexpected error during submissions fetch: {exc}")
            return []

    def get_or_create_active_submission(self, student_id: int, assignment_id: int):
        """Return the in-progress submission for a student/assignment, or create one."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                supabase = self.get_connection()
                if not supabase:
                    print("❌ No Supabase connection available")
                    return None
                
                # Check for existing in-progress submission
                result = supabase.table('submissions').select('*').eq('student_id', student_id).eq('assignment_id', assignment_id).eq('status', 'in_progress').order('id', desc=True).limit(1).execute()
                
                if result.data and len(result.data) > 0:
                    return result.data[0]

                # Create new submission
                submission_data = {
                    'student_id': student_id,
                    'assignment_id': assignment_id,
                    'started_at': datetime.now().isoformat(),
                    'status': 'in_progress'
                }
                
                create_result = supabase.table('submissions').insert(submission_data).execute()
                
                if create_result.data and len(create_result.data) > 0:
                    return create_result.data[0]
                else:
                    return None

            except Exception as exc:
                print(f"Unexpected error during submission create (attempt {attempt + 1}): {exc}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                    # Force reconnection
                    self.force_reconnect()
                else:
                    print(f"Failed to create/get submission after {max_retries} attempts")
                    return None

    def get_submission(self, submission_id: int):
        """Fetch a submission and its answers grouped by question."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            # Get submission
            result = supabase.table('submissions').select('*').eq('id', submission_id).execute()
            
            if not result.data or len(result.data) == 0:
                return None

            sub = result.data[0]

            # Get submission answers
            answers_result = supabase.table('submission_answers').select('*').eq('submission_id', submission_id).order('question_id').order('attempt_number').execute()
            
            answers_by_q = {}
            if answers_result.data:
                for r in answers_result.data:
                    qid = r["question_id"]
                    if qid not in answers_by_q:
                        answers_by_q[qid] = []
                    answers_by_q[qid].append(r)
            
            sub["answers_by_question"] = answers_by_q
            return sub

        except Exception as exc:
            print(f"❌ Unexpected error during submission fetch: {exc}")
            return None

    def get_submission_answers(self, submission_id: int):
        """Return a dict question_id -> list of attempts for a submission."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                supabase = self.get_connection()
                if not supabase:
                    print("❌ No Supabase connection available")
                    return {}

                result = supabase.table('submission_answers').select('*').eq('submission_id', submission_id).order('question_id').order('attempt_number').execute()
                
                answers_by_q = {}
                if result.data:
                    for r in result.data:
                        qid = r["question_id"]
                        answers_by_q.setdefault(qid, []).append(r)
                
                return answers_by_q

            except Exception as exc:
                print(f"Unexpected error during submission answers fetch (attempt {attempt + 1}): {exc}")
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                    # Force reconnection
                    self.force_reconnect()
                else:
                    print(f"Failed to fetch submission answers after {max_retries} attempts")
                    return {}

    def record_answer_attempt(
        self,
        submission_id: int,
        question_id: int,
        attempt_number: int,
        student_answer: str,
        grade: int,
        feedback: str,
    ) -> bool:
        """Insert a graded answer attempt for a submission/question."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            answer_data = {
                'submission_id': submission_id,
                'question_id': question_id,
                'attempt_number': attempt_number,
                'student_answer': student_answer,
                'grade': grade,
                'feedback': feedback,
                'created_at': datetime.now().isoformat()
            }

            result = supabase.table('submission_answers').insert(answer_data).execute()
            return bool(result.data)

        except Exception as exc:
            print(f"❌ Unexpected error during answer insert: {exc}")
            return False

    def mark_submission_completed(self, submission_id: int, overall_score: float, summary: str) -> bool:
        """Mark a submission as completed with overall score and summary."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            update_data = {
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'overall_score': overall_score,
                'summary': summary
            }

            result = supabase.table('submissions').update(update_data).eq('id', submission_id).execute()
            return bool(result.data)

        except Exception as exc:
            print(f"❌ Unexpected error during submission completion: {exc}")
            return False

    def update_student_feedback(self, submission_id: int, student_feedback: str) -> bool:
        """Update student feedback for a completed submission."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            result = supabase.table('submissions').update({'student_feedback': student_feedback}).eq('id', submission_id).eq('status', 'completed').execute()
            return bool(result.data)

        except Exception as exc:
            print(f"❌ Unexpected error during student feedback update: {exc}")
            return False

    def get_submissions_by_student(self, student_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get submissions by a specific student."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            query = supabase.table('submissions').select(
                'id, student_id, assignment_id, started_at, completed_at, overall_score, summary, status, assignments!inner(name)'
            ).eq('student_id', student_id).order('started_at', desc=True)
            
            if limit and isinstance(limit, int) and limit > 0:
                query = query.limit(limit)

            result = query.execute()
            return result.data if result.data else []

        except Exception as exc:
            print(f"❌ Unexpected error during student submissions fetch: {exc}")
            return []


    # =============================================================================
    # RAG QUIZZER MANAGEMENT METHODS
    # =============================================================================

    def create_rag_quizzer(self, quizzer_data):
        """
        Create a new RAG quizzer entry.

        quizzer_data: dict with the following structure:
        {
            'teacher_id': int,
            'name': str,
            'collection_id': str,
            'presentation_name': str,
            'num_slides': int,
            'num_text_items': int,
            'num_image_items': int,
            'slides': List[Dict] (optional)
        }

        Returns the quizzer id if successful, None otherwise.
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None

            # Validate required fields
            required_fields = ['teacher_id', 'name', 'collection_id', 'presentation_name', 'num_slides']
            for field in required_fields:
                if field not in quizzer_data or quizzer_data[field] is None:
                    print(f"❌ Missing required field: {field}")
                    return None

            # Insert RAG quizzer
            quizzer_insert_data = {
                'teacher_id': quizzer_data['teacher_id'],
                'name': quizzer_data['name'],
                'collection_id': quizzer_data['collection_id'],
                'presentation_name': quizzer_data['presentation_name'],
                'num_slides': quizzer_data['num_slides'],
                'num_text_items': quizzer_data.get('num_text_items', 0),
                'num_image_items': quizzer_data.get('num_image_items', 0),
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }

            result = supabase.table('rag_quizzers').insert(quizzer_insert_data).execute()
            
            if not result.data or len(result.data) == 0:
                print("❌ Failed to create RAG quizzer")
                return None

            quizzer_id = result.data[0]['id']

            # Insert slides if provided
            if 'slides' in quizzer_data and quizzer_data['slides']:
                for slide in quizzer_data['slides']:
                    slide_content = json.dumps(slide) if isinstance(slide, dict) else str(slide)
                    slide_data = {
                        'rag_quizzer_id': quizzer_id,
                        'slide_number': slide.get('slide_number', 0),
                        'slide_content': slide_content,
                        'created_at': datetime.now().isoformat()
                    }
                    supabase.table('rag_quizzer_slides').insert(slide_data).execute()

            print(f"✅ RAG Quizzer created successfully with ID: {quizzer_id}")
            return quizzer_id

        except Exception as e:
            print(f"❌ Error creating RAG quizzer: {e}")
            return None

    def get_rag_quizzers_by_teacher(self, teacher_id: int):
        """Get all RAG quizzers for a specific teacher."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return []

            result = supabase.table('rag_quizzers').select('*').eq('teacher_id', teacher_id).eq('status', 'active').order('created_at', desc=True).execute()
            
            return result.data if result.data else []

        except Exception as e:
            print(f"❌ Error getting RAG quizzers by teacher: {e}")
            return []

    def delete_rag_quizzer(self, quizzer_id: int):
        """Soft delete a RAG quizzer by setting status to 'archived'."""
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return False

            result = supabase.table('rag_quizzers').update({'status': 'archived'}).eq('id', quizzer_id).execute()

            if result.data:
                print(f"✅ RAG Quizzer {quizzer_id} archived successfully")
                return True
            else:
                print(f"❌ Failed to archive RAG Quizzer {quizzer_id}")
                return False

        except Exception as e:
            print(f"❌ Error deleting RAG quizzer: {e}")
            return False


    # =============================================================================
    # IMAGE MANAGEMENT METHODS
    # =============================================================================

    def upload_image(self, image_bytes, image_extension=None, content_type=None):
        """
        Uploads an image to the database and returns the image id
        image_bytes: bytes
        image_extension: str (optional) - file extension like 'png', 'jpg'
        content_type: str (optional) - MIME type like 'image/png'
        returns: image_id
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None
                
            file_size = len(image_bytes)
            created_at = datetime.now().isoformat()
            
            # Convert bytes to base64 for storage
            image_data_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Store in database as base64 string - ensure all values are JSON serializable
            image_data = {
                'image_data': image_data_b64,
                'image_extension': str(image_extension) if image_extension else None,
                'created_at': created_at,
                'file_size': int(file_size),
                'content_type': str(content_type) if content_type else None
            }
            
            # Remove None values to avoid serialization issues
            image_data = {k: v for k, v in image_data.items() if v is not None}
            
            result = supabase.table('images').insert(image_data).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]['id']
            else:
                print("Failed to upload image")
                return None
                
        except Exception as e:
            print(f"Unexpected error during image upload: {e}")
            return None
            
    def get_image(self, image_id):
        """
        Gets an image from the database and returns the image data and metadata
        image_id: int
        returns: dict with image_data (as bytes), image_extension, file_size, content_type, created_at
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None
                
            result = supabase.table('images').select('*').eq('id', image_id).execute()
            
            if result.data and len(result.data) > 0:
                image_record = result.data[0]
                
                # Convert hex string back to base64, then to bytes
                if image_record.get('image_data'):
                    try:
                        # Supabase stores base64 as hex, so we need to convert hex to base64 first
                        hex_data = image_record['image_data']
                        # Remove \x prefix if present
                        if hex_data.startswith('\\x'):
                            hex_data = hex_data[2:]
                        
                        # Convert hex to bytes, then to base64 string
                        hex_bytes = bytes.fromhex(hex_data)
                        base64_string = hex_bytes.decode('utf-8')
                        
                        # Now decode the base64 to get original bytes
                        image_record['image_data'] = base64.b64decode(base64_string)
                    except Exception as decode_error:
                        print(f"Error decoding image data: {decode_error}")
                        return None
                
                return image_record
            else:
                return None
                
        except Exception as e:
            print(f"❌ Unexpected error during image get: {e}")
            return None
            
    def get_image_as_base64(self, image_id):
        """
        Gets an image from the database and returns it as base64 encoded string
        image_id: int
        returns: base64 encoded string or None if error
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None
                
            result = supabase.table('images').select('image_data').eq('id', image_id).execute()
            
            if result.data and len(result.data) > 0:
                hex_data = result.data[0].get('image_data')
                if hex_data:
                    try:
                        # Remove \x prefix if present
                        if hex_data.startswith('\\x'):
                            hex_data = hex_data[2:]
                        
                        # Convert hex to bytes, then to base64 string
                        hex_bytes = bytes.fromhex(hex_data)
                        base64_string = hex_bytes.decode('utf-8')
                        
                        return base64_string
                    except Exception as e:
                        print(f"Error converting hex to base64: {e}")
                        return None
                else:
                    return None
            else:
                return None
                
        except Exception as e:
            print(f"❌ Unexpected error during image base64 conversion: {e}")
            return None

    def delete_image(self, image_id):
        """
        Deletes an image from the database
        image_id: int
        returns: True if successful, None if error
        """
        try:
            supabase = self.get_connection()
            if not supabase:
                print("❌ No Supabase connection available")
                return None
                
            result = supabase.table('images').delete().eq('id', image_id).execute()
            
            if result.data:
                return True
            else:
                print("Failed to delete image")
                return None
                
        except Exception as e:
            print(f"Unexpected error during image delete: {e}")
            return None


# =============================================================================
# CONVENIENCE ALIASES FOR BACKWARD COMPATIBILITY
# =============================================================================

# Create singleton instances for backward compatibility
UserServer = DatabaseManagerSupabase
HomeworkServer = DatabaseManagerSupabase
ImageServer = DatabaseManagerSupabase
