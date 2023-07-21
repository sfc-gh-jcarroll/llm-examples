import openai
import streamlit as st
from st_app_state import AppState

if "openai_api_key" in st.secrets:
    openai_api_key = st.secrets.openai_api_key
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

USER_KEY = st.sidebar.text_input("Conversation password", type="password")
if not USER_KEY:
    st.info(
        """
        Please enter a personal Conversation Password to continue.
        Note: Any other user who can guess your password will have access to your saved conversations.
        """
    )
    st.stop()

state = AppState.from_deta(USER_KEY)
if len(state) == 0:
    # First time for this user, set up initial conversation
    state.last_key = " "
    state.convos = {}
    state.convos[state.last_key] = [{"role": "assistant", "content": "How can I help you?"}]

# display the existing chat messages
messages = state.convos[state.last_key]
for message in messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Prompt for user input and save
if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    openai.api_key = openai_api_key
    messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        response = ""
        resp_container = st.empty()
        for delta in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            stream=True,
        ):
            response += delta.choices[0].delta.get("content", "")
            resp_container.markdown(response)

        messages.append({"role": "assistant", "content": response})

with st.sidebar.form("new_convo", clear_on_submit=True):
    convo_name = st.text_input("Conversation Name")
    if st.form_submit_button("Save Conversation", type="secondary"):
        state.convos[convo_name] = messages
        state.last_key = convo_name
        state.convos[" "] = [{"role": "assistant", "content": "How can I help you?"}]


def update_conversation():
    state.last_key = st.session_state.convo_selection


st.sidebar.selectbox(
    "Select conversation",
    state.convos.keys(),
    index=list(state.convos.keys()).index(state.last_key),
    key="convo_selection",
    on_change=update_conversation,
)

# Make sure the StateBackend has the latest version from session_state
state.sync()
