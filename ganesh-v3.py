import streamlit as st
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import tempfile
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import pdb;

# ---------- CONFIG ----------
st.set_page_config(page_title="🎤 Whisper + 📘 DocuMind", layout="wide")

PDF_STORAGE_PATH = 'document_store/pdfs/'
EMBEDDING_MODEL = OllamaEmbeddings(model="deepseek-r1:1.5b")
DOCUMENT_VECTOR_DB = InMemoryVectorStore(EMBEDDING_MODEL)
LANGUAGE_MODEL = OllamaLLM(model="deepseek-r1:1.5b")

PROMPT_TEMPLATE = """
You are an expert research assistant. Use the provided context to answer the query. 
If unsure, state that you don't know. Be concise and factual (max 3 sentences).

Question: {user_query}  
Context: {document_context}  
Answer:
"""

# ---------- SESSION STATE ----------
if "transcription" not in st.session_state:
    st.session_state.transcription = ""

# ---------- FUNCTIONS ----------
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("small")

def save_uploaded_file(uploaded_file):
    file_path = PDF_STORAGE_PATH + uploaded_file.name
    with open(file_path, "wb") as file:
        file.write(uploaded_file.getbuffer())
    return file_path

def load_pdf_documents(file_path):
    loader = PDFPlumberLoader(file_path)
    return loader.load()

def chunk_documents(raw_documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    return splitter.split_documents(raw_documents)

def index_documents(document_chunks):
    DOCUMENT_VECTOR_DB.add_documents(document_chunks)

def find_related_documents(query):
    return DOCUMENT_VECTOR_DB.similarity_search(query)

def generate_answer(user_query, context_documents):
    context_text = "\n\n".join([doc.page_content for doc in context_documents])
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    response_chain = prompt | LANGUAGE_MODEL
    return response_chain.invoke({
        "user_query": user_query,
        "document_context": context_text
    })

# ---------- UI ----------
st.title("🧠 DocuMind AI + Whisper")
st.markdown("Upload a PDF, speak or type your question, then ask the AI for an answer!")

# Upload PDF
uploaded_pdf = st.file_uploader("📄 Upload Research Document (PDF)", type="pdf")
if uploaded_pdf:
    saved_path = save_uploaded_file(uploaded_pdf)
    raw_docs = load_pdf_documents(saved_path)
    processed_chunks = chunk_documents(raw_docs)
    index_documents(processed_chunks)
    st.success("✅ Document loaded and indexed!")

# Manual Text Input
manual_input = st.text_area("✍️ Type your question here", height=100)

# Transcribed Text Area (read-only but visible)
st.text("🎤 Speak your question below")
if st.button("🎙️ Record with Microphone"):
    st.info("Recording... Speak now!")
    duration = 5  # seconds
    sample_rate = 16000

    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        write(tmp_file.name, sample_rate, audio)
        audio_path = tmp_file.name

    st.info("Transcribing...")
    model = load_whisper_model()
    result = model.transcribe(audio_path)
    st.session_state.transcription = result["text"]
    st.success("Transcription complete!")

# Show the transcription
st.text_area("🗣️ Transcribed Question (from speech)", value=st.session_state.transcription, height=100, key="transcribed_input")

# Submit section
st.markdown("---")
selected_input = st.radio("📌 Choose which input to submit:", ("Typed Text", "Transcribed Text"))

if st.button("🔍 Submit to Search PDF"):
    if not uploaded_pdf:
        st.warning("❗ Please upload a PDF first.")
    else:
        query = manual_input.strip() if selected_input == "Typed Text" else st.session_state.transcription.strip()

        if query == "":
            st.warning("❗ Selected input is empty.")
        else:
            with st.spinner("Analyzing document..."):
                docs = find_related_documents(query)
                response = generate_answer(query, docs)

            st.subheader("🤖 AI Assistant's Answer")
            st.write(response)
