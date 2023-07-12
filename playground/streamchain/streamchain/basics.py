from langchain.callbacks import StreamlitCallbackHandler
import streamlit as st


def from_func(response_func):
    if "messages" not in st.session_state.keys():
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"], background=message["role"] == "user"):
            st.write(message["content"])

    prompt = st.chat_input()
    if prompt:
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response = response_func(prompt)
            st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})


def from_langchain(factory_func):
    chain = factory_func()

    def run_chain(prompt):
        cb = StreamlitCallbackHandler(st.container())
        return chain.run(prompt, callbacks=[cb])

    from_func(run_chain)
