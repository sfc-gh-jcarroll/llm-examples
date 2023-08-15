from typing import Any, Dict, List, Optional
from pathlib import Path
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
            print("QUERY EVENT START")
            self._results = self._container.status(
                f"**Retrieval:** {payload['query_str']}", expanded=True
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
            print("RETRIEVE EVENT END")
            for idx, node in enumerate(payload["nodes"]):
                self._results.write(f"**Node {idx}: Score: {node.score}**")
                self._results.write(node.node.text)
            ########
            # NOTE: If you add `expanded=True` here, the bug does not repro
            ########
            self._results.update(state="complete")


api_key = st.secrets.openai_api_key
if not api_key:
    st.info("Please add an OpenAI API Key to continue.")
    st.stop()

prompt = st.text_input("Ask a query about Paul Graham", value="What did he do growing up?")
submit = st.button("Run query")

if prompt and submit:
    llm = OpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=api_key,
        additional_kwargs=dict(api_key=api_key),
    )
    embedding = OpenAIEmbedding(model="text-embedding-ada-002", api_key=api_key)
    st_cb = StreamlitRetrievalWriter(container=st.container())
    callback_manager = CallbackManager([st_cb])

    service_context = ServiceContext.from_defaults(
        callback_manager=callback_manager, llm=llm, embed_model=embedding
    )

    data_filepath = (Path(__file__).parent / "data").absolute()
    documents = SimpleDirectoryReader(data_filepath).load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    query_engine = index.as_query_engine(streaming=True)
    response = query_engine.query(prompt)
    answer = st.empty()
    answer_text = ""

    for text in response.response_gen:
        answer_text += text
        answer.write(answer_text)
