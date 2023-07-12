import openai
import streamchain as sc

import streamlit as st

openai.api_key = st.secrets.openai_api_key


@sc.from_func
def get_response(prompt):
    r = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return r.choices[0].message.content
