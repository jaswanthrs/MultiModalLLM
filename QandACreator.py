import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from datetime import datetime
import psycopg2
import logging
import re
import json

# --- DB Connection Function ---
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="llmqa",
        user="postgres",
        password="postgres"
    )

# --- Insert Q&A to DB ---
def save_qa_to_db(topic, qa_pairs, created_by="admin"):
    try:
        conn = get_connection()
        cur = conn.cursor()
        insert_query = """
            INSERT INTO questions (topic_name, question, answer, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        for pair in qa_pairs:
            cur.execute(insert_query, (
                topic,
                pair.get("question"),
                pair.get("answer"),
                created_by,
                datetime.now()
            ))
        conn.commit()
        cur.close()
        conn.close()
        st.success("✅ Questions saved to database!")
    except Exception as e:
        st.error("❌ Failed to insert data.")
        st.exception(e)

# --- Logging ---
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# --- LangChain Prompt ---
PROMPT_TEMPLATE = """
You are an expert assistant generating question-answer pairs from the given context.
Return the output in JSON format as a list of objects. Each object must have a "question" and an "answer" field.
If the context lacks clarity, return an empty list.

Context:
{document_context}

Respond only in this JSON format:
[
  {{
    "question": "What is ...?",
    "answer": "..."
  }},
  ...
]
"""

# --- Constants ---
PDF_STORAGE_PATH = 'document_store/pdfs/'
EMBEDDING_MODEL = OllamaEmbeddings(model="deepseek-r1:1.5b")
DOCUMENT_VECTOR_DB = InMemoryVectorStore(EMBEDDING_MODEL)
LANGUAGE_MODEL = OllamaLLM(model="deepseek-r1:1.5b")

# --- Helpers ---
def save_uploaded_file(uploaded_file):
    file_path = PDF_STORAGE_PATH + uploaded_file.name
    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    return file_path

def load_pdf_documents(file_path):
    return PDFPlumberLoader(file_path).load()

def chunk_documents(raw_documents):
    return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, add_start_index=True).split_documents(raw_documents)

def index_documents(document_chunks):
    DOCUMENT_VECTOR_DB.add_documents(document_chunks)

def find_related_documents(query):
    return DOCUMENT_VECTOR_DB.similarity_search(query)

def generate_answer(user_query, context_documents):
    context_text = "\n\n".join([doc.page_content for doc in context_documents])
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | LANGUAGE_MODEL
    return chain.invoke({"user_query": user_query, "document_context": context_text})

def extract_json_from_response(response):
    match = re.search(r'\[\s*{.*?}\s*\]', response, re.DOTALL)
    if match:
        raw_json = match.group()
        raw_json = re.sub(r'"\s*\.,', '",', raw_json)
        raw_json = re.sub(r'",\s*([\]}])', r'\1', raw_json)
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            logging.debug(f"Raw JSON: {raw_json}")
    return None

# --- Streamlit App Entry Point ---
def app():  # 👈 Wrap UI code here
    st.markdown("""<style> ... your CSS ... </style>""", unsafe_allow_html=True)

    st.title("QandA from document")
    #st.markdown("### Your Intelligent Document Assistant")
    st.markdown("---")

    topicName = st.text_input("Enter Topic Name")
    uploaded_pdf = st.file_uploader("Upload Research Document (PDF)", type="pdf")

    if uploaded_pdf:
        saved_path = save_uploaded_file(uploaded_pdf)
        raw_docs = load_pdf_documents(saved_path)
        processed_chunks = chunk_documents(raw_docs)
        index_documents(processed_chunks)

        st.success("✅ Document processed successfully! Ask your questions below.")

        user_input = st.chat_input("Enter your question about the document...")

        if user_input:
            with st.chat_message("user"):
                st.write(user_input)

            if "qa_saved" not in st.session_state:
                st.session_state.qa_saved = False

            with st.spinner("Analyzing document..."):
                relevant_docs = find_related_documents(user_input)
                ai_response = generate_answer(user_input, relevant_docs)
                qa_pairs = extract_json_from_response(ai_response)

            with st.chat_message("assistant", avatar="🤖"):
                if qa_pairs:
                    st.write(qa_pairs)
                    if not st.session_state.qa_saved:
                        topic = topicName #"AutoTopic"
                        save_qa_to_db(topic, qa_pairs)
                        st.session_state.qa_saved = True
                else:
                    st.write("No Q&A generated.")
