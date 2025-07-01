# Drafting Agent

## Purpose
The Drafting Agent interactively drafts legal documents (e.g., NDA, Contract, Lease Agreement) through a conversational workflow, ensuring all required information is collected and generating a well-structured legal document.

## Core Functionality
- Interprets user requests to draft legal documents.
- Identifies missing or vague information and asks follow-up questions.
- Maintains in-session memory of user responses.
- Generates well-structured legal documents in plain English.
- Supports multiple document types with customizable templates and prompts.
- Uses LLMs (Groq, Gemini) with fallback for robust generation.

## LangGraph Workflow
- **Nodes:**
  - `identify_document`: Determines the type of document to draft based on user input.
  - `ask_question`: Asks the next required or optional question to collect information.
  - `process_answer`: Processes the user's answer and updates collected information.
  - `generate_document`: Generates the final legal document using collected information and LLMs.
  - `handle_error`: Handles errors in the workflow.
- **Edges:**
  - Conditional transitions between nodes based on workflow state (e.g., missing info, completion, errors).
  - Workflow ends after document generation or error handling.

## LLMs Used
- **Primary:** Groq (Qwen-QWQ-32B)
- **Fallback:** Gemini (Gemini-2.5-Flash)

## Tools and Memory Management
- **SessionMemoryManager:** Manages session-based memory, storing conversation history and collected information for each drafting session.
- **Prompt Templates:** Customizable prompts and templates for each supported document type (NDA, Contract, Lease Agreement).

## Supported Document Types
- Non-Disclosure Agreement (NDA)
- Contract (Service Agreement, Employment Contract, Sales Agreement)
- Lease Agreement (Residential, Rental)

## Document Generation Flow
1. **Document Identification:**
   - The agent determines the type of document to draft from the user's initial input.
2. **Information Collection:**
   - The agent asks a series of required and optional questions, collecting all necessary details.
3. **Memory Management:**
   - All responses and conversation history are stored in session memory for reference.
4. **Document Generation:**
   - Once all required information is collected, the agent generates a complete legal document using LLMs and the appropriate template.

## File Structure
- `graph.py`: Main LangGraph workflow and agent logic.
- `memory.py`: Session-based memory management.
- `prompt_templates.py`: Templates and question sets for supported legal documents.
- `test.py`, `__init__.py`: Utilities and package marker. 