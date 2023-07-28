import streamlit as st
from datetime import datetime
from st_app_state import AppState

state = AppState.from_deta()

with st.echo("below"):
    if "messages" not in state:
        state.messages = []

    with st.expander("Get all messages"):
        st.write(state.messages)
        if st.button("Delete messages"):
            del state.messages[:]
            state.sync()
            st.experimental_rerun()

    with st.form("message", clear_on_submit=True):
        name = st.text_input("Your name (optional)")
        question = st.text_area("What's your question?")
        hide = st.checkbox("Hide your question from the public board")

        if st.form_submit_button("Submit"):
            state.messages.append(
                {
                    "name": name,
                    "question": question,
                    "hide": hide,
                    "created_at": datetime.now().isoformat(),
                }
            )

            if hide:
                state.messages.append("This message is hidden from the public board")

            state.sync()
            st.experimental_rerun()
