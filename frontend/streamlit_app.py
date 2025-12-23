import streamlit as st
import requests 
#import asyncio
#import sys
import os 
from dotenv import load_dotenv

load_dotenv()

curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(curr_dir)
#if root_dir not in sys.path:
#    sys.path.append(root_dir)
#try:
#    from backend.app.main import run_chatbot
#except ImportError:
#    sys.path.append(os.path.abspath("."))
#    from backend.app.main import run_chatbot
API_URL = "https://test-bot-spgp.onrender.com/chat"

#------------------------------------
st.set_page_config(
    page_title="Solar AI",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Styling for chat messages */
    .stChatMessage { padding: 1rem; border-radius: 10px; }
    
    /* Clean up the title color */
    h1 { color: #fca500; }

    /* Optional: Small spacing at the very bottom */
    [data-testid="stBottomBlockContainer"] {
        padding-bottom: 50px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Configuration")
    st.markdown("---")

    if "session_id" not in st.session_state:
        st.session_state.session_id = "user1"

    session_id = st.text_input("Session ID", value=st.session_state.session_id, help="Unique ID for your conversation context.")
    st.session_state.session_id=session_id

    if st.button("Clear Conversation", type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = f"user-{os.urandom(4).hex()}"
        st.rerun()

    st.markdown("### Tips")
    st.info(
        "- Ask: 'List all solar plants'\n"
        "- Ask: 'Status of Ovobel Foods'\n"
        "- Ask: 'Weather in Karnataka'"
    )

title_section = st.container(border=True)
with title_section:
    st.title("Solar AI")
    st.caption("Monitoring Dashboard & Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

chat_display = st.container()

with chat_display:
    for message in st.session_state.messages: 
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Place the input OUTSIDE of any with blocks
if prompt := st.chat_input("Ask about your solar plants..."):
    with chat_display:
        with st.chat_message("user"):
            st.markdown(prompt)
    st.session_state.messages.append({"role" : "user", "content" : prompt})
    with chat_display:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            try:
                with st.spinner("Analyzing solar data..."):
                    #response = asyncio.run(run_chatbot(prompt, session_id = session_id))
                    resp = requests.post(
                        API_URL,
                        json={"message": prompt, "session_id": session_id},
                        timeout=120
                    )

                    resp.raise_for_status()
                    bot_reply = resp.json()["response"]
                    message_placeholder.markdown(bot_reply)
                    st.session_state.messages.append({"role" : "assistant", "content" : bot_reply})
            except Exception as e:
                error_msg = f" System Error: {str(e)}"
                message_placeholder.error(error_msg)
