import streamlit as st
import os
import sys
import base64
from typing import Dict, List
from datetime import datetime

# Ensure local imports work
sys.path.append(os.path.dirname(__file__))

from database.db_psql import HomeworkServer, UserServer
from pptx_rag_quizzer.quiz_master import QuizMaster
from pptx_rag_quizzer.rag_core import RAGCore


st.set_page_config(
    page_title="Student Portal", 
    page_icon="🧑‍🎓", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for consistent button sizing
st.markdown("""
<style>
    /* Set fixed width for all buttons except those with use_container_width */
    .stButton > button:not([data-testid="baseButton-secondary"]) {
        width: 200px !important;
        min-width: 200px !important;
        max-width: 200px !important;
    }
    
    /* Keep full width for navigation buttons */
    .stButton > button[data-testid="baseButton-secondary"] {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

ss = st.session_state

# Initialize session state
if "homework_server" not in ss:
    ss.homework_server = HomeworkServer()
if "user_server" not in ss:
    ss.user_server = UserServer()
if "current_user" not in ss:
    ss.current_user = None
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
    
    # Check if there's already a completed submission for this student/assignment
    completed_submission = ss.homework_server.get_completed_submission(ss.current_user['id'], assignment_id)
    if completed_submission:
        ss.submission = completed_submission
        return
    
    # Get or create active submission
    submission = ss.homework_server.get_or_create_active_submission(ss.current_user['id'], assignment_id)
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
        # Check if student has a completed submission for this assignment
        completed_submission = ss.homework_server.get_completed_submission(ss.current_user['id'], a['id'])
        active_submission = ss.homework_server.get_active_submission(ss.current_user['id'], a['id'])
        
        if completed_submission:
            # Assignment completed
            status_text = f"✅ COMPLETED - Score: {completed_submission['overall_score']}%"
            button_text = "📊 View Results"
        elif active_submission:
            # Assignment in progress
            status_text = "🔄 IN PROGRESS"
            button_text = "📝 Continue Assignment"
        else:
            # Assignment not started
            status_text = "📋 NOT STARTED"
            button_text = "🚀 Start Assignment"
        
        with st.expander(f"{a['name']} — {a['num_questions']} questions"):
            st.write(f"**Status:** {status_text}")
            st.write(f"**Questions:** Text: {a['num_text_questions']}, Image: {a['num_image_questions']}")
            
            if st.button(button_text, key=f"start_{a['id']}"):
                load_assignment(a["id"]) 
                ss.page = "take"
                st.rerun()


def display_completed_assignment(assignment, submission):
    """Display a completed assignment with all attempts and grades."""
    st.header(f"📝 {assignment['name']} - COMPLETED")
    st.caption(f"Submission ID: {submission['id']} — Completed: {submission['completed_at']}")
    st.success(f"🎉 Final Score: {submission['overall_score']}%")
    
    if submission.get('summary'):
        st.info(f"**Summary:** {submission['summary']}")
    
    # Load all answers
    answers_by_q = ss.homework_server.get_submission_answers(submission['id'])
    
    # Load image bytes for questions
    image_qs = ss.homework_server.get_assignment_questions(assignment['id'], include_image_bytes=True)
    image_lookup = {item['id']: item for item in image_qs}
    
    # Show all questions with their attempts
    for question_index, q in enumerate(assignment.get("questions", []), 1):
        qid = q["id"]
        st.subheader(f"Question {question_index}")
        st.write(q["question"])
        
        if q.get("type") == "image":
            st.caption("This was an image-based question.")
            img_info = image_lookup.get(qid)
            img_b64 = img_info.get("image_bytes") if img_info else None
            if img_b64:
                try:
                    st.image(base64.b64decode(img_b64), width=1000, caption="Question Image")
                except Exception:
                    st.warning("Unable to display image preview.")
        
        attempts = answers_by_q.get(qid, [])
        if attempts:
            for i, attempt in enumerate(attempts, 1):
                with st.expander(f"Attempt {i} - Grade: {attempt['grade']}/2"):
                    st.write(f"**Your answer:** {attempt['student_answer']}")
                    if attempt['feedback']:
                        st.info(f"**Feedback:** {attempt['feedback']}")
        else:
            st.warning("No attempts recorded for this question.")
    
    # Student feedback section
    st.markdown("---")
    st.subheader("📝 Assignment Feedback")
    st.write("Please share your thoughts about this assignment to help improve future learning experiences.")
    
    # Check if feedback already exists
    existing_feedback = submission.get('student_feedback', '')
    
    if existing_feedback:
        st.info(f"**Your previous feedback:** {existing_feedback}")
        if st.button("Edit Feedback", key="edit_feedback"):
            ss.editing_feedback = True
            st.rerun()
    else:
        ss.editing_feedback = True
    
    if ss.get('editing_feedback', False):
        feedback = st.text_area(
            "Share your feedback about this assignment:",
            value=existing_feedback,
            height=100,
            placeholder="e.g., What did you find challenging? What was helpful? Any suggestions for improvement?",
            key="feedback_input"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Feedback", key="save_feedback"):
                if feedback.strip():
                    success = ss.homework_server.update_student_feedback(submission['id'], feedback.strip())
                    if success:
                        st.success("✅ Feedback saved successfully!")
                        ss.editing_feedback = False
                        # Refresh submission data
                        ss.submission = ss.homework_server.get_completed_submission(ss.current_user['id'], assignment['id'])
                        st.rerun()
                    else:
                        st.error("❌ Failed to save feedback. Please try again.")
                else:
                    st.warning("⚠️ Please enter some feedback before saving.")
        
        with col2:
            if st.button("Cancel", key="cancel_feedback"):
                ss.editing_feedback = False
                st.rerun()
    
    # Back button
    if st.button("← Back to Assignments", key="student_back1"):
        ss.page = "assignments"
        st.rerun()


def grade_and_save(answers: Dict[int, str], finalize: bool = False):
    assignment = ss.current_assignment
    submission = ss.submission
    if not assignment or not submission:
        st.error("No assignment or submission found.")
        return

    questions = assignment.get("questions", [])
    graded_results: List[Dict] = []

    # Create mapping from question ID to sequential number
    question_id_to_number = {q["id"]: i + 1 for i, q in enumerate(questions)}

    # Grade only questions that have answers and haven't reached max attempts
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
        graded_results.append({"question_id": qid, "question_number": question_id_to_number[qid], "attempt": attempt_number, "grade": grade, "feedback": feedback})
        ok = ss.homework_server.record_answer_attempt(submission_id=submission["id"], question_id=qid, attempt_number=attempt_number, student_answer=student_answer, grade=grade, feedback=feedback)
        if ok:
            ss.attempts_used[qid] = attempt_number

    if graded_results:
        st.success("✅ Answers saved and graded successfully!")
        for r in graded_results:
            st.write(f"**Q{r['question_number']} (Attempt {r['attempt']})** - Grade: {r['grade']}/2")
            st.info(f"Feedback: {r['feedback']}")
    else:
        st.info("No new answers to grade.")

    if finalize:
        # Check if all questions have been attempted at least once
        answers_map = ss.homework_server.get_submission_answers(submission["id"]) or {}
        total_questions = len(questions)
        questions_attempted = sum(1 for q in questions if answers_map.get(q["id"]))
        
        if questions_attempted < total_questions:
            st.error(f"❌ Please attempt all {total_questions} questions before submitting final.")
            return
        
        # Compute overall score from latest attempts of all questions
        num_questions = max(1, len(questions))
        latest_sum = 0
        for q in questions:
            qid = q["id"]
            attempts = answers_map.get(qid, [])
            latest_sum += attempts[-1]["grade"] if attempts else 0
        max_per_q = 2
        avg = latest_sum / (num_questions * max_per_q)
        percent = round(avg * 100, 1)
        
        # Generate summary
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
        
        # Mark submission as completed
        ss.homework_server.mark_submission_completed(submission_id=submission["id"], overall_score=percent, summary=summary)
        st.success(f"🎉 Assignment completed! Final score: {percent}%")
        st.info("You can now view your results or return to assignments.")
        
        # Refresh the submission to get updated status
        ss.submission = ss.homework_server.get_completed_submission(ss.current_user['id'], assignment['id'])


def take_assignment():
    assignment = ss.current_assignment
    submission = ss.submission
    if not assignment:
        st.info("Select an assignment to begin.")
        return
    
    # Check if submission is completed
    if submission and submission.get('status') == 'completed':
        display_completed_assignment(assignment, submission)
        return
    
    st.header(f"📝 {assignment['name']}")
    st.caption(f"Started at: {submission['started_at']}")

    # Load current attempts from DB for display and gating
    answers_by_q = ss.homework_server.get_submission_answers(submission['id'])

    # Load image bytes for questions (base64) when available
    image_qs = ss.homework_server.get_assignment_questions(assignment['id'], include_image_bytes=True)
    image_lookup = {item['id']: item for item in image_qs}

    # Determine current attempt state
    total_questions = len(assignment.get("questions", []))
    questions_with_attempts = sum(1 for q in assignment.get("questions", []) 
                                 if len(answers_by_q.get(q["id"], [])) > 0)
    
    # Check if this is first attempt (no questions answered yet)
    is_first_attempt = questions_with_attempts == 0
    
    # Check if first attempt is complete (all questions have at least 1 attempt)
    first_attempt_complete = questions_with_attempts == total_questions and total_questions > 0
    
    # Check if second attempt is complete (all questions have 2 attempts)
    questions_with_two_attempts = sum(1 for q in assignment.get("questions", []) 
                                     if len(answers_by_q.get(q["id"], [])) >= 2)
    second_attempt_complete = questions_with_two_attempts == total_questions and total_questions > 0

    # Show questions
    for question_index, q in enumerate(assignment.get("questions", []), 1):
        qid = q["id"]
        st.subheader(f"Question {question_index}")
        st.write(q["question"])
        if q.get("type") == "image":
            st.caption("This is an image-based question. Answer based on the image context.")
            img_info = image_lookup.get(qid)
            img_b64 = img_info.get("image_bytes") if img_info else None
            if img_b64:
                try:
                    st.image(base64.b64decode(img_b64), width=1000, caption="Question Image")
                except Exception:
                    st.warning("Unable to display image preview for this question.")
        else:
            st.caption("This is a text-based question. Answer based on the text context.")

        attempts = answers_by_q.get(qid, [])
        used = len(attempts)
        
        # Show attempt history
        if attempts:
            st.markdown(f"**Attempts completed: {used}/2**")
            for i, attempt in enumerate(attempts, 1):
                with st.expander(f"Attempt {i} - Grade: {attempt['grade']}/2"):
                    st.write(f"**Your answer:** {attempt['student_answer']}")
                    if attempt['feedback']:
                        st.info(f"**Feedback:** {attempt['feedback']}")
        
        # Determine if student can answer this question
        can_answer = used < 2
        
        if can_answer:
            # Pre-fill with last attempt if available
            last_answer = attempts[-1]["student_answer"] if attempts else ""
            answer = st.text_area(f"Your answer (Attempt {used + 1})", 
                                key=f"ans_{qid}", 
                                value=ss.answers_draft.get(qid, last_answer))
            ss.answers_draft[qid] = answer
        else:
            st.success("✅ Maximum attempts reached for this question.")
            if attempts:
                st.write(f"**Final answer:** {attempts[-1]['student_answer']}")

    # Button logic based on attempt state
    if is_first_attempt:
        # First attempt - only show Save & Grade and Back buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save & Grade First Attempt", type="primary"):
                grade_and_save(ss.answers_draft, finalize=False)
                st.rerun()
        with col2:
            if st.button("← Back to Assignments", key="student_back2"):
                ss.page = "assignments"
                st.rerun()
    
    elif first_attempt_complete and not second_attempt_complete:
        # First attempt complete, ready for second attempt
        st.success("🎉 First attempt completed! You can now make your second attempt.")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Save & Grade Second Attempt", type="primary"):
                grade_and_save(ss.answers_draft, finalize=False)
                st.rerun()
        with col2:
            if st.button("✅ Submit Final Assignment"):
                grade_and_save(ss.answers_draft, finalize=True)
                st.rerun()
        with col3:
            if st.button("← Back to Assignments", key="student_back3"):
                ss.page = "assignments"
                st.rerun()
    
    elif second_attempt_complete:
        # Both attempts complete, mark as finished
        st.success("🎉 Assignment completed! Both attempts have been submitted.")
        if st.button("✅ Submit Final Assignment"):
            grade_and_save(ss.answers_draft, finalize=True)
            st.rerun()


# Check if user is logged in and is a student
if not ss.current_user:
    st.error("❌ Please login first.")
    st.info("Redirecting to login page...")
    st.switch_page("main.py")
    st.stop()

if ss.current_user['role'] != 'student':
    st.error("❌ Access denied. This page is for students only.")
    st.info("Redirecting to teacher portal...")
    st.switch_page("pages/1_Teacher_Portal.py")
    st.stop()

st.title("🧑‍🎓 Student Portal")
st.write(f"Welcome, {ss.current_user['first_name']} {ss.current_user['last_name']}!")

# User info
st.write(f"**Username:** {ss.current_user['username']}")

if ss.page == "assignments":
    view_assignments()
elif ss.page == "take":
    take_assignment()

# Logout button at bottom
st.markdown("---")
if st.button("🚪 Logout"):
    ss.current_user = None
    st.switch_page("main.py")


