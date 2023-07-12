from langchain import OpenAI, LLMMathChain, SerpAPIWrapper
from langchain.agents import initialize_agent, Tool
from langchain.chat_models import ChatOpenAI
import os

import streamchain as sc
import streamlit as st

os.environ["OPENAI_API_KEY"] = st.secrets.openai_api_key
os.environ["SERPAPI_API_KEY"] = st.secrets.serpapi_api_key

llm = OpenAI(temperature=0, streaming=True)
chat_llm = ChatOpenAI(temperature=0, streaming=True)
search = SerpAPIWrapper()
llm_math_chain = LLMMathChain.from_llm(llm=chat_llm)

tools = [
    Tool(
        name="Search",
        func=search.run,
        description="useful for when you need to answer questions about current events. You should ask targeted questions",
    ),
    Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="useful for when you need to answer questions about math",
    ),
]


@sc.from_langchain
def load():
    return initialize_agent(tools, llm, agent="chat-zero-shot-react-description")
