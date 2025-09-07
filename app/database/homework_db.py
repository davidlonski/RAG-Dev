import os
import uuid
import base64
import json
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
        mydb = self.get_connection()
        if not mydb:
            print("❌ No Homework DB connection available")
            return None

        cursor = None

        try:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
            name = assignment.get("name")
            collection_id = assignment.get("collection_id")
            teacher_id = assignment.get("teacher_id")
            status = assignment.get("status", "active")
            questions: List[Dict[str, Any]] = assignment.get("questions", [])
            
            # Validate teacher_id is provided
            if not teacher_id:
                print("❌ teacher_id is required for assignment creation")
                return None
            
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
                "INSERT INTO assignments (name, collection_id, teacher_id, created_at, num_questions, num_text_questions, num_image_questions, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            )
            cursor.execute(
                insert_assignment_sql,
                (
                    name,
                    collection_id,
                    teacher_id,
                    created_at,
                    num_questions,
                    num_text_questions,
                    num_image_questions,
                    status,
                ),
            )

            assignment_id = cursor.lastrowid

            insert_question_sql = (
                "INSERT INTO questions (assignment_id, type, question, answer, context, image_id, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"
            )


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
                    from database.image_db import ImageServer
                    image_server = ImageServer()
                    img_bytes = base64.b64decode(q.get("image_bytes"))
                    image_id = image_server.upload_image(img_bytes, q["image_extension"])

                cursor.execute(
                    insert_question_sql,
                    (
                        assignment_id,
                        qtype,
                        qtext,
                        ans,
                        ctx,
                        image_id,
                        created_at,
                    ),
                )

            mydb.commit()
            return assignment_id
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
                "SELECT id, name, collection_id, teacher_id, created_at, num_questions, "
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
                "teacher_id": row.get("teacher_id"),
                "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                "num_questions": row["num_questions"],
                "num_text_questions": row["num_text_questions"],
                "num_image_questions": row["num_image_questions"],
                "status": row["status"],
            }

            if include_questions:
                cursor.execute(
                    "SELECT id, assignment_id, type, question, answer, context, image_id, created_at FROM questions WHERE assignment_id = %s ORDER BY id ASC",
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
                        "image_id": q.get("image_id"),
                        "created_at": q["created_at"].isoformat() if q.get("created_at") else None,
                    }
                    if include_image_bytes and q.get("image_id") is not None:
                        # Get image data from images table
                        from database.image_db import ImageServer
                        image_server = ImageServer()
                        image_data = image_server.get_image_as_base64(q["image_id"])
                        if image_data:
                            qdict["image_bytes"] = image_data
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
                "SELECT id, name, collection_id, teacher_id, created_at, num_questions, "
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
                        "teacher_id": row.get("teacher_id"),
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
                "SELECT id, assignment_id, type, question, answer, context, image_id, created_at FROM questions WHERE assignment_id = %s ORDER BY id ASC",
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
                    "image_id": q.get("image_id"),
                    "created_at": q["created_at"].isoformat() if q.get("created_at") else None,
                }
                if include_image_bytes and q.get("image_id") is not None:
                    # Get image data from images table
                    from database.image_db import ImageServer
                    image_server = ImageServer()
                    image_data = image_server.get_image_as_base64(q["image_id"])
                    if image_data:
                        item["image_bytes"] = image_data
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

    # -------------------------
    # Submissions CRUD
    # -------------------------

    def get_completed_submission(self, student_id: int, assignment_id: int):
        """Return the completed submission for a student/assignment if it exists."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return None
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, student_id, assignment_id, started_at, completed_at, overall_score, summary, status, student_feedback "
                "FROM submissions WHERE student_id = %s AND assignment_id = %s AND status = 'completed' ORDER BY id DESC LIMIT 1",
                (student_id, assignment_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row
        except Exception as exc:
            print(f"❌ Unexpected error during completed submission fetch: {exc}")
            return None

    def get_active_submission(self, student_id: int, assignment_id: int):
        """Return the active (in-progress) submission for a student/assignment if it exists."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return None
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, student_id, assignment_id, started_at, completed_at, overall_score, summary, status, student_feedback "
                "FROM submissions WHERE student_id = %s AND assignment_id = %s AND status = 'in_progress' ORDER BY id DESC LIMIT 1",
                (student_id, assignment_id),
            )
            row = cursor.fetchone()
            cursor.close()
            return row
        except Exception as exc:
            print(f"❌ Unexpected error during active submission fetch: {exc}")
            return None

    def get_all_submissions_for_assignment(self, assignment_id: int):
        """Get all submissions (completed and in-progress) for a specific assignment."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return []
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT s.id, s.student_id, s.assignment_id, s.started_at, s.completed_at, s.overall_score, s.summary, s.status, s.student_feedback, "
                "u.first_name, u.last_name, u.username "
                "FROM submissions s "
                "JOIN users u ON s.student_id = u.id "
                "WHERE s.assignment_id = %s "
                "ORDER BY s.completed_at DESC, s.started_at DESC",
                (assignment_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
        except Exception as exc:
            print(f"❌ Unexpected error during submissions fetch: {exc}")
            return []

    def get_or_create_active_submission(self, student_id: int, assignment_id: int):
        """Return the in-progress submission for a student/assignment, or create one."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return None
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, student_id, assignment_id, started_at, completed_at, overall_score, summary, status, student_feedback "
                "FROM submissions WHERE student_id = %s AND assignment_id = %s AND status = 'in_progress' ORDER BY id DESC LIMIT 1",
                (student_id, assignment_id),
            )
            row = cursor.fetchone()
            if row:
                cursor.close()
                return row

            # Create new submission
            cursor.execute(
                "INSERT INTO submissions (student_id, assignment_id, started_at, status) VALUES (%s, %s, %s, 'in_progress')",
                (student_id, assignment_id, datetime.now().strftime("%Y-%m-%d %H:%M")),
            )
            mydb.commit()
            sub_id = cursor.lastrowid
            cursor.close()
            return {
                "id": sub_id,
                "student_id": student_id,
                "assignment_id": assignment_id,
                "started_at": datetime.now().isoformat(timespec='minutes'),
                "completed_at": None,
                "overall_score": None,
                "summary": None,
                "status": "in_progress",
            }
        except Exception as exc:
            print(f"❌ Unexpected error during submission create: {exc}")
            return None

    def get_submission(self, submission_id: int):
        """Fetch a submission and its answers grouped by question."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return None
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, student_id, assignment_id, started_at, completed_at, overall_score, summary, status, student_feedback FROM submissions WHERE id = %s",
                (submission_id,),
            )
            sub = cursor.fetchone()
            if not sub:
                cursor.close()
                return None

            cursor.execute(
                "SELECT id, submission_id, question_id, attempt_number, student_answer, grade, feedback, created_at "
                "FROM submission_answers WHERE submission_id = %s ORDER BY question_id ASC, attempt_number ASC",
                (submission_id,),
            )
            rows = cursor.fetchall()
            cursor.close()

            answers_by_q = {}
            for r in rows:
                qid = r["question_id"] if isinstance(r, dict) else r[2]
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
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return {}
            cursor = mydb.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, submission_id, question_id, attempt_number, student_answer, grade, feedback, created_at "
                "FROM submission_answers WHERE submission_id = %s ORDER BY question_id ASC, attempt_number ASC",
                (submission_id,),
            )
            rows = cursor.fetchall()
            cursor.close()
            answers_by_q = {}
            for r in rows:
                qid = r["question_id"]
                answers_by_q.setdefault(qid, []).append(r)
            return answers_by_q
        except Exception as exc:
            print(f"❌ Unexpected error during submission answers fetch: {exc}")
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
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return False
            cursor = mydb.cursor()
            cursor.execute(
                "INSERT INTO submission_answers (submission_id, question_id, attempt_number, student_answer, grade, feedback, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    submission_id,
                    question_id,
                    attempt_number,
                    student_answer,
                    grade,
                    feedback,
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                ),
            )
            mydb.commit()
            cursor.close()
            return True
        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during answer insert: {exc}")
            return False

    def mark_submission_completed(self, submission_id: int, overall_score: float, summary: str) -> bool:
        """Mark a submission as completed with overall score and summary."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return False
            cursor = mydb.cursor()
            cursor.execute(
                "UPDATE submissions SET status='completed', completed_at=%s, overall_score=%s, summary=%s WHERE id=%s",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), overall_score, summary, submission_id),
            )
            mydb.commit()
            cursor.close()
            return True
        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during submission completion: {exc}")
            return False

    def update_student_feedback(self, submission_id: int, student_feedback: str) -> bool:
        """Update student feedback for a completed submission."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return False
            cursor = mydb.cursor()
            cursor.execute(
                "UPDATE submissions SET student_feedback=%s WHERE id=%s AND status='completed'",
                (student_feedback, submission_id),
            )
            mydb.commit()
            cursor.close()
            return True
        except Exception as exc:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Unexpected error during student feedback update: {exc}")
            return False

    def get_assignments_by_teacher(self, teacher_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get assignments created by a specific teacher."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return []
            cursor = mydb.cursor(dictionary=True)
            sql = (
                "SELECT id, name, collection_id, teacher_id, created_at, num_questions, "
                "num_text_questions, num_image_questions, status FROM assignments "
                "WHERE teacher_id = %s ORDER BY created_at DESC"
            )
            params = [teacher_id]
            
            if limit and isinstance(limit, int) and limit > 0:
                sql += " LIMIT %s"
                params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "name": row["name"],
                    "collection_id": row.get("collection_id"),
                    "teacher_id": row.get("teacher_id"),
                    "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                    "num_questions": row["num_questions"],
                    "num_text_questions": row["num_text_questions"],
                    "num_image_questions": row["num_image_questions"],
                    "status": row["status"],
                })
            return result
        except Exception as exc:
            print(f"❌ Unexpected error during teacher assignments fetch: {exc}")
            return []

    def get_submissions_by_student(self, student_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get submissions by a specific student."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No Homework DB connection available")
                return []
            cursor = mydb.cursor(dictionary=True)
            sql = (
                "SELECT s.id, s.student_id, s.assignment_id, s.started_at, s.completed_at, "
                "s.overall_score, s.summary, s.status, a.name as assignment_name "
                "FROM submissions s "
                "JOIN assignments a ON s.assignment_id = a.id "
                "WHERE s.student_id = %s ORDER BY s.started_at DESC"
            )
            params = [student_id]
            
            if limit and isinstance(limit, int) and limit > 0:
                sql += " LIMIT %s"
                params.append(limit)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            
            result = []
            for row in rows:
                result.append({
                    "id": row["id"],
                    "student_id": row["student_id"],
                    "assignment_id": row["assignment_id"],
                    "assignment_name": row["assignment_name"],
                    "started_at": row["started_at"].isoformat() if row.get("started_at") else None,
                    "completed_at": row["completed_at"].isoformat() if row.get("completed_at") else None,
                    "overall_score": row["overall_score"],
                    "summary": row["summary"],
                    "status": row["status"],
                })
            return result
        except Exception as exc:
            print(f"❌ Unexpected error during student submissions fetch: {exc}")
            return []

    # RAG Quizzer Methods (Integrated from rag_quizzer_db.py)
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
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
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

            except Exception as e:
                try:
                    if mydb:
                        mydb.rollback()
                except Exception:
                    pass
                print(f"❌ Unexpected error during RAG quizzer creation: {e}")
                return None
            finally:
                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass

        except Exception as e:
            print(f"❌ Error creating RAG quizzer: {e}")
            return None

    def get_rag_quizzers_by_teacher(self, teacher_id: int):
        """Get all RAG quizzers for a specific teacher."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
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

        except Exception as e:
            print(f"❌ Error getting RAG quizzers by teacher: {e}")
            return []

    def delete_rag_quizzer(self, quizzer_id: int):
        """Soft delete a RAG quizzer by setting status to 'archived'."""
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
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

        except Exception as e:
            try:
                if mydb:
                    mydb.rollback()
            except Exception:
                pass
            print(f"❌ Error deleting RAG quizzer: {e}")
            return False 