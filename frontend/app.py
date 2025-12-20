import sys
import streamlit as st
from dotenv import load_dotenv
import os 
load_dotenv()
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
from backend.main import run_chatbot

st.set_page_config(page_title="Solar Chatbot", layout = "centered")

CHAT_BOX_STYLE ="""
    <style>
    .chat-user { color: #0b5cff; font-weight:600; }
    .chat-user {color : #0a7a3f; }
    .msg {padding: 8px 0; border-bottom : 1px dashed #eee; }
    .meta { font-size : 0.8rem; color : #666; }
    </style>
"""
st.markdown(CHAT_BOX_STYLE, unsafe_allow_html= True)

st.title("Solar Monitoring Chatbot")
st.write("Ask the Bot about solar system status, weather, or search the web.")

if "session_id" not in st.session_state:
    st.session_state.session_id = "default"

sid = st.text_input("Session ID", value = st.session_state.session_id)
st.session_state.session_id = sid.strip() or "default"

chat_container = st.container()

with st.form("chat_form", clear_on_submit=False):
    user_input = st.text_input("You:", key = "user_input", placeholder="Ask about evergy, weather, or search...")
    col1, col2 = st.columns([1,0.3])
    with col1:
        submit=st.form_submit_button("Send")
    with col2:
        clear = st.form_submit_button("Clear Chat")

if clear : 
    st.session_state.session_id = sid
    st.rerun()

if submit and user_input:
    with st.spinner("Thinking..."):
        try:
            reply = run_chatbot(user_input, session_id="user1")
        except Exception as e:
            reply = f"Error Callling Backend: {e}"
    if "display" not in st.session_state:
        st.session_state.display= []
    st.session_state.display.append(("You", user_input))
    st.session_state.display.append(("Bot", reply))

try:
    backend_history = get_session_history(st.session_state.session_id)
    rendered = []
    for m in backend_history:
        role = getattr(m, "type", None) or m.__class__.__name__
        content = getattr(m, "content", str(m))

        if role.lower().startswith("system"):
            rendered.append(("System", content))
        elif role.lower().startswith("human") or "HumanMessage" in role:
            rendered.append(("You", content))
        else:
            rendered.append(("Bot", content))
    display_list = rendered
except Exception:
    display_list = st.session_state.get("display", [])


with st.container():
    st.markdown('<div id="chat-box">', unsafe_allow_html=True)

    for role, text in display_list:
        if role == "You":
            st.markdown(
                f"""
                <div class="msg">
                    <div class="chat-user"><strong>You:</strong></div>
                    <div>{text}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif role == "Bot":
            st.markdown(
                f"""
                <div class="msg">
                    <div class="chat-bot"><strong>Bot:</strong></div>
                    <div>{text}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif role == "System":
            st.markdown(
                f'<div class="msg meta">System: {text}</div>',
                unsafe_allow_html=True
            )

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("---")
st.write("Tips: Ask `What is the weather like at 12.97,77.59` or `Search solar panel efficiency 2024`.")



