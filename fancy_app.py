import streamlit as st
from openai import OpenAI

st.title("🤖 AI for developers basic bot!")

if "messages" not in st.session_state or st.sidebar.button("Clear chat history"):
    st.session_state.messages = [
        {"role": "system", "content": ""},
        {"role": "assistant", "content": "How can I help you?"},
    ]

# Set custom temperature
temperature = st.sidebar.number_input("Temperature", 0.0, 2.0, 1.0, step=0.1)

# Assign a persona to the assistant
persona_options = ["", "🦜 Pirate 🏴‍☠️ ", "🧐 Refined gentleman ", "🦹 Supervillain "]
persona = st.sidebar.selectbox(
    "Persona", persona_options, help="Which persona the assistant should adopt"
)
st.session_state.messages[0][
    "content"
] = f"You are a {persona}assistant. Make it obvious who you are in your responses. Keep your responses brief."

# Take in a file for input context
context_file = st.sidebar.file_uploader("Input context", type=("txt", "md"), accept_multiple_files=False)
if context_file:
    context = context_file.read().decode()
    context_msg = f"The user provided the following document for context. Please refer to the document in your response.\n\n----------\n\n{context}\n\n----------"

for m in st.session_state.messages[1:]:
    st.chat_message(m["role"]).write(m["content"])

if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    #  Append the context document to the conversation if available
    if context_file:
        messages = st.session_state.messages + [{"role": "system", "content": context_msg}]
    else:
        messages = st.session_state.messages

    # Get a streaming response from OpenAI
    client = OpenAI(api_key=st.secrets.openai_api_key)
    with st.chat_message("assistant"):
        response_block = st.empty()
        response = ""
        stream = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
            temperature=temperature,
            stream=True,
        )
        for part in stream:
            next = part.choices[0].delta.content or ""
            response = response + next
            response_block.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
