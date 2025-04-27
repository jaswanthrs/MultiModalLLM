import streamlit as st
import ollama
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
from nltk.tokenize import TreebankWordTokenizer
import json
import re
import evaluate

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

# ✅ MAIN FUNCTION to be called from menu.py
def app():
    st.title("Answer Evaluator with Scoring Details")

    # Input fields
    question = st.text_area("Enter the Question", height=100)
    correct_answer = st.text_area("Enter the Correct Answer", height=100)
    user_answer = st.text_area("Enter the User's Answer", height=100)

    if st.button("Submit"):
        if question and correct_answer and user_answer:
            with st.spinner("Evaluating..."):
                # Get BLEU and ROUGE scores
                bleu_score = round(calculate_bleu(correct_answer, user_answer), 2)
                rouge_score = round(calculate_rouge_l(correct_answer, user_answer), 2)
                bert_score = round(calculate_bertscore(correct_answer, user_answer), 2)

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
                    else:
                        st.error("❌ Failed to extract JSON from model response.")
                        st.text(content)
                        return

                    # Extract values
                    correctness = result_json.get('correctness', 0)
                    completeness = result_json.get('completeness', 0)
                    relevance = result_json.get('relevance', 0)
                    depth = result_json.get('depth', 0)

                    # Final Score Calculation (custom weights)
                    final_score = round(
                        completeness * 0.4 +
                        relevance * 0.2 +
                        depth * 0.4 
                    )

                    # Final display
                    final_result = {
                        "correctness (1 = correct, 0 = incorrect)": correctness,
                        "final_score (completeness + relevance + depth)": final_score,
                        "bleu_score (Looks at how many exact word groups match)": bleu_score,
                        "rouge_score (Checks if the important words from the reference are found in the answer)": rouge_score,
                        "bert_score (Checks  if two sentences mean the same thing)": bert_score 
                    }

                    st.markdown("### ✅ Evaluation Result")
                    st.json(final_result)

                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.warning("Please fill in all fields.")
