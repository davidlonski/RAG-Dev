import os
import hashlib
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import mysql.connector


class UserServer:
    """
    Singleton class for managing user database connections and CRUD operations.
    Handles user authentication, registration, and user management using the schema
    defined in homework_schema.sql.
    """

    _instance = None
    _mydb = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserServer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._mydb = self._configure_user_server()
            self._initialized = True

    def _configure_user_server(self):
        """Configure and return a MySQL database connection for user tables."""
        load_dotenv()
        host = os.getenv("HOMEWORK_DB_HOST")  # Using same DB as homework
        user = os.getenv("HOMEWORK_DB_USER")
        password = os.getenv("HOMEWORK_DB_PASS")
        database = os.getenv("HOMEWORK_DB_NAME")

        try:
            mydb = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
            )
            print("✅ User DB connection established successfully")
            return mydb
        except Exception as exc:
            print(f"❌ Error connecting to User DB: {exc}")
            return None

    @property
    def mydb(self):
        """Return the underlying MySQL connection object, or None if not connected."""
        return self._mydb

    def get_connection(self):
        """Return an active connection, attempting to reconnect if needed."""
        try:
            if self._mydb and self._mydb.is_connected():
                return self._mydb
            print("🔄 Reconnecting to User DB...")
            self._mydb = self._configure_user_server()
            return self._mydb
        except Exception as exc:
            print(f"❌ Error getting User DB connection: {exc}")
            return None

    def close_connection(self):
        """Close the database connection if open."""
        try:
            if self._mydb and self._mydb.is_connected():
                self._mydb.close()
                print("✅ User DB connection closed")
        except Exception as exc:
            print(f"❌ Error closing User DB connection: {exc}")

    def __del__(self):
        self.close_connection()

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
        mydb = self.get_connection()
        if not mydb:
            print("❌ No User DB connection available")
            return None

        cursor = None
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

            cursor = mydb.cursor()
            insert_sql = (
                "INSERT INTO users (username, password_hash, email, first_name, last_name, role, created_at, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')"
            )
            cursor.execute(
                insert_sql,
                (
                    user_data['username'],
                    password_hash,
                    user_data.get('email'),
                    user_data['first_name'],
                    user_data['last_name'],
                    user_data['role'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            user_id = cursor.lastrowid
            mydb.commit()
            print(f"✅ User created successfully with ID: {user_id}")
            return user_id

        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during user creation: {exc}")
            return None
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.

        Returns user data if authentication successful, None otherwise.
        """
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No User DB connection available")
                return None

            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, password_hash, email, first_name, last_name, role, created_at, last_login, status "
                "FROM users WHERE username = %s AND status = 'active'",
                (username,),
            )
            user = cursor.fetchone()
            cursor.close()

            if not user:
                return None

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
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
                'last_login': user['last_login'].isoformat() if user.get('last_login') else None,
                'status': user['status'],
            }

        except Exception as exc:
            print(f"❌ Unexpected error during authentication: {exc}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No User DB connection available")
                return None

            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, email, first_name, last_name, role, created_at, last_login, status "
                "FROM users WHERE id = %s",
                (user_id,),
            )
            user = cursor.fetchone()
            cursor.close()

            if not user:
                return None

            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
                'last_login': user['last_login'].isoformat() if user.get('last_login') else None,
                'status': user['status'],
            }

        except Exception as exc:
            print(f"❌ Unexpected error during user fetch: {exc}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No User DB connection available")
                return None

            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, username, email, first_name, last_name, role, created_at, last_login, status "
                "FROM users WHERE username = %s",
                (username,),
            )
            user = cursor.fetchone()
            cursor.close()

            if not user:
                return None

            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
                'last_login': user['last_login'].isoformat() if user.get('last_login') else None,
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
            mydb = self.get_connection()
            if not mydb:
                print("❌ No User DB connection available")
                return []

            cursor = mydb.cursor(dictionary=True)
            
            sql = "SELECT id, username, email, first_name, last_name, role, created_at, last_login, status FROM users WHERE status = 'active'"
            params = []

            if role and role in ['teacher', 'student']:
                sql += " AND role = %s"
                params.append(role)

            sql += " ORDER BY created_at DESC"

            if limit and isinstance(limit, int) and limit > 0:
                sql += " LIMIT %s"
                params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()

            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'role': row['role'],
                    'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                    'last_login': row['last_login'].isoformat() if row.get('last_login') else None,
                    'status': row['status'],
                })

            return result

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
            mydb = self.get_connection()
            if not mydb:
                print("❌ No User DB connection available")
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

            cursor = mydb.cursor()
            
            # Build dynamic SQL
            set_clause = ", ".join([f"{field} = %s" for field in valid_updates.keys()])
            sql = f"UPDATE users SET {set_clause} WHERE id = %s"
            params = list(valid_updates.values()) + [user_id]

            cursor.execute(sql, params)
            mydb.commit()
            cursor.close()

            print(f"✅ User {user_id} updated successfully")
            return True

        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during user update: {exc}")
            return False

    def update_password(self, user_id: int, new_password: str) -> bool:
        """Update user password."""
        try:
            if not new_password:
                print("❌ New password cannot be empty")
                return False

            password_hash = self._hash_password(new_password)
            return self.update_user(user_id, {'password_hash': password_hash})

        except Exception as exc:
            print(f"❌ Unexpected error during password update: {exc}")
            return False

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No User DB connection available")
                return False

            cursor = mydb.cursor()
            cursor.execute(
                "UPDATE users SET last_login = %s WHERE id = %s",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id),
            )
            mydb.commit()
            cursor.close()
            return True

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

    def create_default_users(self) -> bool:
        """
        Create default teacher and student accounts for testing.
        Returns True if successful, False otherwise.
        """
        try:
            # Create default teacher
            teacher_data = {
                'username': 'teacher',
                'password': 'teacher123',
                'email': 'teacher@example.com',
                'first_name': 'Default',
                'last_name': 'Teacher',
                'role': 'teacher'
            }
            
            # Create default student
            student_data = {
                'username': 'student',
                'password': 'student123',
                'email': 'student@example.com',
                'first_name': 'Default',
                'last_name': 'Student',
                'role': 'student'
            }

            # Check if users already exist
            if not self.get_user_by_username('teacher'):
                self.create_user(teacher_data)
                print("✅ Default teacher account created")
            
            if not self.get_user_by_username('student'):
                self.create_user(student_data)
                print("✅ Default student account created")

            return True

        except Exception as exc:
            print(f"❌ Error creating default users: {exc}")
            return False
