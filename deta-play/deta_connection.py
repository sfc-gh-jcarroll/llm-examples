from streamlit.connections import ExperimentalBaseConnection
from st_app_state.interface import StateBackend
import deta
from typing import Union


class DetaConnection(ExperimentalBaseConnection[deta.Base], StateBackend):
    """Basic st.experimental_connection implementation for Deta"""

    def _connect(self, **kwargs) -> deta.Base:
        client = deta.Deta(self._secrets.deta_key)
        db = client.Base(self._secrets.base)
        return db

    @property
    def base(self) -> deta.Base:
        return self._instance

    def put(self, key: str, data) -> None:
        self.base.put(data, key=key)

    def get(self, key: str, default=None) -> Union[dict, None]:
        if val := self.base.get(key):
            return val
        return default

    def update(self, key: str, data: dict) -> None:
        self.base.update(data, key)
