import streamlit as st
from graph import LegalDocumentAgent, AgentState
import uuid

st.set_page_config(page_title="Legal Document Drafting Agent", layout="centered")
st.title("Conversational Legal Document Drafting Agent")

if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'state_dict' not in st.session_state:
    st.session_state.state_dict = None
if 'agent' not in st.session_state:
    st.session_state.agent = LegalDocumentAgent()
if 'input_counter' not in st.session_state:
    st.session_state.input_counter = 0

agent = st.session_state.agent

# Start new session button
def reset_session():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.state_dict = None
    st.session_state.input_counter = 0
st.button("Start New Session", on_click=reset_session)

# Initial user input for document type
if not st.session_state.messages:
    user_input = st.text_input("Describe the document you want to draft (e.g., 'Draft an NDA between Alice and Bob'):", key="init_input")
    if user_input:
        state = AgentState(session_id=st.session_state.session_id, user_input=user_input)
        state_dict = state.model_dump()
        state_dict = agent.identify_document_type(state_dict)
        st.session_state.state_dict = state_dict
        st.session_state.messages.append({"role": "user", "content": user_input})
        # Ask first question
        state_dict = agent.ask_question(state_dict)
        st.session_state.state_dict = state_dict
        question = state_dict.get("current_question", "")
        if question:
            st.session_state.messages.append({"role": "ai", "content": question})

# Chat loop
if st.session_state.messages:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**AI:** {msg['content']}")
    if not st.session_state.state_dict.get("is_complete", False):
        # Use a unique key for each input to avoid Streamlit state issues
        input_key = f"chat_input_{st.session_state.input_counter}"
        answer = st.text_input("Your answer:", key=input_key)
        if answer:
            st.session_state.messages.append({"role": "user", "content": answer})
            st.session_state.state_dict["user_input"] = answer
            st.session_state.state_dict = agent.process_answer(st.session_state.state_dict)
            # If now complete, generate and show document
            if st.session_state.state_dict.get("is_complete", False):
                st.session_state.state_dict = agent.generate_document(st.session_state.state_dict)
                document = st.session_state.state_dict.get("final_document", "[No document generated]")
                st.session_state.messages.append({"role": "ai", "content": "---\n**Generated Legal Document**\n" + document})
            else:
                st.session_state.state_dict = agent.ask_question(st.session_state.state_dict)
                question = st.session_state.state_dict.get("current_question", "")
                if question:
                    st.session_state.messages.append({"role": "ai", "content": question})
            st.session_state.input_counter += 1
            try:
                st.rerun()
            except AttributeError:
                try:
                    st.experimental_rerun()
                except AttributeError:
                    pass
    else:
        # Show the generated document if already complete
        document = st.session_state.state_dict.get("final_document", "[No document generated]")
        st.markdown("---")
        st.subheader("Generated Legal Document")
        st.code(document) 