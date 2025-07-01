import sys
from .graph import LegalDocumentAgent, AgentState

def main():
    print("=== Conversational Legal Document Drafting Agent ===")
    session_id = input("Enter session ID: ").strip()
    user_input = input("Describe the document you want to draft (e.g., 'Draft an NDA between Alice and Bob'): ").strip()

    agent = LegalDocumentAgent()
    state = AgentState(session_id=session_id, user_input=user_input)

    # Run identification
    state_dict = state.dict()
    state_dict = agent.identify_document_type(state_dict)

    # Main Q&A loop
    while not state_dict.get("is_complete", False):
        state_dict = agent.ask_question(state_dict)
        question = state_dict.get("current_question", "")
        if not question:
            print("Error: No question generated. Exiting.")
            sys.exit(1)
        print(f"\nAI: {question}")
        answer = input("You: ").strip()
        state_dict["user_input"] = answer
        state_dict = agent.process_answer(state_dict)

    # Generate document
    state_dict = agent.generate_document(state_dict)
    print("\n=== Generated Legal Document ===\n")
    print(state_dict.get("final_document", "[No document generated]") )

if __name__ == "__main__":
    main() 