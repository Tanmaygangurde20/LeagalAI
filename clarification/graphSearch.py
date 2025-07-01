"""
Legal Clarification Search System using LangGraph
Handles query processing, keyword extraction, and web searching with fallback LLMs
"""

import os
from typing import Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.llms import HuggingFacePipeline
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import logging
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchState(TypedDict):
    """State management for the search workflow"""
    original_query: str
    keywords: List[str]
    search_results: List[Dict]
    current_llm: str
    error_count: int
    final_summary: str
    sources: List[str]

class LegalSearchGraph:
    """LangGraph-based legal search and clarification system"""
    
    def __init__(self, groq_api_key: str = None, gemini_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Initialize search tool
        self.search_tool = DuckDuckGoSearchRun(max_results=5)
        
        # Initialize LLMs with fallback mechanism
        self.llms = self._initialize_llms()
        
        # Create the graph
        self.graph = self._create_graph()
        
    def _initialize_llms(self) -> Dict:
        """Initialize available LLMs with fallback mechanism"""
        llms = {}
        # Try Groq first
        if self.groq_api_key:
            try:
                llms['groq'] = ChatGroq(
                    groq_api_key=self.groq_api_key,
                    model_name="llama3-70b-8192",
                    temperature=0.1
                )
                logger.info("Groq LLM initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq: {e}")
        # Try Gemini as fallback
        if self.gemini_api_key:
            try:
                llms['gemini'] = ChatGoogleGenerativeAI(
                    google_api_key=self.gemini_api_key,
                    model="gemini-1.5-flash",
                    temperature=0.1
                )
                logger.info("Gemini LLM initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
        # If no LLMs available, raise error (do not use transformers)
        if not llms:
            logger.error("No Groq or Gemini API key provided. Please set GROQ_API_KEY or GEMINI_API_KEY in your environment.")
            raise Exception("No Groq or Gemini API key provided. Please set GROQ_API_KEY or GEMINI_API_KEY in your environment.")
        return llms
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(SearchState)
        
        # Add nodes
        workflow.add_node("extract_keywords", self._extract_keywords)
        workflow.add_node("search_web", self._search_web)
        workflow.add_node("validate_results", self._validate_results)
        workflow.add_node("fallback_llm", self._fallback_llm)
        
        # Define edges
        workflow.set_entry_point("extract_keywords")
        workflow.add_edge("extract_keywords", "search_web")
        workflow.add_edge("search_web", "validate_results")
        
        # Conditional edges for error handling
        workflow.add_conditional_edges(
            "validate_results",
            self._should_retry,
            {
                "retry": "fallback_llm",
                "end": END
            }
        )
        workflow.add_edge("fallback_llm", "search_web")
        
        return workflow.compile()
    
    def _extract_keywords(self, state: SearchState) -> SearchState:
        """Extract search keywords from the legal query"""
        query = state["original_query"]
        
        keyword_prompt = PromptTemplate(
            template="""
            You are a legal research assistant. Your task is to extract the most relevant legal keywords from the user query to assist in  law research.

            - Focus on legal terms, legal concepts, and jurisdiction-specific elements (e.g., acts, provinces, legal doctrines).
            - Do not include general or irrelevant words.
            - Limit the result to a **maximum of 5 keywords**, separated by commas.
            - Return only the keywords — no extra text or explanation.
                        
            Query: {query}
            
            Return only the keywords as a comma-separated list (max 5 keywords):
            """,
            input_variables=["query"]
        )
        
        # Try available LLMs in order
        for llm_name, llm in self.llms.items():
            try:
                prompt_text = keyword_prompt.format(query=query)
                response = llm.invoke([HumanMessage(content=prompt_text)])
                
                if hasattr(response, 'content'):
                    keywords_text = response.content
                else:
                    keywords_text = str(response)
                
                keywords = [k.strip() for k in keywords_text.split(',')]
                keywords = [k for k in keywords if k]  # Remove empty strings
                
                state["keywords"] = keywords[:5]  # Limit to 5 keywords
                state["current_llm"] = llm_name
                logger.info(f"Keywords extracted using {llm_name}: {keywords}")
                break
                
            except Exception as e:
                logger.warning(f"Keyword extraction failed with {llm_name}: {e}")
                continue
        
        if not state.get("keywords"):
            # Fallback to basic keyword extraction
            state["keywords"] = self._basic_keyword_extraction(query)
            logger.info(f"Using fallback keyword extraction: {state['keywords']}")
        
        return state
    
    def _basic_keyword_extraction(self, query: str) -> List[str]:
        """Basic keyword extraction as fallback"""
        legal_terms = [
            "contract", "void", "voidable", "tort", "negligence", 
            "liability", "statute", "common law", "civil", "criminal",
            "constitutional", "administrative", "property", "family"
        ]
        
        query_lower = query.lower()
        found_terms = [term for term in legal_terms if term in query_lower]
        
        # Add "Canada" for jurisdiction
        if "canada" not in query_lower and "canadian" not in query_lower:
            found_terms.append("Canada")
        
        return found_terms[:5] if found_terms else ["legal", "law", "Canada"]
    
    def _search_web(self, state: SearchState) -> SearchState:
        """Perform web search using extracted keywords"""
        keywords = state.get("keywords", [])
        search_query = " ".join(keywords) + " site:canlii.org OR site:justice.gc.ca"
        
        try:
            search_results = self.search_tool.run(search_query)
            
            # Parse and structure results
            results_list = []
            if isinstance(search_results, str):
                # Simple parsing for DuckDuckGo results
                entries = search_results.split('\n\n')
                for entry in entries[:5]:  # Limit to top 5 results
                    if entry.strip():
                        results_list.append({
                            "content": entry.strip(),
                            "source": "DuckDuckGo Search",
                            "timestamp": datetime.now().isoformat()
                        })
            
            state["search_results"] = results_list
            logger.info(f"Found {len(results_list)} search results")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            state["search_results"] = []
            state["error_count"] = state.get("error_count", 0) + 1
        
        return state
    
    def _validate_results(self, state: SearchState) -> SearchState:
        """Validate search results and determine if retry is needed"""
        results = state.get("search_results", [])
        
        if len(results) < 2 and state.get("error_count", 0) < 2:
            state["needs_retry"] = True
            logger.info("Insufficient results, will retry with different LLM")
        else:
            state["needs_retry"] = False
            logger.info(f"Validation passed with {len(results)} results")
        
        return state
    
    def _should_retry(self, state: SearchState) -> str:
        """Determine if we should retry with a different LLM"""
        return "retry" if state.get("needs_retry", False) else "end"
    
    def _fallback_llm(self, state: SearchState) -> SearchState:
        """Switch to next available LLM for retry"""
        current_llm = state.get("current_llm", "")
        available_llms = list(self.llms.keys())
        
        try:
            current_index = available_llms.index(current_llm)
            next_index = (current_index + 1) % len(available_llms)
            state["current_llm"] = available_llms[next_index]
            logger.info(f"Switching to fallback LLM: {state['current_llm']}")
        except (ValueError, IndexError):
            state["current_llm"] = available_llms[0] if available_llms else "none"
        
        return state
    
    def search_legal_query(self, query: str) -> Dict:
        """Main method to process a legal query"""
        initial_state = SearchState(
            original_query=query,
            keywords=[],
            search_results=[],
            current_llm="",
            error_count=0,
            final_summary="",
            sources=[]
        )
        
        try:
            result = self.graph.invoke(initial_state)
            
            return {
                "success": True,
                "query": query,
                "keywords": result.get("keywords", []),
                "results": result.get("search_results", []),
                "llm_used": result.get("current_llm", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Search workflow failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

# Example usage and testing
if __name__ == "__main__":
    # Initialize the search system
    search_system = LegalSearchGraph(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # Test query
    test_query = "What is the difference between void and voidable contracts in Canadian law?"
    result = search_system.search_legal_query(test_query)
    
    print(json.dumps(result, indent=2))