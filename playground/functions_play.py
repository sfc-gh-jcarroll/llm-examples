import json
import time
import openai
import streamlit as st
from langchain.utilities import DuckDuckGoSearchAPIWrapper

st.set_page_config(page_title="Playing with OpenAI functions")
st.title("Playing with OpenAI functions")
"""
This bot is enabled with web search using OpenAI Function Calls. It uses status panel prototype for rendering function call and response.
The user can decide via checkbox in sidebar whether to run functions automatically or inspect/edit and approve function calls before running.
"""
check_functions = st.sidebar.checkbox(
    "Edit and approve function calls before running?", value=False
)


if "openai_api_key" in st.secrets:
    openai_api_key = st.secrets.openai_api_key
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Enter an OpenAI API Key to continue")
    st.stop()
openai.api_key = openai_api_key


functions = [
    {
        "name": "web_search",
        "description": "Search the web. Useful for current events or answering specific factual questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "The web search query to run",
                },
            },
            "required": ["search_query"],
        },
    }
]


def web_search(search_query):
    # Artificial sleep so the UI is clearer
    time.sleep(1.5)
    search = DuckDuckGoSearchAPIWrapper()
    return search.run(search_query)


# This is callback function used further down for user to explicitly approve function call
def save_fn_call():
    func_name = st.session_state.pending_call
    func_args = st.session_state.pending_args
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": None,
            "function_call": {"name": func_name, "arguments": func_args},
        }
    )


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Display session_state messages for reference / debugging
# st.json(st.session_state.messages, expanded=False)

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "system":
        pass
    elif msg["role"] == "user":
        st.chat_message(msg["role"]).write(msg["content"])
    elif msg["role"] == "assistant":
        if i == 0 or st.session_state.messages[i - 1]["role"] != "function":
            last_asst = st.chat_message("assistant")
            with last_asst:
                status_space = st.container()
        with last_asst:
            if content := msg.get("content", ""):
                st.write(content)
            elif fn := msg.get("function_call", {}):
                last_fn = fn["name"]
                last_status = status_space.status(f"Executing `{last_fn}`")
                last_status.code(fn["arguments"], language="json")
    elif msg["role"] == "function":
        if msg["name"] != last_fn:
            st.error("Unexpected function response")
            st.stop()
        last_status.update(state="complete")
        last_status.write(msg["content"])

# Do we have a function ready to execute?
new_function_response = False
if fn := st.session_state.messages[-1].get("function_call", {}):
    func_name = fn["name"]
    if func_name == "web_search":
        query = json.loads(fn["arguments"]).get("search_query", "")
        if not query:
            st.error("LLM tried to search without a query")
            st.stop()
        results = web_search(query)
        last_status.write(results)
        st.session_state.messages.append(
            {"role": "function", "name": func_name, "content": results}
        )
        last_status.update(state="complete")
    else:
        st.error("Unexpected function name")
        st.stop()
    new_function_response = True

if prompt:  # last was a new user message, we need a new asst chat bubble
    last_asst = st.chat_message("assistant")

if prompt or new_function_response:
    with last_asst:
        response = ""
        status_space = st.container()
        resp_container = st.empty()
        func_name = ""
        for delta in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            functions=functions,
            function_call="auto",
            stream=True,
        ):
            if content := delta.choices[0].delta.get("content", ""):
                response += content
                resp_container.markdown(response)
            if fn := delta.choices[0].delta.get("function_call", ""):
                if "name" in fn:  # Only returned once at the beginning currently
                    func_name = fn.get("name")
                    func_args = ""
                    status = status_space.status(f"Executing `{func_name}`")
                    args_container = status.empty()
                if arg_delta := fn.get("arguments", ""):
                    func_args += arg_delta
                    args_container.code(func_args, language="json")
        if func_name:
            st.session_state.pending_call = func_name
            st.session_state.pending_args = func_args
            if check_functions:
                with args_container.form("args"):
                    st.text_area(
                        "Function arguments",
                        label_visibility="collapsed",
                        key="pending_args",
                    )
                    st.form_submit_button("Execute function", on_click=save_fn_call)
            else:
                # Persist pending call and rerun for auto-function run
                save_fn_call()
                st.experimental_rerun()
        elif response:
            st.session_state.messages.append({"role": "assistant", "content": response})
