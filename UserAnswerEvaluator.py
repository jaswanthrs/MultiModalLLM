import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
import ollama
import json
import re
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import tempfile
import time
from rouge_score import rouge_scorer
from nltk.tokenize import TreebankWordTokenizer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
import evaluate

# ------------------ Load Whisper Model ------------------
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("small")

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
    df = pd.read_sql_query("SELECT id, topic_name, question, answer, created_by, created_at FROM public.questions", conn)
    conn.close()
    return df

# ------------------ Save User Answer and Score ------------------
def save_user_answer(question_id, user_answer, user_id, correctness, bleu_score, rouge_score, bert_score, final_score):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO public.user_answers (
            question_id, user_answer, user_id, created_at,
            correctness, bleu_score, rouge_score, bert_score, final_score
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        question_id, user_answer, user_id, datetime.utcnow(),
        correctness, bleu_score, rouge_score, bert_score, final_score
    ))
    conn.commit()
    cur.close()
    conn.close()

tokenizer = TreebankWordTokenizer()

# Function to calculate BLEU score
def calculate_bleu(reference, candidate):
    reference_tokens = [tokenizer.tokenize(reference.lower())]
    candidate_tokens = tokenizer.tokenize(candidate.lower())
    smoothie = SmoothingFunction().method4
    return sentence_bleu(reference_tokens, candidate_tokens, smoothing_function=smoothie) * 100

# Function to calculate ROUGE-L score
def calculate_rouge_l(reference, candidate):
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    scores = scorer.score(reference, candidate)
    return scores['rougeL'].fmeasure * 100

# BERTScore
def calculate_bertscore(reference, candidate):
    bertscore = evaluate.load("bertscore")
    result = bertscore.compute(predictions=[candidate], references=[reference], lang="en")
    return result["f1"][0] * 100

# ------------------ Evaluate Answer using Ollama ------------------
def evaluate_answer(question, correct_answer, user_answer):
    # Prompt to Ollama for scoring
    prompt = f"""
                You are an expert answer evaluator. Compare the student's answer with the reference answer to the question.

                ### Question:
                {question}

                ### Reference Answer:
                {correct_answer}

                ### Student Answer:
                {user_answer}

                Evaluation Guidelines:
                1. "correctness": 1 if the student's answer includes at least 50% of the key reasons from the reference answer; otherwise 0.
                2. "completeness": Score 0–100 based on how many key points from the reference are covered. Partial matches are allowed.
                3. "relevance": Score 0–100 based on how focused the student's answer is on valid reasons for deforestation.
                4. "depth": Score 0–100 based on the richness of explanation (just listing is low depth, reasoning is high depth).

                Respond ONLY in valid JSON format like this:
                ```json
                {{
                "correctness": 1,
                "completeness": 60,
                "relevance": 70,
                "depth": 40
                }}
                """
    try:
        response = ollama.chat(
            model="deepseek-r1:1.5b",
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0  # makes response deterministic
            }
        )
        content = response['message']['content']
        json_text = re.search(r'\{.*\}', content, re.DOTALL)
        if json_text:
            result_json = json.loads(json_text.group(0))
            return result_json
        else:
            st.error("❌ Failed to extract JSON from LLM response.")
            st.text(content)
            return None
    except Exception as e:
        st.error(f"❌ Ollama Evaluation Error: {e}")
        return None

# ------------------ Main App ------------------
def app():
    st.title("🧠 Question Answer Evaluator with Voice Input")

    questions_df = fetch_questions()

    if questions_df.empty:
        st.warning("No questions found in the database.")
    else:
        topics = sorted(questions_df["topic_name"].unique())

        for topic in topics:
            with st.expander(f"📚 {topic}"):
                topic_questions = questions_df[questions_df["topic_name"] == topic]

                for _, row in topic_questions.iterrows():
                    question_id = row['id']
                    st.markdown(f"**❓ Question {question_id}**")
                    st.write(row["question"])

                    # Unique keys
                    #answer_key = f"answer_{question_id}"
                    start_key = f"start_rec_{question_id}"
                    stop_key = f"stop_rec_{question_id}"
                    transcribe_key = f"transcribe_{question_id}"
                    answer_key = f"answer_{question_id}"
                    transcribed_key = f"transcribed_{question_id}"
                    default_answer = st.session_state.get(transcribed_key, "")

                    # Initialize session state
                    if f"is_recording_{question_id}" not in st.session_state:
                        st.session_state[f"is_recording_{question_id}"] = False
                    if f"audio_path_{question_id}" not in st.session_state:
                        st.session_state[f"audio_path_{question_id}"] = None

                    # Answer Input
                    user_answer = st.text_area(
                                    "✍️ Your Answer (or use voice)",
                                    key=answer_key,
                                    value=st.session_state.get(f"transcribed_{question_id}", "")
                                )

                    # Voice Recording Buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if not st.session_state[f"is_recording_{question_id}"]:
                            if st.button("🟢 Start Recording", key=start_key):
                                st.session_state[f"audio_buffer_{question_id}"] = sd.rec(
                                    int(60 * 16000), samplerate=16000, channels=1, dtype='int16'
                                )
                                sd.sleep(100)
                                st.session_state[f"start_time_{question_id}"] = time.time()
                                st.session_state[f"is_recording_{question_id}"] = True
                                st.info("Recording... Click stop when done.")

                    with col2:
                        if st.session_state[f"is_recording_{question_id}"]:
                            if st.button("🔴 Stop Recording", key=stop_key):
                                sd.stop()
                                duration = int((time.time() - st.session_state[f"start_time_{question_id}"]) * 16000)
                                trimmed_audio = st.session_state[f"audio_buffer_{question_id}"][:duration]

                                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                                    write(tmp_file.name, 16000, trimmed_audio)
                                    st.session_state[f"audio_path_{question_id}"] = tmp_file.name

                                st.session_state[f"is_recording_{question_id}"] = False
                                st.success("Recording stopped.")

                    with col3:
                        if st.session_state.get(f"audio_path_{question_id}"):
                            if st.button("📝 Transcribe", key=transcribe_key):
                                st.info("Transcribing...")
                                model = load_whisper_model()
                                result = model.transcribe(st.session_state[f"audio_path_{question_id}"])
                                st.session_state[transcribed_key] = result["text"]
                                st.rerun()

                    # Evaluate Button
                    if st.button("🧪 Evaluate & Save", key=f"eval_{question_id}"):
                        current_answer = st.session_state.get(answer_key, "").strip()
                        if current_answer:
                            with st.spinner("Evaluating Answer..."):
                                result = evaluate_answer(row["question"], row["answer"], current_answer)

                                if result:
                                    bleu = calculate_bleu(row["answer"], current_answer)
                                    rouge = calculate_rouge_l(row["answer"], current_answer)
                                    bert = calculate_bertscore(row["answer"], current_answer)
                                    final_score = round(result["completeness"] * 0.4 + result["relevance"] * 0.4 + result["depth"] * 0.2, 2)
                                    uid = st.session_state.get("user_id")
                                    save_user_answer(row["id"], current_answer, uid,result["correctness"], bleu, rouge, bert, final_score)
                                    st.success(f"✅ Answer saved with score: {final_score}")
                                    st.markdown("### 🔍 Evaluation Details")
                                    st.json({
                                        **result,
                                        "bleu_score": bleu,
                                        "rouge_score": rouge,
                                        "bert_score": bert,
                                        "final_score": final_score
                                    })
                        else:
                            st.error("⚠️ Please provide an answer before evaluation.")

                    st.markdown("---")