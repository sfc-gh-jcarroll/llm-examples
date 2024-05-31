import streamlit as st
import pathlib

# Check for initial login via query_params
if initial_user := st.query_params.get("user"):
    st.session_state.user_name = initial_user
    st.session_state.admin_mode = True
    del st.query_params["user"]

# Set up navigation
main_pages = [
    st.Page("page/about.py", title="About", icon=":material/info:"),
    st.Page("page/chat.py", title="Chat", icon=":material/chat:", default=True),
]

if st.session_state.get("user_name"):
    main_pages.append(st.Page("page/account.py", title="My Account", icon=":material/account_circle:"))

page_headers = {
    "LLM Evaluation": main_pages,
}

if st.session_state.get("admin_mode"):
    page_headers["Admin view"] = [
        st.Page("page/analysis.py", title="Conversation Analysis", icon=":material/analytics:"),
        st.Page("page/auto_eval.py", title="Automated Evaluation", icon=":material/quiz:"),
        st.Page("page/users.py", title="User Management", icon=":material/group:"),
    ]

pg = st.navigation(page_headers)

# Page config and logo
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
LOGO = str(CURRENT_DIR / "ucbskylogo-blue.svg")
ICON_LOGO = str(CURRENT_DIR / "sky_mark.png")
FAVICON = str(CURRENT_DIR / "sky_favicon.png")

st.set_page_config(
    page_title=f"LLM Evaluation: {pg.title}",
    page_icon=FAVICON,
    layout="wide" if pg.title == "Chat" else "centered",
)

st.logo(LOGO, link="https://sky.cs.berkeley.edu/", icon_image=ICON_LOGO)

pg.run()
