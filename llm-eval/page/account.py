import streamlit as st

from common_ui import page_setup
from conversation_manager import ConversationManager


page_setup("My Account", visibility="user")

user = st.session_state.get("user_name")
conv_mgr: ConversationManager = st.session_state.conversation_manager

st.header(f"User: {user}")

conversations = conv_mgr.get_all_conversations(user=user)
metric_cols = st.columns(2)
metric_cols[0].metric("Total conversations x models", len(conversations))
metric_cols[1].metric("Total feedback", len([c for c in conversations if c.feedback]))

st.subheader("Conversation history")

id_title_mapping = {"": ""}
for id, title in conv_mgr.list_conversations_by_user(user):
    id_title_mapping[id] = title

selected = st.selectbox(
    label="Select a conversation:",
    options=id_title_mapping.keys(),
    format_func=lambda id: id_title_mapping[id],
)
if selected:
    cr = conv_mgr.get_by_id(selected)
    st.subheader(cr.title)
    if st.button("Load this conversation"):
        st.session_state.load_conversation = cr.id
        st.switch_page("page/chat.py")
    "#### Summary"
    cols = st.columns(len(cr.conversations))
    for idx, col in enumerate(cols):
        with col:
            c = cr.conversations[idx]
            "**Model Config**"
            st.json(dict(c.model_config), expanded=False)
            st.write("✅ **Feedback submitted**" if c.feedback else "❌ **Feedback missing**")
            st.write(c.messages_to_text())
            for m in c.messages:
                if len(m.content) < 35:
                    txt = m.content
                else:
                    txt = m.content[0:35] + "..."
                f"**{m.role}:** {txt}"

""
""

st.subheader("Conversation export")


@st.experimental_dialog("Export conversations")
def export():
    records = []
    for id in id_title_mapping.keys():
        if id == "":
            continue
        records.append(conv_mgr.get_by_id(id))

    output = "\n".join([r.to_json() for r in records])
    st.caption("Highlight and copy the output from here:")
    st.code(output, language="txt")
    ""
    st.caption("Or download as a .jsonl:")
    st.download_button(
        "Download conversations",
        output,
        file_name="conversations.jsonl",
        mime="application/jsonl+json",
    )
    st.divider()
    if st.button("All done, thanks!"):
        st.rerun()


if st.button("Export my conversations"):
    export()
