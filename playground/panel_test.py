import streamlit as st
import time

if st.button("Run the search!"):
    with st.chat_message("assistant"):
        sp = st.status_panel(behavior="stay_open")
        stage = sp.stage("🤔 **Search:** Womens US Open winner 2018")
        stage.set_expandable_state(st.proto.Block_pb2.Block.Expandable.COLLAPSED)
        with stage:
            with st.spinner("Running"):
                time.sleep(2)
                stage.set_label("✅ Search Complete!")
                stage.set_expandable_state(st.proto.Block_pb2.Block.Expandable.AUTO_COLLAPSED)
                st.write("Naomi Osaka won round 3 of the open with .... blah blah blah")
        st.write("Naomi Osaka won the 2018 Womens US Open")
