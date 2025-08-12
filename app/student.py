import streamlit as st
import os
import sys
import base64
from typing import Dict, List
from datetime import datetime

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from database.homework_server import HomeworkServer
from pptx_rag_quizzer.quiz_master import QuizMaster
from pptx_rag_quizzer.rag_core import RAGCore


st.set_page_config(page_title="Student Portal", page_icon="🧑‍🎓", layout="wide")

ss = st.session_state

# Initialize session state
if "student_id" not in ss:
    ss.student_id = "student_001"  # In real app, get from auth
if "homework_server" not in ss:
    ss.homework_server = HomeworkServer()
if "rag_core" not in ss:
    ss.rag_core = RAGCore()
if "quiz_master" not in ss:
    ss.quiz_master = QuizMaster(ss.rag_core)
if "page" not in ss:
    ss.page = "assignments"
if "current_assignment" not in ss:
    ss.current_assignment = None
if "submission" not in ss:
    ss.submission = None
if "answers_draft" not in ss:
    ss.answers_draft = {}  # question_id -> str
if "attempts_used" not in ss:
    ss.attempts_used = {}  # question_id -> int


def load_assignment(assignment_id: int):
    assignment = ss.homework_server.get_assignment(assignment_id, include_questions=True, include_image_bytes=False)
    ss.current_assignment = assignment
    # Get or create active submission
    submission = ss.homework_server.get_or_create_active_submission(ss.student_id, assignment_id)
    ss.submission = submission
    # Load existing attempts to compute attempts used
    answers = ss.homework_server.get_submission_answers(submission["id"]) if submission else {}
    ss.attempts_used = {qid: len(attempts) for qid, attempts in answers.items()}
    # Pre-fill drafts with last attempt answer if exists
    ss.answers_draft = {}
    for q in assignment.get("questions", []):
        qid = q["id"]
        prior = answers.get(qid, [])
        ss.answers_draft[qid] = prior[-1]["student_answer"] if prior else ""


def view_assignments():
    st.header("📚 Available Assignments")
    assignments = ss.homework_server.list_assignments()
    if not assignments:
        st.info("No assignments available yet.")
        return
    for a in assignments:
        with st.expander(f"{a['name']} — {a['num_questions']} questions"):
            st.write(f"Created: {a.get('created_at','')}")
            st.write(f"Text: {a['num_text_questions']}, Image: {a['num_image_questions']}")
            if st.button("Start / Continue", key=f"start_{a['id']}"):
                load_assignment(a["id"]) 
                ss.page = "take"
                st.rerun()


def grade_and_save(answers: Dict[int, str], finalize: bool = False):
    assignment = ss.current_assignment
    submission = ss.submission
    if not assignment or not submission:
        st.error("No assignment or submission found.")
        return

    questions = assignment.get("questions", [])
    graded_results: List[Dict] = []

    for q in questions:
        qid = q["id"]
        student_answer = answers.get(qid, "").strip()
        if not student_answer:
            continue
        used = ss.attempts_used.get(qid, 0)
        if used >= 2:
            continue
        attempt_number = used + 1
        grade, feedback = ss.quiz_master.grade_question(q, student_answer)
        graded_results.append({"question_id": qid, "attempt": attempt_number, "grade": grade, "feedback": feedback})
        ok = ss.homework_server.record_answer_attempt(submission_id=submission["id"], question_id=qid, attempt_number=attempt_number, student_answer=student_answer, grade=grade, feedback=feedback)
        if ok:
            ss.attempts_used[qid] = attempt_number

    if graded_results:
        for r in graded_results:
            st.write(f"Q{r['question_id']} attempt {r['attempt']} → grade {r['grade']}: {r['feedback']}")
        st.success("Saved and graded current answers.")
    else:
        st.info("No new answers to grade.")

    if finalize:
        # Compute overall score from latest attempts of all questions
        answers_map = ss.homework_server.get_submission_answers(submission["id"]) or {}
        num_questions = max(1, len(questions))
        latest_sum = 0
        for q in questions:
            qid = q["id"]
            attempts = answers_map.get(qid, [])
            latest_sum += attempts[-1]["grade"] if attempts else 0
        max_per_q = 2
        avg = latest_sum / (num_questions * max_per_q)
        percent = round(avg * 100, 1)
        # Basic summary prompt
        summary_prompt = f"""
Generate a concise summary of the student's performance in one short paragraph, including strengths and weaknesses.
Use this context:
- Assignment name: {assignment.get('name')}
- Questions: {num_questions}
- Total raw points: {latest_sum} (out of {num_questions*max_per_q})
Format as plain text.
"""
        try:
            summary = ss.rag_core.prompt_gemini(summary_prompt)
        except Exception:
            summary = "Summary unavailable."
        ss.homework_server.mark_submission_completed(submission_id=submission["id"], overall_score=percent, summary=summary)
        st.success(f"Assignment submitted. Final score: {percent}%")
        ss.page = "assignments"


def take_assignment():
    assignment = ss.current_assignment
    submission = ss.submission
    if not assignment:
        st.info("Select an assignment to begin.")
        return
    st.header(f"📝 {assignment['name']}")
    st.caption(f"Submission ID: {submission['id']} — Started: {submission['started_at']}")

    # Load current attempts from DB for display and gating
    answers_by_q = ss.homework_server.get_submission_answers(submission['id'])

    # Load image bytes for questions (base64) when available
    image_qs = ss.homework_server.get_assignment_questions(assignment['id'], include_image_bytes=True)
    image_lookup = {item['id']: item for item in image_qs}

    # Show questions
    for q in assignment.get("questions", []):
        qid = q["id"]
        st.subheader(f"Question {qid}")
        st.write(q["question"])
        if q.get("type") == "image":
            st.caption("This is an image-based question. Answer based on the image context.")
            img_info = image_lookup.get(qid)
            img_b64 = img_info.get("image_bytes") if img_info else None
            if img_b64:
                try:
                    st.image(base64.b64decode(img_b64), use_container_width=True)
                except Exception:
                    st.warning("Unable to display image preview for this question.")
        else:
            st.caption("This is a text-based question. Answer based on the text context.")

        attempts = answers_by_q.get(qid, [])
        used = len(attempts)
        last_grade = attempts[-1]["grade"] if attempts else None
        last_feedback = attempts[-1]["feedback"] if attempts else None
        last_answer = attempts[-1]["student_answer"] if attempts else None

        if attempts:
            st.markdown(f"- Attempts: {used}")
            st.markdown(f"- Last grade: {last_grade if last_grade is not None else '-'}")
            if last_feedback:
                st.info(f"Feedback: {last_feedback}")
            if last_answer:
                with st.expander("View last submitted answer"):
                    st.write(last_answer)

        # Gate input
        if used >= 2 or last_grade == 2:
            st.success("No more attempts allowed for this question.")
            continue

        answer = st.text_area("Your answer", key=f"ans_{qid}", value=ss.answers_draft.get(qid, ""))
        ss.answers_draft[qid] = answer

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Save & Grade Now"):
            grade_and_save(ss.answers_draft, finalize=False)
            st.rerun()
    with col2:
        if st.button("Submit Final"):
            grade_and_save(ss.answers_draft, finalize=True)
            st.rerun()
    with col3:
        if st.button("Back to Assignments"):
            ss.page = "assignments"
            st.rerun()


st.title("🧑‍🎓 Student Portal")

with st.sidebar:
    st.write(f"Student: {ss.student_id}")
    choice = st.radio("Navigate", ["assignments", "take"], index=0 if ss.page == "assignments" else 1)
    if choice != ss.page:
        ss.page = choice
        st.rerun()

if ss.page == "assignments":
    view_assignments()
elif ss.page == "take":
    take_assignment()


