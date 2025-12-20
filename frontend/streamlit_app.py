import streamlit as st
import asyncio
import sys
import os 
from dotenv import load_dotenv

load_dotenv()

curr_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(curr_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
try:
    from backend.main import run_chatbot
except ImportError:
    sys.path.append(os.path.abspath("."))
    from backend.main import run_chatbot

#------------------------------------
st.set_page_config(
    page_title="Solar AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
        .stChatMessage { padding: 1rem; border-radius: 10px; }
        .stChatInput { position: fixed; bottom: 0; }
        h1 { color: : #fca500; }
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
        st.rerun()

    st.markdown("### Tips")
    st.info(
        "- Ask: 'List all solar plants'\n"
        "- Ask: 'Status of Ovobel Foods'\n"
        "- Ask: 'Weather in Karnataka'"
    )
st.title("Solar AI")
st.caption("Monitoring Dashboard & Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []
for message in st.session_state.messages : 
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about your solar plants..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role" : "user", "content" : prompt})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            with st.spinner("Analyaing solar data..."):
                response = asyncio.run(run_chatbot(prompt, session_id = session_id))
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role" : "assistant", "content" : response})
        except Exception as e:
            error_msg = f" System Error: {str(e)}"
            message_placeholder.error(error_msg)




    

