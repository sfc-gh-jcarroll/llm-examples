# LLM Evaluation Demo

This app enables conversation with several LLMs under various configurations,
along with simple human feedback and persisted conversation history.

Log in to save your conversations. Use Admin Mode to manage users, view
aggregated feedback stats, as well as view automated evaluation _(coming soon!)_.

**You can access the hosted app at
[llm-eval-demo.streamlit.app](https://llm-eval-demo.streamlit.app/about?user=Snow).**

## Goals

- Highlight many of the new features launched in Streamlit in the last ~6 months
- Show how those features can work together to deliver a functional, useful app
- Provide some templates for solving common AI application problems around evaluating LLMs.

## Running the app

1. Clone the repo, create a new python virtual environment, and do `pip install -r requirements.txt`
1. You'll need a `[connections.cortex]` section in your `.streamlit/secrets.toml` to call the models.
   - You can also configure `enablePersistence = false` in secrets to disable saving
     out changes to the `.jsonl` file.
1. Do `streamlit run app.py` to run the app locally.

## App architecture

TODO: Fill in

## Contributing

We are welcoming small improvements to this app as PRs and bigger ideas as Github issues.
Feel free to tag `@sfc-gh-jcarroll` for faster responses.

If you want to add a new dependency or model in the main repo, please open an issue first
to discuss! We likely won't be accepting many of those. However, if you want to fork
the app and add your own version, we'd love for you to host it on
[share.streamlit.io](https://share.streamlit.io) and let us know or tag Streamlit on socials
so we can highlight it as well!

### Contributing new conversation data

We are also welcoming new sample conversation data in `data/conversation_history.jsonl` to
more fully flesh out the app. Instructions can be found on the `/about` page.
