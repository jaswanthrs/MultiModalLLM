import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import ollama
import json
import re


# ------------------ DB Connection ------------------
def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="llmqa",
        user="postgres",
        password="postgres",
        port="5432"
    )

# ------------------ Fetch Questions ------------------
def fetch_questions():
    conn = get_connection()
    df = pd.read_sql_query("SELECT id, topic_name, question, answer FROM public.questions", conn)
    conn.close()
    return df

# ------------------ Get LLM Feedback ------------------
def get_feedback(question, correct_answer, user_answer):
    prompt = f"""
You are an expert tutor and evaluator. Your job is to help the user learn and improve their answer.

### Question:
{question}

### Correct Answer:
{correct_answer}

### User Answer:
{user_answer}

Instructions:
- Analyze the user's answer compared to the correct answer.
- First, briefly mention what the user did well.
- Then, explain clearly what is missing, incorrect, or could be improved.
- Offer helpful suggestions or examples to guide the user to a better answer.
- Keep the language simple and supportive.

Respond ONLY in this JSON format:
```json
{{
  "explanation": "Your detailed but friendly feedback here"
}}
"""

    try:
        response = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": prompt}],
            keep_alive=False
        )
        content = response['message']['content']
        json_text = re.search(r'\{.*\}', content, re.DOTALL)
        if json_text:
             return json.loads(json_text.group(0))
        else:
            return {"explanation": "⚠️ Failed to extract feedback JSON."}
    except Exception as e:
        return f"❌ Error fetching feedback: {e}"

# ------------------ Main UI ------------------
# --- Streamlit App Entry Point ---
def app():  # 👈 Wrap UI code here
    #st.set_page_config(page_title="Answer with Feedback", layout="wide")
    st.title("Answer Feedback")

    questions_df = fetch_questions()

    if questions_df.empty:
        st.warning("No questions found in the database.")
    else:
        topics = sorted(questions_df["topic_name"].unique())

        for topic in topics:
            with st.expander(f"📂 {topic}"):
                topic_questions = questions_df[questions_df["topic_name"] == topic]

                for _, row in topic_questions.iterrows():
                    st.markdown(f"**📝 Question {row['id']}**")
                    st.write(row["question"])

                    user_input_key = f"user_answer_{row['id']}"
                    feedback_output_key = f"feedback_{row['id']}"

                    user_answer = st.text_area("✍️ Your Answer", key=user_input_key)

                    if st.button("🧠 Get Feedback", key=f"feedback_btn_{row['id']}"):
                            if user_answer.strip():
                                explanation = get_feedback(row["question"], row["answer"], user_answer)
                                st.session_state[feedback_output_key] = explanation
                            else:
                                st.error("⚠️ Please enter your answer before requesting feedback.")

                    # Show feedback if already fetched
                    if feedback_output_key in st.session_state:
                        st.markdown("**🗣️ Feedback:**")
                        st.info(st.session_state[feedback_output_key])

                    st.markdown("---")
