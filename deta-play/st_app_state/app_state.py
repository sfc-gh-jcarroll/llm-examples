import streamlit as st
from typing import Any
from st_app_state.interface import StateBackend

DEFAULT_ID = "GLOBAL"


class AppState:
    def __init__(self, id: str | None, backend: StateBackend):
        self._conn = backend

        if id is None:
            id = DEFAULT_ID

        self._id = id
        if "_app_state" not in st.session_state:
            st.session_state._app_state = {}
        if id not in st.session_state._app_state:
            val = self._conn.get(id, {})
            if not val:
                self._conn.put(id, {})
            st.session_state._app_state[id] = val

    @classmethod
    def from_deta(cls, id=DEFAULT_ID):
        from deta_connection import DetaConnection

        return cls(id, DetaConnection("deta"))

    def _dict(self):
        return st.session_state._app_state[self._id]

    def sync(self):
        # TODO: Figure out if there's a hack so this isn't needed.
        # It should be possible to copy the state when it inits and compare
        # at the end of the run to see if it changed (and sync in that case).
        # But need a way to ensure the code runs at the end of the script execution.
        self._conn.put(self._id, self._dict())

    def __getitem__(self, key: str) -> Any:
        return self._dict()[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._conn.update(self._id, {key: value})
        self._dict()[key] = value

    def __delitem__(self, key: str) -> None:
        del self._dict()[key]

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(_missing_attr_error_message(key))

    def __setattr__(self, key: str, value: Any) -> None:
        if key in ("_conn", "_id"):
            super().__setattr__(key, value)
        else:
            self[key] = value

    def __delattr__(self, key: str) -> None:
        try:
            del self[key]
        except KeyError:
            raise AttributeError(_missing_attr_error_message(key))

    def __iter__(self):
        return iter(self._dict())

    def __len__(self):
        return len(self._dict())

    def __contains__(self, key: str) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def __dict__(self):
        return dict(self._dict())

    def items(self):
        return list(self._dict().items())

    def keys(self):
        return list(self._dict().keys())

    def values(self):
        return list(self._dict().values())


def _missing_attr_error_message(attr_name: str) -> str:
    return f'AppState has no attribute "{attr_name}". Did you forget to initialize it?'
