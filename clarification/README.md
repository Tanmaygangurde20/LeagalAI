# Clarification Agent

## Purpose
The Clarification Agent provides real-time legal clarifications by processing user queries, extracting relevant keywords, searching trusted legal sources, and generating concise, source-cited summaries using advanced LLMs.

## Core Functionality
- Accepts legal clarification queries (e.g., "What is the difference between a void and voidable contract in Canada?").
- Extracts legal keywords from the query using LLMs.
- Performs web search using DuckDuckGoSearchRun, focusing on legal sources (e.g., CanLII, justice.gc.ca).
- Summarizes and cites results using LLMs (Groq, Gemini) with fallback.
- Provides both quick answers and comprehensive, structured legal summaries.
- Focuses on Canadian law but can be adapted for other jurisdictions.

## LangGraph Workflow
- **Nodes:**
  - `extract_keywords`: Extracts search keywords from the legal query using LLMs.
  - `search_web`: Performs web search using extracted keywords.
  - `validate_results`: Validates search results and determines if fallback is needed.
  - `fallback_llm`: Uses fallback LLM if primary search or summarization fails.
- **Edges:**
  - `extract_keywords` → `search_web`
  - `search_web` → `validate_results`
  - `validate_results` → (`fallback_llm` or END)
  - `fallback_llm` → `search_web`

## LLMs Used
- **Primary:** Groq (Llama3-70B)
- **Fallback:** Gemini (Gemini-Pro)

## Tools Used
- **DuckDuckGoSearchRun**: For web search and legal content retrieval.
- **LangChain PromptTemplate**: For prompt engineering and keyword extraction.

## Processing Flow
1. **Keyword Extraction:**
   - The agent uses LLMs to extract up to 5 relevant legal keywords from the user's query.
2. **Web Search:**
   - Performs a targeted search using DuckDuckGo, focusing on Canadian legal sources.
3. **Result Validation:**
   - Validates the quality and relevance of search results. If results are insufficient, triggers fallback logic.
4. **Summarization:**
   - Summarizes the search results using LLMs, providing a structured, source-cited answer.
5. **Fallback:**
   - If the primary LLM or search fails, the agent uses a fallback LLM to ensure robust performance.

## File Structure
- `graphSearch.py`: Main LangGraph workflow and search logic.
- `summarize.py`: Summarization, prompt engineering, and citation extraction.
- `bing_search.py`, `fallback.py`: Stubs for future extension.
- `__init__.py`: Package marker.

## LangGraph Nodes and Edges
### Nodes
- **extract_keywords**: Extracts relevant legal keywords from the user's query using LLMs.
- **search_web**: Performs a web search using the extracted keywords, focusing on legal sources.
- **validate_results**: Checks the quality and sufficiency of search results, deciding whether to proceed or trigger fallback.
- **fallback_llm**: Uses a fallback LLM to retry keyword extraction or summarization if previous steps fail.

### Edges
- **extract_keywords → search_web**: After extracting keywords, proceeds to web search.
- **search_web → validate_results**: After searching, validates the results.
- **validate_results → fallback_llm**: If results are insufficient, triggers fallback logic.
- **validate_results → END**: If results are sufficient, ends the workflow.
- **fallback_llm → search_web**: After fallback, retries the web search. 