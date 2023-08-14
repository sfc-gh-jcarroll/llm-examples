import streamlit as st
import openai
import trubrics
from streamlit_feedback import streamlit_feedback

st.title("🔎 Chat with user feedback")

"""A simple app using [streamlit-feedback](https://github.com/trubrics/streamlit-feedback).
"""

if "authorized" not in st.session_state:
    "Enter the password to continue"
    app_password = st.text_input("App password", type="password")
    if app_password != st.secrets.app_password:
        if app_password:
            st.warning("Sorry, this password is incorrect")
        st.stop()
    st.session_state.authorized = True
    st.experimental_rerun()

openai.api_key = st.secrets.openai_api_key
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi, how can I help you?"}]

with st.sidebar:
    feedback_type = st.selectbox("Type of feedback", ["thumbs", "faces"])
    include_text = st.checkbox("Enable text feedback?")

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="Tell me a joke about sharks"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    r = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    response = r.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)

# At least one generated response, basically
if len(st.session_state.get("messages", [])) > 2:
    config = trubrics.init(
        email=st.secrets.TRUBRICS_EMAIL,
        password=st.secrets.TRUBRICS_PASSWORD,
    )
    label = None
    if include_text:
        label = "[Optional] Please provide an explanation"
    feedback = streamlit_feedback(
        feedback_type=feedback_type,
        optional_text_label=label,
        key=f"feedback_{len(st.session_state.messages)}",
    )
    if feedback:
        collection = trubrics.collect(
            component_name="default",
            model="gpt",
            response=feedback,
            metadata={"chat": st.session_state.messages},
        )
        trubrics.save(config, collection)
        st.toast("Feedback recorded!", icon="📝")
