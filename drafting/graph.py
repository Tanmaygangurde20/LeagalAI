"""
Conversational Legal Document Drafting Agent using LangGraph
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .memory import SessionMemoryManager
from .prompt_templates import (
    DOCUMENT_IDENTIFICATION_PROMPT,
    QUESTION_GENERATION_PROMPT,
    DOCUMENT_GENERATION_PROMPT,
    get_questions_for_document,
    get_template_for_document,
    get_missing_required_fields,
    format_collected_info_for_display
)

load_dotenv()

class AgentState(BaseModel):
    session_id: str = Field(description="Session identifier")
    user_input: str = Field(default="", description="Current user input")
    document_type: str = Field(default="", description="Type of document to draft")
    collected_info: Dict[str, Any] = Field(default_factory=dict, description="Collected information")
    current_question: str = Field(default="", description="Current question being asked")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Conversation history")
    is_complete: bool = Field(default=False, description="Whether all information is collected")
    final_document: str = Field(default="", description="Generated final document")
    error_message: str = Field(default="", description="Error message if any")

class LegalDocumentAgent:
    def __init__(self):
        self.setup_llms()
        self.memory_manager = SessionMemoryManager()
        self.graph = self.create_graph()

    def setup_llms(self):
        try:
            self.primary_llm = ChatGroq(
                groq_api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-70b-8192",
                temperature=0.1,
                max_tokens=4000
            )
        except Exception:
            self.primary_llm = None
        try:
            self.fallback_llm = ChatGoogleGenerativeAI(
                google_api_key=os.getenv("GEMINI_API_KEY"),
                model="gemini-2.5-flash",
                temperature=0.1,
                max_output_tokens=4000
            )
        except Exception:
            self.fallback_llm = None
        if not self.primary_llm and not self.fallback_llm:
            raise ValueError("Both Groq and Gemini LLMs failed to initialize. Check your API keys.")

    def get_llm_response(self, prompt: str, input_data: Dict[str, Any]) -> str:
        formatted_prompt = ChatPromptTemplate.from_template(prompt)
        parser = StrOutputParser()
        if self.primary_llm:
            try:
                chain = formatted_prompt | self.primary_llm | parser
                response = chain.invoke(input_data)
                return response.strip()
            except Exception:
                pass
        if self.fallback_llm:
            try:
                chain = formatted_prompt | self.fallback_llm | parser
                response = chain.invoke(input_data)
                return response.strip()
            except Exception as e:
                return f"Error: Both LLMs failed. Last error: {e}"
        return "Error: No available LLM models"

    def create_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("identify_document", self.identify_document_type)
        workflow.add_node("ask_question", self.ask_question)
        workflow.add_node("process_answer", self.process_answer)
        workflow.add_node("generate_document", self.generate_document)
        workflow.add_node("handle_error", self.handle_error)
        workflow.set_entry_point("identify_document")
        workflow.add_conditional_edges(
            "identify_document",
            self.should_continue_after_identification,
            {
                "ask_question": "ask_question",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "ask_question",
            self.should_continue_after_asking,
            {
                "process_answer": "process_answer",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "process_answer",
            self.should_continue_after_processing,
            {
                "ask_question": "ask_question",
                "generate_document": "generate_document",
                "error": "handle_error"
            }
        )
        workflow.add_edge("generate_document", END)
        workflow.add_edge("handle_error", END)
        return workflow.compile()

    def identify_document_type(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("user_input", "").lower().strip()
        if state.get("document_type"):
            return state
        # Canonical mapping for document types and aliases
        type_map = {
            "nda": "nda",
            "non-disclosure agreement": "nda",
            "contract": "contract",
            "service agreement": "contract",
            "employment contract": "contract",
            "employment agreement": "contract",
            "lease": "lease",
            "lease agreement": "lease",
            "rental agreement": "lease",
            "residential lease agreement": "lease"
        }
        canonical_type = None
        for k, v in type_map.items():
            if k in user_input:
                canonical_type = v
                break
        if not canonical_type:
            # Try to match by partial words (e.g., 'lease', 'nda', 'contract')
            for k, v in type_map.items():
                if any(word in user_input for word in k.split()):
                    canonical_type = v
                    break
        if not canonical_type:
            state["current_question"] = (
                "Could you please specify the type of document you want to create? "
                "(NDA, Contract, or Lease Agreement)"
            )
            return state
        state["document_type"] = canonical_type
        return state

    def ask_question(self, state: Dict[str, Any]) -> Dict[str, Any]:
        document_type = state.get("document_type", "")
        collected_info = state.get("collected_info", {})
        questions = get_questions_for_document(document_type)
        # Ask all questions (required and optional) in order
        missing_fields = [f for f in questions if f not in collected_info]
        if not missing_fields:
            state["is_complete"] = True
            return state
        next_field = missing_fields[0]
        question_config = questions[next_field]
        base_question = question_config["question"]
        if question_config.get("examples"):
            examples_text = f"\nFor example: {', '.join(question_config['examples'][:3])}"
            state["current_question"] = base_question + examples_text
        else:
            state["current_question"] = base_question
        return state

    def process_answer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        document_type = state.get("document_type", "")
        collected_info = state.get("collected_info", {})
        current_question = state.get("current_question", "")
        user_input = state.get("user_input", "")
        questions = get_questions_for_document(document_type)
        for field, config in questions.items():
            if config["question"] in current_question:
                collected_info[field] = user_input
                break
        state["collected_info"] = collected_info
        state["conversation_history"].append({"question": current_question, "answer": user_input})
        # Only complete when all questions (required and optional) are answered
        missing_fields = [f for f in questions if f not in collected_info]
        if not missing_fields:
            state["is_complete"] = True
        return state

    def generate_document(self, state: Dict[str, Any]) -> Dict[str, Any]:
        document_type = state.get("document_type", "")
        collected_info = state.get("collected_info", {})
        template = get_template_for_document(document_type)
        today = datetime.now().strftime("%B %d, %Y")
        collected_info["date"] = today

        # NDA-specific formatting for fallback
        if document_type == "nda":
            disclosing_addr = collected_info.get("disclosing_party_address", "")
            receiving_addr = collected_info.get("receiving_party_address", "")
            collected_info["disclosing_party_address_formatted"] = f" (Address: {disclosing_addr})" if disclosing_addr else ""
            collected_info["receiving_party_address_formatted"] = f" (Address: {receiving_addr})" if receiving_addr else ""
            exclusions = collected_info.get("specific_exclusions", "")
            if exclusions:
                collected_info["specific_exclusions_formatted"] = f"Additional exclusions: {exclusions}\n"
            else:
                collected_info["specific_exclusions_formatted"] = ""

        # Try LLM-based document generation first
        llm_input = {
            "document_type": document_type,
            "collected_info": format_collected_info_for_display(collected_info),
            "date": today
        }
        llm_result = self.get_llm_response(DOCUMENT_GENERATION_PROMPT, llm_input)
        if llm_result and not llm_result.lower().startswith("error"):
            state["final_document"] = llm_result + "\n\n[Generated by LLM (Groq or Gemini)]"
            state["is_complete"] = True
            return state

        # Fallback: use template formatting
        try:
            document = template.format(**collected_info)
        except Exception as e:
            state["error_message"] = f"Error generating document: {e}"
            return state
        state["final_document"] = document + "\n\n[Generated by predefined template]"
        state["is_complete"] = True
        return state

    def handle_error(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state["error_message"] = state.get("error_message", "Unknown error.")
        return state

    def should_continue_after_identification(self, state: Dict[str, Any]) -> str:
        if state.get("document_type"):
            return "ask_question"
        return "error"

    def should_continue_after_asking(self, state: Dict[str, Any]) -> str:
        return "process_answer"

    def should_continue_after_processing(self, state: Dict[str, Any]) -> str:
        if state.get("is_complete"):
            return "generate_document"
        return "ask_question" 