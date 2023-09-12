import json
import openai
import streamlit as st
from langchain.utilities import DuckDuckGoSearchAPIWrapper

st.set_page_config(page_title="st.status with OpenAI functions")
st.title("st.status with OpenAI functions")
"""
This bot is enabled with web search using OpenAI Function Calls. It uses `st.status` for rendering function call and response.
"""

if "openai_api_key" in st.secrets:
    openai_api_key = st.secrets.openai_api_key
else:
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Enter an OpenAI API Key to continue")
    st.stop()
openai.api_key = openai_api_key


def web_search(search_query):
    search = DuckDuckGoSearchAPIWrapper()
    return search.run(search_query)


# Metadata about supported web_search function to pass to OpenAI
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

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Render previous messages and function calls
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        for fn in msg.get("fn_calls", []):
            with st.status(f"""Executing `{fn["name"]}`""", state=fn["state"]):
                st.code(fn["arguments"], language="json")
                st.write(fn["results"])
        st.write(msg["content"])

# Generate response for a new prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        response_object = {"role": "assistant", "fn_calls": []}
        response = ""
        status_space = st.container()
        resp_container = st.empty()
        # Loop to support function calls and subsequent generations by OpenAI
        for i in range(5):
            func_name = ""
            # We store function calls in a slightly different format than the one expected by OpenAI - convert it here
            openai_funcs = []
            for fn in response_object["fn_calls"]:
                openai_funcs.extend(
                    [
                        {
                            "role": "assistant",
                            "content": None,
                            "function_call": {"name": fn["name"], "arguments": fn["arguments"]},
                        },
                        {"role": "function", "name": fn["name"], "content": fn["results"]},
                    ]
                )
            msg_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.messages
            ]

            # Use deltas to stream back response
            for delta in openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=msg_history + openai_funcs,
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

            # Run the web search if requested and append the result for the next loop iteration
            if func_name == "web_search":
                query = json.loads(func_args).get("search_query", "")
                if not query:
                    st.error("LLM tried to search without a query")
                    st.stop()
                results = web_search(query)
                status.write(results)
                status.update(state="complete")
                response_object["fn_calls"].append(
                    {
                        "name": func_name,
                        "arguments": func_args,
                        "results": results,
                        "state": "complete",
                    }
                )
            elif response:
                # Stop once the LLM generates an actual response
                response_object["content"] = response
                st.session_state.messages.append(response_object)
                break
            else:
                st.error("Unexpected response from LLM")
                st.stop()
        if st.session_state.messages[-1]["role"] != "assistant":
            st.error("Something went wrong: reached max iteration of function calls.")
