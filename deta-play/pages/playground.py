import streamlit as st
import hashlib
from datetime import datetime
from st_app_state import AppState

from streamlit_ace import st_ace

DEFAULT_HASH_LENGTH = 6
BASE_URL = "http://localhost:8501/playground"


def get_hash(data: str, length: int = DEFAULT_HASH_LENGTH) -> str:
    """
    Given a string representation of data, return a length-characters-long string hash
    """
    return hashlib.md5(data.encode()).hexdigest()[:length]


st.set_page_config("Playground", layout="wide", page_icon="🛝")

st.title("🛝 Playground")

state = AppState.from_deta()

if "snippets" not in state:
    state.snippets = {}

params = st.experimental_get_query_params()


def execute(code: str):
    try:
        exec(code, globals(), globals())
    except Exception as e:
        st.exception(e)


with st.echo("below"):
    with st.expander("Get all snippets"):
        import pandas as pd

        df = pd.DataFrame(state.snippets.values())
        df["url"] = BASE_URL + "?q=" + df.get("hash", "")
        st.dataframe(df, hide_index=True, column_config={"url": st.column_config.LinkColumn()})

    if st.button("Delete snippets"):
        state.snippets = {}
        state.sync()
    code = ""
    if "q" in params:
        q = params["q"][0]

        if q in state["snippets"]:
            snippet = state["snippets"][q]
            code = snippet["code"]
            snippet["loaded_times"] += 1
            snippet["last_loaded_at"] = datetime.now().isoformat()

            state.sync()

    code = st_ace(language="python", value=code, height=300)

    hash = st.text_input("Custom hash (optional)")
    if st.button("Get sharable url"):
        if not hash:
            hash = get_hash(code)

        if hash in state["snippets"]:
            st.toast("Overwriting existing snippet", icon="🚧")

        state["snippets"][hash] = {
            "code": code,
            "created_at": datetime.now().isoformat(),
            "hash": hash,
            "loaded_times": 0,
            "last_loaded_at": "",
        }

        state.sync()

        url = "http://localhost:8501/playground?q=" + hash

        st.write(url)

    execute(code)
