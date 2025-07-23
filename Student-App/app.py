import streamlit as st
import json
import os
import base64
from PIL import Image
import io

st.set_page_config(page_title="RAG Homework - Student", page_icon="📝", layout="wide")
st.title("📝 Student Homework Portal")

# --- Load Homework Data ---
if not os.path.exists("./homework_data1.json"):
    st.error("No homework available yet. Please check back later.")
    st.stop()

with open("./homework_data1.json", "r") as f:
    data = json.load(f)

image_questions = data.get("image_question_list", [])
text_questions = data.get("text_question_list", [])

st.header("Image Questions")
for idx, q in enumerate(image_questions):
    st.subheader(f"Image Question {idx+1}")
    st.write(q.get("question", "No question text"))
    if q.get("image_bytes"):
        try:
            img_data = base64.b64decode(q["image_bytes"])
            st.image(Image.open(io.BytesIO(img_data)), caption="Question Image")
        except Exception as e:
            st.warning(f"Could not display image: {e}")
    st.text_area("Your Answer", key=f"img_ans_{idx}")

st.header("Text Questions")
for idx, q in enumerate(text_questions):
    st.subheader(f"Text Question {idx+1}")
    st.write(q.get("question", "No question text"))
    st.text_area("Your Answer", key=f"text_ans_{idx}")

# (Optional) Download answers as JSON
if st.button("Download My Answers"):
    answers = {
        "image_answers": [st.session_state.get(f"img_ans_{i}", "") for i in range(len(image_questions))],
        "text_answers": [st.session_state.get(f"text_ans_{i}", "") for i in range(len(text_questions))]
    }
    st.download_button(
        label="Download Answers as JSON",
        data=json.dumps(answers, indent=4),
        file_name="my_homework_answers.json",
        mime="application/json"
    )
