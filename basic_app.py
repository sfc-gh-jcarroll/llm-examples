import streamlit as st
from openai import OpenAI

st.title("AI for developers basic bot!")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you?"}]

for m in st.session_state.messages:
    st.chat_message(m["role"]).write(m["content"])

if prompt := st.chat_input():
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    client = OpenAI(api_key=st.secrets.openai_api_key)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            r = client.chat.completions.create(
                messages=st.session_state.messages,
                model="gpt-3.5-turbo",
            )
            msg = r.choices[0].message.content
            st.write(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})
