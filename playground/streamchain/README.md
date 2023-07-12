# streamchain

Streamchain lets you quickly wrap Langchain chains and other LLM response functions in a Streamlit UI, while also
drawing other elements and UI pieces in native Streamlit.

## How to run your apps

Run your apps like any Streamlit app, with `streamlit run my_app.py`

## Supported decorators

Streamchain mostly works by wrapping functions with various decorators that turn them into app UI.

Note you can also call other Streamlit commands outside the decorated function and reference any Streamlit
generated variables inside the function (although state etc follows the normal Streamlit paradigm)

### `@sc.from_func`

Write any `str -> str` response function such as calling openai for a chat completion, then decorate it with `@sc.from_func`
to get a fast UI.

```python
@sc.from_func
def get_response(prompt):
    r = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user", "content": prompt}],
    )
    return r.choices[0].message.content
```

### `@sc.from_langchain`

Decorate a function that creates a Langchain Chain with `@sc.from_langchain`

**Note:** If you wrap a LangChain Agent, you'll also see tool use steps rendered with the new
Streamlit CallbackHandler for "Agent Thoughts"!

```python
# llm = ...
# tools = ...

@sc.from_langchain
def load():
    return initialize_agent(
        tools, llm, agent="chat-zero-shot-react-description"
    )
```

## Next steps

- [ ] Add a `@sc.chat_history` that wraps session state for easy tracking, and an example using a full chat
- [ ] Add examples that use other Streamlit commands like st.header and st.sidebar in the app
- [ ] Add support for `@sc.render_func` or similar that takes LLM output and custom writes to assistant container (e.g. query + display data)
- [ ] How to store additional attributes in the chat history for rendering? Ideally support grabbing content from Tools in LangChain
