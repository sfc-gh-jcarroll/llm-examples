import streamlit as st
import openai
import trubrics
from streamlit_feedback import streamlit_feedback

st.title("🔎 Chat with user feedback (Trubrics)")

if "authorized" not in st.session_state:
    "Enter the password to continue"
    app_password = st.text_input("App password", type="password")
    if app_password != st.secrets.app_password:
        if app_password:
            st.warning("Sorry, this password is incorrect")
        st.stop()
    st.session_state.authorized = True
    st.experimental_rerun()

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi, how can I help you?"}]

openai.api_key = st.secrets.openai_api_key
config = trubrics.init(
    email=st.secrets.TRUBRICS_EMAIL,
    password=st.secrets.TRUBRICS_PASSWORD,
)

with st.sidebar:
    feedback_type = st.selectbox("Type of feedback", ["thumbs", "faces"])
    include_text = st.checkbox("Enable text feedback?")


def get_feedback(idx):
    label = None
    if include_text:
        label = "[Optional] Please provide an explanation"
    feedback = streamlit_feedback(
        feedback_type=feedback_type,
        optional_text_label=label,
        key=f"feedback_{idx}",
    )
    if feedback:
        collection = trubrics.collect(
            component_name="default",
            model="gpt",
            response=feedback,
            metadata={"chat": st.session_state.messages[0:idx]},
        )
        trubrics.save(config, collection)
        st.toast("Feedback recorded!", icon="📝")


for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and idx > 0:
            get_feedback(idx)

if prompt := st.chat_input(placeholder="Tell me a joke about sharks"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    response = r.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)
        get_feedback(len(st.session_state.messages))
