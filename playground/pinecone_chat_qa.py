import streamlit as st
import experimental
import openai
import pinecone
import time

st.status_panel = experimental.StatusPanel

st.title("Q&A App 🔎")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if query := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": query})
    st.chat_message("user").write(query)
    with st.chat_message("assistant"):
        sp = st.status_panel()
        # Initialize Pinecone client and set index
        stage = sp.stage("🤔 Retrieving embedding results from Pinecone")
        with stage:
            pinecone.init(
                api_key=st.secrets.PINECONE_API_KEY, environment=st.secrets.PINECONE_API_ENV
            )
            index = pinecone.Index("sotu")

            history = "\n\n".join(
                f"""{msg["role"]}: {msg["content"]}""" for msg in st.session_state.messages
            )
            st.write(f"**Querying for:** \n\n{history}")

            # Convert your query into a vector using Azure OpenAI
            try:
                query_vector = openai.Embedding.create(
                    input=history, model="text-embedding-ada-002"
                )["data"][0]["embedding"]
            except Exception as e:
                st.error(f"Error calling OpenAI Embedding API: {e}")
                st.stop()

            # Search for the most similar vectors in Pinecone
            search_response = index.query(top_k=2, vector=query_vector, include_metadata=True)

            chunks = [item["metadata"]["text"] for item in search_response["matches"]]

            # Combine texts into a single chunk to insert in the prompt
            joined_chunks = "\n".join(chunks)

            # Write the selected chunks into the UI
            for i, t in enumerate(chunks):
                t = t.replace("\n", " ")
                st.write("Chunk ", i, " - ", t)
            time.sleep(1.5)

        stage.set_label("✅ Retrieving embedding results from Pinecone")

        with st.spinner("Summarizing..."):
            try:
                # Build the prompt
                prompt = f"""
                Answer the following question based on the context below.
                If you don't know the answer, just say that you don't know. Don't try to make up an answer. Do not answer beyond this context.
                ---
                QUESTION: {query}
                ---
                CONTEXT:
                {joined_chunks}
                """

                # Run chat completion using GPT-4
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=st.session_state.messages + [{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000,
                ).choices[0]["message"]["content"]

                # Write query answer
                st.write(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"Error with OpenAI Chat Completion: {e}")
