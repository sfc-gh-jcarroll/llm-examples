from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

from langchain.callbacks.base import BaseCallbackHandler

import streamlit as st

st.title("Retrieval QA")


class PrintRetreivalHandler(BaseCallbackHandler):
    def __init__(self):
        self.container = st.expander("Retrieval")

    def on_retriever_start(self, query: str, **kwargs):
        self.container.write(f"**Question:** {query}")

    def on_retriever_end(self, documents, **kwargs):
        # self.container.write(documents)
        for idx, doc in enumerate(documents):
            self.container.write(f"**Document {idx} from {doc.metadata['source']}**")
            self.container.markdown(doc.page_content)


@st.cache_resource
def load_qa():
    loader = TextLoader("./state_of_the_union.txt")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_documents(texts, embeddings)
    return RetrievalQA.from_chain_type(
        llm=OpenAI(), chain_type="stuff", retriever=docsearch.as_retriever()
    )


qa = load_qa()

query = st.text_input("query", value="What did the president say about Ketanji Brown Jackson")

if st.button("Run the query"):
    result = qa.run(query, callbacks=[PrintRetreivalHandler()])
    st.write(result)
