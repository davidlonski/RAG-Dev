import os
import uuid
import base64
from datetime import datetime
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
import mysql.connector


class HomeworkServer:
    """
    Singleton class for managing homework assignment database connections and CRUD.
    Mirrors the connection lifecycle used by `ImageServer` and provides helper methods
    to insert and fetch assignments and their questions using the schema in
    `new-app/database/homework_schema.sql`.
    """

    _instance = None
    _mydb = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HomeworkServer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._mydb = self._configure_homework_server()
            self._initialized = True

    def _configure_homework_server(self):
        """Configure and return a MySQL database connection for homework tables."""
        load_dotenv()
        host = os.getenv("HOMEWORK_DB_HOST")
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
            print("✅ Homework DB connection established successfully")
            return mydb
        except Exception as exc:
            print(f"❌ Error connecting to Homework DB: {exc}")
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
            print("🔄 Reconnecting to Homework DB...")
            self._mydb = self._configure_homework_server()
            return self._mydb
        except Exception as exc:
            print(f"❌ Error getting Homework DB connection: {exc}")
            return None

    def close_connection(self):
        """Close the database connection if open."""
        try:
            if self._mydb and self._mydb.is_connected():
                self._mydb.close()
                print("✅ Homework DB connection closed")
        except Exception as exc:
            print(f"❌ Error closing Homework DB connection: {exc}")

    def __del__(self):
        self.close_connection()

    def create_assignment(self, assignment: Dict[str, Any]) -> Optional[str]:
        """
        Insert an assignment and its questions.

        assignment: dict shaped like the session-state homework assignment, e.g.:
          {
            'collection_id': str,
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
        mydb = self.get_connection()
        if not mydb:
            print("❌ No Homework DB connection available")
            return None

        cursor = None

        try:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            name = assignment.get("name")
            collection_id = assignment.get("collection_id")
            status = assignment.get("status", "active")
            questions: List[Dict[str, Any]] = assignment.get("questions", [])
            
            for q in questions:
                qtype = q.get("type")
                qtext = q.get("question")
                ans = q.get("answer")
                ctx = q.get("context")
                if qtype == "image":
                    img_bytes = q.get("image_bytes")
                    img_ext = q.get("image_extension")
                else:
                    img_bytes = None
                    img_ext = None
            num_questions = len(questions)

            num_text_questions = sum(1 for q in questions if q.get("type") == "text")
            num_image_questions = sum(1 for q in questions if q.get("type") == "image")


            
            cursor = mydb.cursor()
            insert_assignment_sql = (
                "INSERT INTO assignments (name, collection_id, created_at, num_questions, num_text_questions, num_image_questions, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )
            cursor.execute(
                insert_assignment_sql,
                (
                    name,
                    collection_id,
                    created_at,
                    num_questions,
                    num_text_questions,
                    num_image_questions,
                    status,
                ),
            )

            insert_question_sql = (
                "INSERT INTO questions (type, question, answer, context, image_bytes, image_extension, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )


            for idx, q in enumerate(questions, start=1):
                qtype = q.get("type")
                qtext = q.get("question")
                ans = q.get("answer")
                ctx = q.get("context")
                if isinstance(ctx, list):
                    ctx = "\n".join(ctx)
                if qtype == "image" and q.get("image_bytes") and q.get("image_extension"):
                    img_bytes = base64.b64decode(q.get("image_bytes"))
                    img_ext = q.get("image_extension")
                else:
                    img_bytes = None
                    img_ext = None

                cursor.execute(
                    insert_question_sql,
                    (
                        qtype,
                        qtext,
                        ans,
                        ctx,
                        img_bytes,
                        img_ext,
                        created_at,
                    ),
                )

            mydb.commit()
            return cursor.lastrowid
        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during assignment create: {exc}")
            return None
        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

    def get_assignment(self, assignment_id: str, include_questions: bool = True, include_image_bytes: bool = False) -> Optional[Dict[str, Any]]:
        """Fetch a single assignment by id. Optionally include its questions."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return None
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, collection_id, created_at, num_questions, "
                "num_text_questions, num_image_questions, status FROM assignments WHERE id = %s",
                (assignment_id,),
            )
            row = cursor.fetchone()
            if not row:
                cursor.close()
                return None
            assignment = {
                "id": row["id"],
                "name": row["name"],
                "collection_id": row.get("collection_id"),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                "num_questions": row["num_questions"],
                "num_text_questions": row["num_text_questions"],
                "num_image_questions": row["num_image_questions"],
                "status": row["status"],
            }

            if include_questions:
                cursor.execute(
                    "SELECT id, assignment_id, type, question, answer, context, image_bytes, image_extension, created_at FROM questions WHERE assignment_id = %s ORDER BY id ASC",
                    (assignment_id,),
                )
                qrows = cursor.fetchall()
                questions: List[Dict[str, Any]] = []
                for q in qrows:
                    ctx = q.get("context")
                    if ctx is not None and not isinstance(ctx, str):
                        ctx = str(ctx)
                    qdict: Dict[str, Any] = {
                        "id": q["id"],
                        "assignment_id": q["assignment_id"],
                        "type": q["type"],
                        "question": q["question"],
                        "answer": q["answer"],
                        "context": ctx,
                        "image_extension": q.get("image_extension"),
                        "created_at": q["created_at"].isoformat() if q.get("created_at") else None,
                    }
                    if include_image_bytes and q.get("image_bytes") is not None:
                        qdict["image_bytes"] = base64.b64encode(q["image_bytes"]).decode("utf-8")
                    questions.append(qdict)
                assignment["questions"] = questions

            cursor.close()
            return assignment
        except Exception as exc:
            print(f"❌ Unexpected error during assignment fetch: {exc}")
            return None

    def list_assignments(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List assignments ordered by created_at desc. Optionally limit the number of rows."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return []
            cursor = mydb.cursor(dictionary=True)
            sql = (
                "SELECT id, name, collection_id, created_at, num_questions, "
                "num_text_questions, num_image_questions, status FROM assignments ORDER BY created_at DESC"
            )
            if limit and isinstance(limit, int) and limit > 0:
                sql += " LIMIT %s"
                cursor.execute(sql, (limit,))
            else:
                cursor.execute(sql)
            rows = cursor.fetchall()
            cursor.close()
            result: List[Dict[str, Any]] = []
            for row in rows:
                result.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "collection_id": row.get("collection_id"),
                        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                        "num_questions": row["num_questions"],
                        "num_text_questions": row["num_text_questions"],
                        "num_image_questions": row["num_image_questions"],
                        "status": row["status"],
                    }
                )
            return result
        except Exception as exc:
            print(f"❌ Unexpected error during assignments list: {exc}")
            return []

    def get_assignment_questions(self, assignment_id: str, include_image_bytes: bool = False) -> List[Dict[str, Any]]:
        """Fetch questions for a specific assignment id, ordered by id."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return []
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, assignment_id, type, question, answer, context, image_bytes, image_extension, created_at FROM questions WHERE assignment_id = %s ORDER BY id ASC",
                (assignment_id,),
            )
            qrows = cursor.fetchall()
            cursor.close()
            result: List[Dict[str, Any]] = []
            for q in qrows:
                ctx = q.get("context")
                if ctx is not None and not isinstance(ctx, str):
                    ctx = str(ctx)
                item: Dict[str, Any] = {
                    "id": q["id"],
                    "assignment_id": q["assignment_id"],
                    "type": q["type"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "context": ctx,
                    "image_extension": q.get("image_extension"),
                    "created_at": q["created_at"].isoformat() if q.get("created_at") else None,
                }
                if include_image_bytes and q.get("image_bytes") is not None:
                    item["image_bytes"] = base64.b64encode(q["image_bytes"]).decode("utf-8")
                result.append(item)
            return result
        except Exception as exc:
            print(f"❌ Unexpected error during questions fetch: {exc}")
            return []

    def delete_assignment(self, assignment_id: str) -> bool:
        """Delete an assignment by id. Questions are deleted via ON DELETE CASCADE."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return False
            cursor = mydb.cursor()
            cursor.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))
            mydb.commit()
            cursor.close()
            return True
        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during assignment delete: {exc}")
            return False

    def update_assignment_status(self, assignment_id: str, status: str) -> bool:
        """Update the status of an assignment to 'active' or 'archived'."""
        try:
            if status not in ("active", "archived"):
                print("❌ Invalid status value")
                return False
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return False
            cursor = mydb.cursor()
            cursor.execute("UPDATE assignments SET status = %s WHERE id = %s", (status, assignment_id))
            mydb.commit()
            cursor.close()
            return True
        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during status update: {exc}")
            return False
