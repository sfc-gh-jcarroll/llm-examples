import json
from copy import deepcopy
from typing import List, Literal
import uuid
from pydantic import BaseModel
import streamlit as st


class ModelConfig(BaseModel):
    model: str = "snowflake-arctic"
    temperature: float = 0.7
    top_p: float = 1.0
    max_new_tokens: int = 1024
    system_prompt: str = ""


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ConversationFeedback(BaseModel):
    category: str
    custom_category: str = ""
    quality_score: float
    comments: str = ""
    flagged: bool = False
    flagged_comments: str = ""


class Conversation:
    messages: List[Message] = []
    model_config: ModelConfig = None
    feedback: ConversationFeedback = None
    has_error: bool = None

    def __init__(self):
        self.reset_messages()
        self.model_config: ModelConfig = ModelConfig()
        self.feedback: ConversationFeedback = None

    def add_message(self, message: Message, container=None, render=True):
        self.messages.append(message)
        if render:
            self.render_message(message, container)

    def reset_messages(self):
        self.messages: List[Message] = []

    def render_all(self, container=None):
        for message in self.messages:
            self.render_message(message, container)

    def render_message(self, message: Message, container=None):
        if container is not None:
            container.chat_message(message.role).write(message.content)
        else:
            st.chat_message(message.role).write(message.content)

    def messages_to_text(self, truncate=True):
        msgs = []
        for m in self.messages[1:]:
            if len(m.content) < 35 or not truncate:
                txt = m.content
            else:
                txt = m.content[0:35] + "..."
            msgs.append(f"{m.role}: {txt}")
        return "\n\n".join(msgs)


class ConversationRecord:
    conversations: List[Conversation] = []
    user: str = ""
    title: str = ""
    id: str = ""

    def __init__(
        self,
        *,
        title: str,
        user: str,
        conversations: List[Conversation] = [],
        id: str = None,
    ):
        self.user = user
        self.title = title
        self.conversations = []
        for c in conversations:
            self.conversations.append(deepcopy(c))
        if id:
            self.id = id
        else:
            self.id = str(uuid.uuid4())

    def to_json(self):
        cr = {
            "conversations": [],
            "user": self.user,
            "title": self.title,
            "id": self.id,
        }
        for conv in self.conversations:
            c = {
                "messages": [dict(m) for m in conv.messages],
                "model_config": dict(conv.model_config),
            }
            if conv.feedback:
                c["feedback"] = dict(conv.feedback)
            cr["conversations"].append(c)
        return json.dumps(cr)

    @classmethod
    def from_json(cls, raw_json: str):
        d = json.loads(raw_json, strict=False)
        cr = ConversationRecord(
            title=d["title"],
            user=d["user"],
            id=d["id"],
        )
        for c in d["conversations"]:
            conversation = Conversation()
            conversation.model_config = ModelConfig.parse_obj(c["model_config"])
            conversation.messages = [Message.parse_obj(m) for m in c["messages"]]
            if "feedback" in c:
                conversation.feedback = ConversationFeedback.parse_obj(c["feedback"])
            cr.conversations.append(conversation)
        return cr
