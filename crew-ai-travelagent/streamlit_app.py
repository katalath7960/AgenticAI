"""
AI Travel Voice Assistant — Streamlit UI
Voice input via OpenAI Whisper, voice output via OpenAI TTS.
Powered by the CrewAI travel booking agents.
"""

import base64
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

from core.travel_booking_crew import TravelBookingCrew
from voice_utils import transcribe, speak

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Travel Voice Assistant",
    page_icon="✈️",
    layout="centered",
)

# ── Session state ─────────────────────────────────────────────────────────────

if "crew" not in st.session_state:
    with st.spinner("Initialising travel agents..."):
        st.session_state.crew = TravelBookingCrew()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "voice" not in st.session_state:
    st.session_state.voice = "alloy"

if "last_audio_key" not in st.session_state:
    st.session_state.last_audio_key = None

if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None

# ── Audio playback (runs at top of every render) ──────────────────────────────

def autoplay_audio(audio_bytes: bytes) -> None:
    b64 = base64.b64encode(audio_bytes).decode()
    components.html(
        f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        height=1,
    )

if st.session_state.pending_audio:
    autoplay_audio(st.session_state.pending_audio)
    st.session_state.pending_audio = None

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("✈️ Travel Voice Assistant")
    st.markdown("Powered by CrewAI + OpenAI")
    st.divider()

    st.subheader("Voice settings")
    st.session_state.voice = st.selectbox(
        "Assistant voice",
        options=["alloy", "echo", "fable", "nova", "onyx", "shimmer"],
        index=0,
    )

    st.divider()
    st.subheader("What can I help with?")
    st.markdown(
        """
- ✈️ Flight searches
- 🏨 Hotel searches
- 🗺️ Complete trip planning
- 📋 Booking requests
- 🌍 Destination information
        """
    )

    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────

st.title("✈️ AI Travel Voice Assistant")
st.caption("Speak or type your travel request below.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Query processor ───────────────────────────────────────────────────────────

def process_query(query: str) -> None:
    """Run the crew, store response + audio, then rerun to render everything."""
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("Agents working on your request..."):
        result = st.session_state.crew.handle_customer_inquiry(query)
        response_text = result.get("response", str(result))

    with st.spinner("Generating voice response..."):
        st.session_state.pending_audio = speak(response_text, voice=st.session_state.voice)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()  # next render plays audio from pending_audio, then shows updated history

# ── Voice input ───────────────────────────────────────────────────────────────

st.divider()
audio_value = st.audio_input("🎙️ Click to record your travel request")

if audio_value is not None:
    audio_hash = hash(audio_value.getvalue())
    if audio_hash != st.session_state.last_audio_key:
        st.session_state.last_audio_key = audio_hash
        with st.spinner("Transcribing..."):
            transcript = transcribe(("audio.wav", audio_value, "audio/wav"))
        if transcript.strip():
            process_query(transcript)

# ── Text input fallback ───────────────────────────────────────────────────────

if prompt := st.chat_input("Or type your travel request here..."):
    process_query(prompt)
