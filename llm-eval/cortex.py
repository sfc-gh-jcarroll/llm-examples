import json
from typing import Any, Iterator, Union, cast
from urllib.parse import urljoin

from snowflake.snowpark import Session

import requests


class Event:
    def __init__(
        self, id: Any = None, event: str = "message", data: str = "", retry: Any = None
    ) -> None:
        self.event = event
        self.data = data

    def __str__(self) -> str:
        s = f"{self.event} event"
        if self.data:
            s += ", {} byte{}".format(len(self.data), "s" if len(self.data) else "")
        else:
            s += ", no data"
        return s


class SSEClient:
    def __init__(self, response: requests.Response) -> None:
        self.response = response

    def _read(self) -> Iterator[str]:
        lines = b""
        for chunk in self.response:
            for line in chunk.splitlines(True):
                lines += line
                if lines.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield cast(str, lines)
                    lines = b""
        if lines:
            yield cast(str, lines)

    def events(self) -> Iterator[Event]:
        for raw_event in self._read():
            event = Event()
            # splitlines() only uses \r and \n
            for line in raw_event.splitlines():
                line = cast(bytes, line).decode("utf-8")

                # Lines starting with a separator are comments
                if not line.strip() or line.startswith(":"):
                    continue

                data = line.split(":", 1)
                field = data[0]

                # Ignore unknown fields.
                if field not in event.__dict__:
                    continue

                if len(data) > 1:
                    # "If value starts with a single U+0020 SPACE character,
                    # remove it from value. .strip() would remove all white spaces"
                    if data[1].startswith(" "):
                        value = data[1][1:]
                    else:
                        value = data[1]
                else:
                    value = ""

                # The data field may come over multiple lines and their values
                # are concatenated with each other.
                if field == "data":
                    event.__dict__[field] += value + "\n"
                else:
                    event.__dict__[field] = value

            if not event.data:
                continue

            # If the data field ends with a newline, remove it.
            if event.data.endswith("\n"):
                event.data = event.data[0:-1]

            # Empty event names default to 'message'
            event.event = event.event or "message"

            if event.event != "message":  # ignore anything but “message” or default event
                continue

            yield event

    def close(self) -> None:
        self.response.close()


class EmptyRestToken(Exception):
    """This exception is raised when session object does not have session.connection.rest.token attribute."""

    pass


def call_rest_function(
    function: str,
    model: str,
    messages,
    session: Session,
    stream: bool = False,
    model_kwargs={},
) -> Union[str, Iterator[str]]:
    if session.connection.rest.token is None or session.connection.rest.token == "":  # type: ignore[attr-defined]
        raise EmptyRestToken(
            "Snowflake token in session object is either None or is an empty string. Authorisation impossible. Exiting."
        )

    host: str = session.connection.host
    if not host.startswith("http"):
        host = "https://" + host
    url = urljoin(host, f"api/v2/cortex/inference/{function}")  # type: ignore[attr-defined]
    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Snowflake Token="{session.connection.rest.token}"',  # type: ignore[attr-defined]
        "Accept": "application/json, text/event-stream",
    }

    data = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }
    data.update(model_kwargs)

    response = requests.post(
        url=url,
        json=data,
        headers=headers,
        stream=stream,
    )

    if not stream:
        return cast(str, response.json()["choices"][0]["message"]["content"])
    else:
        return _return_gen(response)


def _return_gen(response: requests.Response) -> Iterator[str]:
    client = SSEClient(response)
    for event in client.events():
        response = json.loads(event.data)
        delta = response["choices"][0]["delta"]
        yield str(delta.get("content", ""))
