# Document-Based QA Agent

## Purpose
The Document-Based QA Agent enables users to upload legal documents and ask context-specific questions, leveraging vector search and retrieval-augmented generation (RAG) for accurate, grounded answers.

## Core Functionality
- Accepts PDF, DOCX, or TXT uploads and converts them to text.
- Chunks and embeds document text using HuggingFace embeddings.
- Stores embeddings in a persistent Chroma vector database.
- Retrieves relevant document chunks in response to user queries.
- Generates answers using LLMs (Groq, Gemini) with fallback, grounded in retrieved context.
- Supports querying both newly uploaded and previously processed documents.

## LangGraph Workflow
- **Nodes:**
  - `process_documents`: Loads and splits uploaded documents into chunks.
  - `create_embeddings`: Embeds document chunks and stores them in ChromaDB.
  - `retrieve_context`: Retrieves relevant chunks for a given query using vector search.
  - `generate_answer`: Uses LLMs to generate an answer based on retrieved context.
  - `fallback_generate`: Uses fallback LLM if the primary LLM fails.
- **Edges:**
  - `process_documents` → `create_embeddings` → `retrieve_context` → `generate_answer`
  - Conditional edge from `generate_answer` to `fallback_generate` if needed
  - Workflow ends after answer generation or fallback

## LLMs Used
- **Primary:** Groq (Llama3-70B)
- **Fallback:** Gemini (Gemini-2.5-Pro)

## Tools and Vector Database
- **ChromaDB:** Persistent vector database for storing document embeddings.
- **HuggingFace Embeddings:** Used for chunking and embedding document text.
- **LangChain PromptTemplate:** For prompt engineering and answer generation.

## Processing Flow
1. **Document Upload and Loading:**
   - Loads PDF, DOCX, or TXT files and converts them to text.
2. **Chunking and Embedding:**
   - Splits documents into manageable chunks and generates embeddings using HuggingFace models.
3. **Vector Storage:**
   - Stores embeddings in ChromaDB for efficient retrieval.
4. **Query and Retrieval:**
   - Retrieves relevant chunks based on user queries using vector search.
5. **Answer Generation:**
   - Uses LLMs to generate answers grounded in the retrieved context, with fallback if needed.

## File Structure
- `graphRag.py`: Main RAG workflow, including document processing, embedding, retrieval, and answer generation.
- `chroma_db/`: Directory for persistent vector database storage.
- `rag_ui.py`, `__init__.py`: Utilities and package marker. 