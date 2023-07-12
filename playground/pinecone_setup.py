import streamlit as st

import pinecone
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains.question_answering import load_qa_chain


@st.cache_resource
def load():
    loader = TextLoader("./state_of_the_union.txt")
    data = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    chunks = text_splitter.split_documents(data)

    st.write(f"You have a total of {len(chunks)} chunks")

    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    pinecone.init(api_key=st.secrets.PINECONE_API_KEY, environment=st.secrets.PINECONE_API_ENV)

    docsearch = Pinecone.from_texts([t.page_content for t in chunks], embeddings, index_name="sotu")
    return docsearch


docsearch = load()

llm = ChatOpenAI(temperature=0)

chain = load_qa_chain(llm, chain_type="stuff")

query = "What did the president say about Ketanji Brown Jackson"
docs = docsearch.similarity_search(query)

result = chain.run(input_documents=docs, question=query)

st.write(f"Answer: \n\n {result}")
