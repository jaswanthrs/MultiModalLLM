import streamlit as st
import whisper
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import tempfile
import pdb;

# Load Whisper model
@st.cache_resource
def load_model():
    return whisper.load_model("small")

model = load_model()

# Streamlit UI
st.title("🎙️ Whisper Speech-to-Text")
st.write("Click the microphone button to record and transcribe.")
pdb.set_trace()

# Text box to display the result
text_output = st.empty()

# Record settings
duration = 5  # seconds
sample_rate = 16000

if st.button("🎤 Record and Transcribe"):
    st.info("Recording... Speak now!")

    # Record audio
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished

    # Save to temp WAV file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        write(tmp_file.name, sample_rate, audio)
        audio_path = tmp_file.name

    # Transcribe using Whisper
    st.info("Transcribing...")
    result = model.transcribe(audio_path)
    st.success("Done!")

    # Display result
    text_output.text_area("Transcription", result["text"], height=150)
