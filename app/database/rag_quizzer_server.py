import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import mysql.connector


class RAGQuizzerServer:
    """
    Singleton class for managing RAG quizzer database connections and CRUD operations.
    Handles persistence of RAG quizzer data including presentations and collections.
    """

    _instance = None
    _mydb = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAGQuizzerServer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._mydb = self._configure_rag_quizzer_server()
            self._initialized = True

    def _configure_rag_quizzer_server(self):
        """Configure and return a MySQL database connection for RAG quizzer tables."""
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
            print("✅ RAG Quizzer DB connection established successfully")
            return mydb
        except Exception as exc:
            print(f"❌ Error connecting to RAG Quizzer DB: {exc}")
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
            print("🔄 Reconnecting to RAG Quizzer DB...")
            self._mydb = self._configure_rag_quizzer_server()
            return self._mydb
        except Exception as exc:
            print(f"❌ Error getting RAG Quizzer DB connection: {exc}")
            return None

    def close_connection(self):
        """Close the database connection if open."""
        try:
            if self._mydb and self._mydb.is_connected():
                self._mydb.close()
                print("✅ RAG Quizzer DB connection closed")
        except Exception as exc:
            print(f"❌ Error closing RAG Quizzer DB connection: {exc}")

    def __del__(self):
        self.close_connection()

    def create_rag_quizzer(self, quizzer_data: Dict[str, Any]) -> Optional[int]:
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
        mydb = self.get_connection()
        if not mydb:
            print("❌ No RAG Quizzer DB connection available")
            return None

        cursor = None
        try:
            # Validate required fields
            required_fields = ['teacher_id', 'name', 'collection_id', 'presentation_name', 'num_slides']
            for field in required_fields:
                if field not in quizzer_data or quizzer_data[field] is None:
                    print(f"❌ Missing required field: {field}")
                    return None

            cursor = mydb.cursor()
            
            # Insert RAG quizzer
            insert_sql = (
                "INSERT INTO rag_quizzers (teacher_id, name, collection_id, presentation_name, "
                "num_slides, num_text_items, num_image_items, created_at, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')"
            )
            cursor.execute(
                insert_sql,
                (
                    quizzer_data['teacher_id'],
                    quizzer_data['name'],
                    quizzer_data['collection_id'],
                    quizzer_data['presentation_name'],
                    quizzer_data['num_slides'],
                    quizzer_data.get('num_text_items', 0),
                    quizzer_data.get('num_image_items', 0),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )

            quizzer_id = cursor.lastrowid

            # Insert slides if provided
            if 'slides' in quizzer_data and quizzer_data['slides']:
                slide_insert_sql = (
                    "INSERT INTO rag_quizzer_slides (rag_quizzer_id, slide_number, slide_content, created_at) "
                    "VALUES (%s, %s, %s, %s)"
                )
                for slide in quizzer_data['slides']:
                    slide_content = json.dumps(slide) if isinstance(slide, dict) else str(slide)
                    cursor.execute(
                        slide_insert_sql,
                        (
                            quizzer_id,
                            slide.get('slide_number', 0),
                            slide_content,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )

            mydb.commit()
            print(f"✅ RAG Quizzer created successfully with ID: {quizzer_id}")
            return quizzer_id

        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during RAG quizzer creation: {exc}")
            return None
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

    def get_rag_quizzers_by_teacher(self, teacher_id: int) -> List[Dict[str, Any]]:
        """Get all RAG quizzers for a specific teacher."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No RAG Quizzer DB connection available")
                return []

            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, teacher_id, name, collection_id, presentation_name, "
                "num_slides, num_text_items, num_image_items, created_at, status "
                "FROM rag_quizzers WHERE teacher_id = %s AND status = 'active' "
                "ORDER BY created_at DESC",
                (teacher_id,),
            )
            rows = cursor.fetchall()
            cursor.close()

            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'teacher_id': row['teacher_id'],
                    'name': row['name'],
                    'collection_id': row['collection_id'],
                    'presentation_name': row['presentation_name'],
                    'num_slides': row['num_slides'],
                    'num_text_items': row['num_text_items'],
                    'num_image_items': row['num_image_items'],
                    'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                    'status': row['status'],
                })

            return result

        except Exception as exc:
            print(f"❌ Unexpected error during RAG quizzers fetch: {exc}")
            return []

    def get_rag_quizzer_by_id(self, quizzer_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific RAG quizzer by ID."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No RAG Quizzer DB connection available")
                return None

            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, teacher_id, name, collection_id, presentation_name, "
                "num_slides, num_text_items, num_image_items, created_at, status "
                "FROM rag_quizzers WHERE id = %s",
                (quizzer_id,),
            )
            row = cursor.fetchone()
            cursor.close()

            if not row:
                return None

            return {
                'id': row['id'],
                'teacher_id': row['teacher_id'],
                'name': row['name'],
                'collection_id': row['collection_id'],
                'presentation_name': row['presentation_name'],
                'num_slides': row['num_slides'],
                'num_text_items': row['num_text_items'],
                'num_image_items': row['num_image_items'],
                'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                'status': row['status'],
            }

        except Exception as exc:
            print(f"❌ Unexpected error during RAG quizzer fetch: {exc}")
            return None

    def delete_rag_quizzer(self, quizzer_id: int) -> bool:
        """Soft delete a RAG quizzer by setting status to 'archived'."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No RAG Quizzer DB connection available")
                return False

            cursor = mydb.cursor()
            cursor.execute(
                "UPDATE rag_quizzers SET status = 'archived' WHERE id = %s",
                (quizzer_id,),
            )
            mydb.commit()
            cursor.close()

            print(f"✅ RAG Quizzer {quizzer_id} archived successfully")
            return True

        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during RAG quizzer deletion: {exc}")
            return False

    def get_rag_quizzer_slides(self, quizzer_id: int) -> List[Dict[str, Any]]:
        """Get slides for a specific RAG quizzer."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No RAG Quizzer DB connection available")
                return []

            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, rag_quizzer_id, slide_number, slide_content, created_at "
                "FROM rag_quizzer_slides WHERE rag_quizzer_id = %s ORDER BY slide_number ASC",
                (quizzer_id,),
            )
            rows = cursor.fetchall()
            cursor.close()

            result = []
            for row in rows:
                try:
                    slide_content = json.loads(row['slide_content']) if row['slide_content'] else {}
                except:
                    slide_content = {'content': row['slide_content']}

                result.append({
                    'id': row['id'],
                    'rag_quizzer_id': row['rag_quizzer_id'],
                    'slide_number': row['slide_number'],
                    'slide_content': slide_content,
                    'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
                })

            return result

        except Exception as exc:
            print(f"❌ Unexpected error during RAG quizzer slides fetch: {exc}")
            return []
