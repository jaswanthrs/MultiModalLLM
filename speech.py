import streamlit as st
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import tempfile
import time

# Load model once
@st.cache_resource
def load_whisper_model():
    return whisper.load_model("small")

st.title("🎙️ Speak and Stop Recording Anytime")

sample_rate = 16000
channels = 1

# Session state to manage recording
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'audio_buffer' not in st.session_state:
    st.session_state.audio_buffer = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""

# Start recording button
if not st.session_state.is_recording:
    if st.button("🟢 Start Recording"):
        st.session_state.audio_buffer = sd.rec(
            int(60 * sample_rate),  # record max up to 60s to simulate live
            samplerate=sample_rate,
            channels=channels,
            dtype='int16'
        )
        sd.sleep(100)  # sleep a bit to get buffer started
        st.session_state.start_time = time.time()
        st.session_state.is_recording = True
        st.info("Recording... Click 'Stop' when you're done.")

# Stop recording button
if st.session_state.is_recording:
    if st.button("🔴 Stop Recording"):
        sd.stop()
        duration_recorded = int((time.time() - st.session_state.start_time) * sample_rate)
        trimmed_audio = st.session_state.audio_buffer[:duration_recorded]

        # Save to WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            write(tmp_file.name, sample_rate, trimmed_audio)
            st.session_state.audio_path = tmp_file.name

        st.session_state.is_recording = False
        st.success("Recording stopped! You can now transcribe.")

# Transcribe
if st.session_state.audio_path and st.button("📝 Transcribe"):
    st.info("Transcribing...")
    model = load_whisper_model()
    result = model.transcribe(st.session_state.audio_path)
    st.session_state.transcription = result["text"]
    st.success("Done!")

# Display result
if st.session_state.transcription:
    st.text_area("🧾 Transcribed Text", st.session_state.transcription, height=200)
