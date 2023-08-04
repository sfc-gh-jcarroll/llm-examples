import json
import openai
import streamlit as st
from typing import List

st.set_page_config(page_title="Structured responses")
st.title("Structured responses")
with st.expander("App description"):
    """
    This app allows GPT to request structured responses from the user which are generated as Streamlit buttons.
    The app uses OpenAI Function Calling with a special function for generating a question and buttons, which are then
    rendered in Streamlit and the response (click) is returned to the LLM. The app also uses a system message to encourage
    the LLM to use the function for responding to vague questions.

    Try asking the app:
    - What is the most popular kind of food?
    - Who won the Album of the Year award in 2019?
    - What were some popular regional fashion trends in the last decade?

    **Note:** The prompt engineering doesn't always work consistently, you might have to ask a couple of times.
    """


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
        "name": "clarify_with_options",
        "description": "Ask the user to clarify their question in an earlier prompt. Provide some guesses about what the user was asking as options.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Ask the user what you want them to clarify.",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The list of options provided to the user to answer your question. Max 3.",
                },
            },
            "required": ["options"],
        },
    }
]


def structured_response_options(question: str, options: List[str]) -> str:
    import time

    st.write(question)
    wrapper = st.empty()
    cols = wrapper.columns(len(options))
    vals = [False] * len(options)
    for idx, opt in enumerate(options):
        vals[idx] = cols[idx].button(opt)
    for idx, val in enumerate(vals):
        if val:
            time.sleep(0.5)
            wrapper.empty()
            return options[idx]
    return None


system_msg = """You are a helpful AI assistant.

The user may ask slightly vague questions. When they do, you should respond by calling the clarify_with_options() function. In case of a vague question, it's better to call the function than try to respond directly.

For example:
User: What is the population in 2019? // Assistant: clarify_with_options("Which country do you mean?", ["Japan", "United States", "France"])
User: Who won the US Open in 1997? // Assistant: clarify_with_options("Which one do you mean?", ["Men's", "Women's"])
User: Who won the Grammy last year? // Assistant: clarify_with_options("Which year was that?", ["2019", "2020", "2021"])
User: Who won the Oscar in 2018? // Assistant: clarify_with_options("Which category?", ["Best supporting actor", "Best film", "Best score"])

Now you try!
"""

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": system_msg},
        {"role": "assistant", "content": "How can I help you?"},
    ]

# Display session_state messages for reference / debugging
# st.json(st.session_state.messages, expanded=False)

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "system":
        pass
    elif msg["role"] in ("user", "function"):
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant" and msg.get("content"):
        st.chat_message(msg["role"]).write(msg["content"])

# Do we have a function ready to execute?
if fn := st.session_state.messages[-1].get("function_call", {}):
    func_name = fn["name"]
    if func_name == "clarify_with_options":
        args = json.loads(fn["arguments"])
        options = args.get("options", [])
        question = args.get("question")
        if not options:
            st.error("LLM tried to respond without giving options")
            st.stop()
        with st.chat_message("assistant"):
            buttons = st.container()
            with buttons:
                selection = structured_response_options(question, options)
        if selection:
            buttons.empty()
            st.session_state.messages.append(
                {"role": "function", "name": func_name, "content": selection}
            )
            st.chat_message("user").write(selection)
            prompt = selection
    else:
        st.error("Unexpected function name")
        st.stop()

if prompt:
    with st.chat_message("assistant"):
        response = ""
        resp_container = st.empty()
        func_name = ""
        for delta in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            functions=functions,
            function_call="auto",
            # function_call={"name": "clarify_with_options"},
            stream=True,
        ):
            if content := delta.choices[0].delta.get("content", ""):
                response += content
                resp_container.markdown(response)
            if fn := delta.choices[0].delta.get("function_call", ""):
                if "name" in fn:  # Only returned once at the beginning currently
                    func_name = fn.get("name")
                    func_args = ""
                    status = st.expander("Generating responses")
                    args_container = status.empty()
                if arg_delta := fn.get("arguments", ""):
                    func_args += arg_delta
                    args_container.code(func_args, language="json")
        if func_name:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "function_call": {"name": func_name, "arguments": func_args},
                }
            )
            st.experimental_rerun()
        elif response:
            st.session_state.messages.append({"role": "assistant", "content": response})
