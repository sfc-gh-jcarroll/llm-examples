from typing import Any, Dict, List, Optional
import streamlit as st
from llama_index import VectorStoreIndex, SimpleDirectoryReader
from llama_index import ServiceContext
from llama_index.callbacks import CallbackManager
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms import OpenAI

from llama_index.callbacks.base import BaseCallbackHandler
from llama_index.callbacks.schema import CBEventType

st.set_page_config(page_title="LlamaIndex Streamlit Example", page_icon="🦙")

st.title("🦙 LlamaIndex Streamlit Example")


class StreamlitRetrievalWriter(BaseCallbackHandler):
    """Callback handler for writing retrieval results to Streamlit."""

    def __init__(
        self,
        container=st.container(),
        event_starts_to_ignore: Optional[List[CBEventType]] = None,
        event_ends_to_ignore: Optional[List[CBEventType]] = None,
        verbose: bool = False,
    ) -> None:
        self._response = ""
        self._container = container

        super().__init__(
            event_starts_to_ignore=event_starts_to_ignore or [],
            event_ends_to_ignore=event_ends_to_ignore or [],
        )

    def set_container(self, container):
        self._container = container

    def start_trace(self, trace_id: Optional[str] = None) -> None:
        return

    def end_trace(
        self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        return

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> str:
        if (
            event_type in (CBEventType.QUERY)
            and event_type not in self.event_starts_to_ignore
            and payload is not None
        ):
            self._results = self._container.expander(
                f"**Retrieval:** {payload['query_str']}", expanded=False
            )
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        if (
            event_type in (CBEventType.RETRIEVE)
            and event_type not in self.event_ends_to_ignore
            and payload is not None
        ):
            for idx, node in enumerate(payload["nodes"]):
                self._results.write(f"**Node {idx}: Score: {node.score}**")
                self._results.write(node.node.text)


api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if not api_key:
    st.info("Please add an OpenAI API Key to continue.")
    st.stop()

prompt = st.text_input("Ask a query about Paul Graham")
submit = st.button("Run query")


@st.cache_resource(ttl="30m", show_spinner="Setting up query engine")
def load_engine_for_key(openai_key):
    llm = OpenAI(model="gpt-3.5-turbo", temperature=0, api_key=openai_key)
    embedding = OpenAIEmbedding(model="text-davinci-003", api_key=openai_key)
    st_cb = StreamlitRetrievalWriter()
    callback_manager = CallbackManager([st_cb])

    service_context = ServiceContext.from_defaults(
        callback_manager=callback_manager, llm=llm, embed_model=embedding
    )

    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    query_engine = index.as_query_engine(streaming=True)
    return query_engine, st_cb


if prompt and submit:
    query_engine, st_cb = load_engine_for_key(api_key)
    st_cb.set_container(st.container())
    response = query_engine.query(prompt)
    answer = st.empty()
    answer_text = ""

    for text in response.response_gen:
        answer_text += text
        answer.write(answer_text)
