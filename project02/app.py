import sys
import streamlit as st
from agent.core import Agent
from cv_extract import extract_cv_text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


st.set_page_config(page_title="Job Search Agent", layout="centered")
st.title("Job Search Agent")
st.caption("Ask about jobs, search the database, or scrape LinkedIn. Type naturally.")

if "agent" not in st.session_state:
    st.session_state.agent = Agent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "cv_file_id" not in st.session_state:
    st.session_state.cv_file_id = None

uploaded = st.file_uploader(
    "Upload CV",
    type=["pdf", "docx", "txt"],
)

if uploaded is not None:
    file_id = f"{uploaded.name}:{uploaded.size}"
    if file_id != st.session_state.cv_file_id:
        try:
            cv_text = extract_cv_text(uploaded)
            st.session_state.agent.registry.state["cv_text"] = cv_text
            st.session_state.agent.memory.add_user_message(
                f"[System] User uploaded a CV ({len(cv_text)} characters). "
                "It is stored for match_all_jobs and tailor_cv. Confirm if asked."
            )
            st.session_state.agent.registry.state["cv_profile"] = None
            st.session_state.agent.registry.state["cv_overrides"] = {}
            st.session_state.cv_file_id = file_id
            st.success(f"CV loaded: {uploaded.name} ({len(cv_text)} characters)")
        except Exception as e:
            st.error(str(e))
    else:
        st.info(f"CV ready: {uploaded.name}")
elif st.session_state.agent.registry.state.get("cv_text"):
    st.info("CV loaded in this session.")
else:
    st.warning("No CV uploaded yet. Upload a PDF, DOCX, or TXT before matching.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me about jobs..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("Working...", expanded=True) as status:
            def on_progress(msg: str):
                status.write(msg)

            reply = (
                st.session_state.agent.run(prompt, on_progress=on_progress)
                or "No response"
            )
            # expanded=True keeps the step log open after complete (default collapses)
            status.update(label="Done", state="complete", expanded=True)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
