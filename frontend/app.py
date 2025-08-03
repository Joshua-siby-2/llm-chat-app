import streamlit as st
import requests
import json
import time
from datetime import datetime
from markdown import markdown

# App config
st.set_page_config(page_title="Local LLM Chat", layout="wide")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stop_streaming" not in st.session_state:
    st.session_state.stop_streaming = False
if "current_model" not in st.session_state:
    st.session_state.current_model = "mistral"
if "typing_active" not in st.session_state:
    st.session_state.typing_active = False
if "last_update" not in st.session_state:
    st.session_state.last_update = time.time()

# Sidebar
with st.sidebar:
    st.title("Settings")
    st.session_state.current_model = st.selectbox(
        "Model",
        ["mistral", "llama2", "gemma"],
        index=0
    )

    if st.button("New Chat"):
        try:
            requests.post("http://localhost:8000/new_chat")
        except:
            pass
        st.session_state.messages = []
        st.rerun()

    if st.download_button(
            "Save Chat",
            data=json.dumps(st.session_state.messages),
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    ):
        st.success("Chat saved!")

# Main chat
st.title("Local LLM Chat")

# Display history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(markdown(msg["content"]), unsafe_allow_html=True)
        if msg.get("model"):
            st.caption(f"Model: {msg['model']}")


def show_typing_indicator(placeholder):
    dots = ""
    while st.session_state.typing_active:
        current_time = time.time()
        if current_time - st.session_state.last_update > 0.5:
            dots = dots + "." if len(dots) < 3 else ""
            placeholder.markdown(f"Thinking{dots}")
            st.session_state.last_update = current_time
        time.sleep(0.1)


# Chat input
if prompt := st.chat_input("Type your message"):
    # User message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "model": st.session_state.current_model
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Start typing indicator
        st.session_state.typing_active = True
        st.session_state.last_update = time.time()

        try:
            # Show initial typing indicator
            message_placeholder.markdown("Thinking...")

            # API call
            response = requests.post(
                "http://localhost:8000/chat",
                json={
                    "message": prompt,
                    "model": st.session_state.current_model
                },
                stream=True,
                headers={"Accept": "text/event-stream"},
                timeout=30
            )

            # Process streaming response
            for line in response.iter_lines():
                if st.session_state.stop_streaming:
                    response.close()
                    break

                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data:'):
                        try:
                            data = json.loads(decoded[5:])
                            if data.get("content"):
                                full_response += data["content"]
                                st.session_state.typing_active = False
                                message_placeholder.markdown(
                                    markdown(full_response + "▌"),
                                    unsafe_allow_html=True
                                )
                        except json.JSONDecodeError:
                            continue

            # Final message
            st.session_state.typing_active = False
            message_placeholder.markdown(
                markdown(full_response),
                unsafe_allow_html=True
            )

            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "model": st.session_state.current_model
            })

        except Exception as e:
            st.session_state.typing_active = False
            message_placeholder.error(f"Error: {str(e)}")

        # Stop button
        if st.button("Stop Generating", key="stop_btn"):
            st.session_state.stop_streaming = True
            st.session_state.typing_active = False
            st.rerun()

        # Reset stop flag
        st.session_state.stop_streaming = False