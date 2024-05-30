import json
import threading
from copy import deepcopy
from typing import Dict

import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx

from conversation_manager import ConversationManager
from llm import generate_stream, AVAILABLE_MODELS
from schema import (
    Conversation,
    Message,
    ModelConfig,
)


def page_setup(title, visibility="public"):
    st.title(title)

    if "conversation_manager" not in st.session_state:
        st.session_state.conversation_manager = ConversationManager()

    # Add sidebar content
    with st.sidebar:
        if user := st.session_state.get("user_name"):
            with st.popover("⚙️&nbsp; Settings", use_container_width=True):
                st.write(f"Logged in user: `{user}`")
                sidebar_container = st.container()
                if st.button("🔑&nbsp; Logout", use_container_width=True):
                    st.session_state.user_name = None
                    st.session_state.admin_mode = None
                    if visibility != "public":
                        st.switch_page("page/chat.py")
                    else:
                        st.rerun()
        else:
            sidebar_container = st.container()
            if st.button("🔑&nbsp; Login", use_container_width=True):
                login()

    return sidebar_container


@st.experimental_dialog("Login")
def login():
    conv_mgr: ConversationManager = st.session_state.conversation_manager
    options = set([""])
    options.update(conv_mgr.list_users())
    existing = st.selectbox("Existing user:", options)
    if not existing:
        new_user = st.text_input("New user:")
    admin_mode = st.checkbox("Admin mode", value=True)
    user_name = existing or new_user
    if st.button("Submit", disabled=not user_name):
        st.session_state.user_name = user_name
        st.session_state.admin_mode = admin_mode
        st.rerun()


def configure_model(*, container, model_config: ModelConfig, key: str, full_width: bool = True):
    MODEL_KEY = f"model_{key}"
    TEMPERATURE_KEY = f"temperature_{key}"
    TOP_P_KEY = f"top_p_{key}"
    MAX_NEW_TOKENS_KEY = f"max_new_tokens_{key}"
    SYSTEM_PROMPT_KEY = f"system_prompt_{key}"

    if MODEL_KEY not in st.session_state:
        st.session_state[MODEL_KEY] = model_config.model
        st.session_state[TEMPERATURE_KEY] = model_config.temperature
        st.session_state[TOP_P_KEY] = model_config.top_p
        st.session_state[MAX_NEW_TOKENS_KEY] = model_config.max_new_tokens
        st.session_state[SYSTEM_PROMPT_KEY] = model_config.system_prompt

    with container:
        with st.popover(
            f"Configure :blue[{st.session_state[MODEL_KEY]}]", use_container_width=full_width
        ):
            left1, right1 = st.columns(2)
            left2, right2 = st.columns(2)
            with left1:
                model_config.model = st.selectbox(
                    label="Select model:",
                    options=AVAILABLE_MODELS,
                    key=MODEL_KEY,
                )

            with left2:
                SYSTEM_PROMPT_HELP = """
                    Add a system prompt which is added to the beginning
                    of each conversation.
                """
                model_config.system_prompt = st.text_area(
                    label="System Prompt:",
                    height=2,
                    key=SYSTEM_PROMPT_KEY,
                    help=SYSTEM_PROMPT_HELP,
                )

                if model_config.model == "Mistral 7B":
                    MISTRAL_NOTE = """
                        **Note:** Mistral 7b only supports short responses, it may
                        be truncated earlier than expected.
                    """
                    st.caption(MISTRAL_NOTE)

            with right1:
                model_config.temperature = st.slider(
                    min_value=0.0,
                    max_value=1.0,
                    step=0.1,
                    label="Temperature:",
                    key=TEMPERATURE_KEY,
                )

            with right2:
                model_config.top_p = st.slider(
                    min_value=0.0,
                    max_value=1.0,
                    step=0.1,
                    label="Top P:",
                    key=TOP_P_KEY,
                )

                model_config.max_new_tokens = st.slider(
                    min_value=100,
                    max_value=1500,
                    step=100,
                    label="Max new tokens:",
                    key=MAX_NEW_TOKENS_KEY,
                )
    return model_config


def chat_response(
    conversation: Conversation,
    container=None,
):
    try:
        stream_iter = generate_stream(deepcopy(conversation))

        conversation.add_message(
            Message(role="assistant", content=""),
            render=False,
        )

        def generate_and_save():
            for t in stream_iter:
                conversation.messages[-1].content += str(t)
                yield str(t)

        if container:
            chat = container.chat_message("assistant")
        else:
            chat = st.chat_message("assistant")
        full_streamed_response = chat.write_stream(generate_and_save)
        conversation.messages[-1].content = str(full_streamed_response).strip()
    except Exception as e:
        conversation.has_error = True
        print(f"Error while generating chat response: {type(e).__name__}: {e}")


def generate_title(
    user_input: str,
    response_dict: Dict,
):
    SYSTEM_PROMPT = """
        You are a helpful assistant generating a brief summary title of a
        conversation based on the users input. The summary title should
        be no more than 4-5 words, with 2-3 words as a typical response.
        In general, brief is better when the title is a clear summary.

        Input will be provided in JSON format and you should specify the
        output in JSON format. Do not add any commentary or discussion.
        ONLY return the JSON.

        Here are a few examples:
        INPUT: {"input": "Hey, I'm looking for tips on planning a trip to Chicago. What should I do while I'm there?"}
        OUTPUT: {"summary": "Visiting Chicago"}

        INPUT: {"input": "I've been scripting and doing simple database work for a few years and I want to learn frontend web development. Where should I start?"}
        OUTPUT: {"summary": "Learning frontend development"}

        INPUT: {"input": "Can you share a few jokes?"}
        OUTPUT: {"summary": "Sharing jokes"}

        Ok, now your turn. Remember to only respond with the JSON.
        ------------------------------------------
    """
    conversation = Conversation()
    conversation.model_config = ModelConfig(system_prompt=SYSTEM_PROMPT)
    input_msg = json.dumps({"input": user_input})
    conversation.add_message(Message(role="user", content=input_msg), render=False)
    title_json = ""
    try:
        stream_iter = generate_stream(conversation)
        for t in stream_iter:
            title_json += str(t)
        result = json.loads(title_json)
        response_dict["output"] = result["summary"]

    except Exception as e:
        response_dict["error"] = True
        print("Error while generating title: " + str(e))
        print("Response:" + title_json)


def st_thread(target, args) -> threading.Thread:
    """Return a function as a Streamlit-safe thread"""

    thread = threading.Thread(target=target, args=args)
    add_script_run_ctx(thread, get_script_run_ctx())
    return thread
