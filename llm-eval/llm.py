from schema import Conversation, Message, ModelConfig
from litellm import completion
from cortex import call_rest_function
import streamlit as st

# TODO: Address current limitations of Arctic on Cortex
# 1. Need to use the `-instruct` model variant
# 2. Need to support multiple messages (or just take the last user msg)

FRIENDLY_MAPPING = {
    "Snowflake Arctic in Cortex": "snowflake-arctic",
    "LLaMa 3 8B": "meta/meta-llama-3-8b-instruct",
    "Mistral 7B": "mistralai/mistral-7b-instruct-v0.2",
}
AVAILABLE_MODELS = [k for k in FRIENDLY_MAPPING.keys()]


def generate_stream(
    conversation: Conversation,
):
    messages = conversation.messages
    model_config: ModelConfig = conversation.model_config
    model = FRIENDLY_MAPPING[model_config.model]
    USE_CORTEX = model == "snowflake-arctic"

    # Cortex requires the first message is a user
    # This is fine since this app has a placeholder first message anyway
    if USE_CORTEX and messages[0].role == "assistant":
        messages = messages[1:]

    if model_config.system_prompt:
        system_msg = Message(role="system", content=model_config.system_prompt)
        messages = [system_msg]
        messages.extend(conversation.messages)

    if USE_CORTEX:
        kwargs = {
            "temperature": model_config.temperature,
            "top_p": model_config.top_p,
            "max_output_tokens": model_config.max_new_tokens,
        }

        conn = st.connection("cortex")
        session = conn.session()

        stream = call_rest_function(
            function="complete",
            model=model,
            messages=[dict(m) for m in messages],
            session=session,
            stream=True,
            model_kwargs=kwargs,
        )

        for t in stream:
            yield t

    else:
        response = completion(
            model=f"replicate/{model}",
            messages=[dict(m) for m in messages],
            api_key=st.secrets.REPLICATE_API_TOKEN,
            stream=True,
            temperature=model_config.temperature,
            top_p=model_config.top_p,
            max_tokens=model_config.max_new_tokens,
        )
        for part in response:
            yield part.choices[0].delta.content or ""
