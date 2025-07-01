"""
Legal Content Summarizer with Multi-LLM Support
Processes search results and generates comprehensive legal summaries
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalSummarizer:
    """AI-powered legal content summarizer with fallback LLM support"""
    
    def __init__(self, groq_api_key: str = None, gemini_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # Initialize LLMs
        self.llms = self._initialize_llms()
        
        # Text splitter for long content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Legal summarization prompts
        self.prompts = self._create_prompts()
        
    def _initialize_llms(self) -> Dict:
        """Initialize LLMs with fallback mechanism"""
        llms = {}
        
        # Primary: Groq
        if self.groq_api_key:
            try:
                llms['groq'] = ChatGroq(
                    groq_api_key=self.groq_api_key,
                    model_name="llama3-70b-8192",
                    temperature=0.1,
                    max_tokens=2000
                )
                logger.info("Groq LLM initialized for summarization")
            except Exception as e:
                logger.warning(f"Groq initialization failed: {e}")
        
        # Secondary: Gemini
        if self.gemini_api_key:
            try:
                llms['gemini'] = ChatGoogleGenerativeAI(
                    google_api_key=self.gemini_api_key,
                    model="gemini-1.5-flash",
                    temperature=0.1,
                    max_output_tokens=2000
                )
                logger.info("Gemini LLM initialized for summarization")
            except Exception as e:
                logger.warning(f"Gemini initialization failed: {e}")
        
        if not llms:
            raise Exception("No LLM available for summarization")
        
        return llms
    
    def _create_prompts(self) -> Dict[str, PromptTemplate]:
        """Create specialized prompts for different summarization tasks"""
        
        legal_summary_prompt = PromptTemplate(
            template="""
You are a legal expert specializing in Canadian law. Analyze the provided legal content and create a comprehensive summary.

CONTENT TO ANALYZE:
{content}

ORIGINAL QUERY: {query}

Please provide a structured summary that includes:

1. **DIRECT ANSWER**: A clear, concise answer to the specific legal question asked.

2. **KEY LEGAL CONCEPTS**: Explain the main legal principles involved.

3. **CANADIAN LEGAL CONTEXT**: How these concepts apply specifically in Canadian law, including relevant provinces if applicable.

4. **PRACTICAL IMPLICATIONS**: What this means in real-world legal scenarios.

5. **SOURCES**: Reference any specific statutes, cases, or legal authorities mentioned.

Format your response in clear sections. Be precise, accurate, and focus on Canadian legal precedents.
Do not provide legal advice - only educational information about legal concepts.

SUMMARY:
""",
            input_variables=["content", "query"]
        )
        
        quick_answer_prompt = PromptTemplate(
            template="""
Based on the legal content provided, give a concise but complete answer to this question: {query}

LEGAL CONTENT:
{content}

Provide a focused answer that:
- Directly addresses the question
- Uses proper legal terminology
- Mentions Canadian law context
- Is clear and understandable

ANSWER:
""",
            input_variables=["content", "query"]
        )
        
        citation_prompt = PromptTemplate(
            template="""
Extract and format legal citations from this content. Focus on Canadian legal sources.

CONTENT:
{content}

List all legal sources mentioned including:
- Statutes and acts
- Case law (court decisions)
- Legal authorities
- Government sources

Format as a numbered list with proper legal citation format.

CITATIONS:
""",
            input_variables=["content"]
        )
        
        return {
            "comprehensive": legal_summary_prompt,
            "quick": quick_answer_prompt,
            "citations": citation_prompt
        }
    
    def _extract_clean_content(self, search_results: List[Dict]) -> str:
        """Extract and clean content from search results"""
        combined_content = []
        
        for result in search_results:
            content = result.get("content", "")
            if content:
                # Clean the content
                cleaned = self._clean_text(content)
                if len(cleaned) > 100:  # Only include substantial content
                    combined_content.append(cleaned)
        
        return "\n\n---\n\n".join(combined_content)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML-like tags if present
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Clean up special characters but keep legal punctuation
        text = re.sub(r'[^\w\s\.,;:()"\'-]', '', text)
        
        return text.strip()
    
    def _generate_with_fallback(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Generate response with LLM fallback mechanism"""
        
        for llm_name, llm in self.llms.items():
            for attempt in range(max_retries):
                try:
                    response = llm.invoke([HumanMessage(content=prompt)])
                    
                    if hasattr(response, 'content'):
                        content = response.content
                    else:
                        content = str(response)
                    
                    if content and len(content.strip()) > 50:
                        logger.info(f"Summary generated using {llm_name} (attempt {attempt + 1})")
                        return content.strip()
                    
                except Exception as e:
                    logger.warning(f"Generation failed with {llm_name} (attempt {attempt + 1}): {e}")
                    continue
        
        return None
    
    def summarize_search_results(self, search_data: Dict, summary_type: str = "comprehensive") -> Dict:
        """Main method to summarize legal search results"""
        
        if not search_data.get("success", False):
            return {
                "success": False,
                "error": "Search data indicates failure",
                "timestamp": datetime.now().isoformat()
            }
        
        query = search_data.get("query", "")
        results = search_data.get("results", [])
        
        if not results:
            return {
                "success": False,
                "error": "No search results to summarize",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        # Extract and clean content
        content = self._extract_clean_content(results)
        
        if not content:
            return {
                "success": False,
                "error": "No usable content found in search results",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        # Split content if too long
        if len(content) > 8000:
            chunks = self.text_splitter.split_text(content)
            content = "\n\n".join(chunks[:3])  # Use first 3 chunks
        
        # Generate summary based on type
        summary_prompt = self.prompts.get(summary_type, self.prompts["comprehensive"])
        prompt_text = summary_prompt.format(content=content, query=query)
        
        summary = self._generate_with_fallback(prompt_text)
        
        if not summary:
            return {
                "success": False,
                "error": "Failed to generate summary with all available LLMs",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        # Generate citations if comprehensive summary
        citations = []
        if summary_type == "comprehensive":
            citation_prompt = self.prompts["citations"].format(content=content)
            citation_text = self._generate_with_fallback(citation_prompt)
            if citation_text:
                citations = self._parse_citations(citation_text)
        
        return {
            "success": True,
            "query": query,
            "summary": summary,
            "citations": citations,
            "summary_type": summary_type,
            "content_length": len(content),
            "source_count": len(results),
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_citations(self, citation_text: str) -> List[str]:
        """Parse citations from generated text"""
        citations = []
        
        # Split by lines and clean
        lines = citation_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering and clean
                citation = re.sub(r'^\d+\.?\s*', '', line)
                citation = re.sub(r'^-\s*', '', citation)
                if len(citation) > 10:  # Only substantial citations
                    citations.append(citation)
        
        return citations[:10]  # Limit to 10 citations
    
    def generate_quick_answer(self, search_data: Dict) -> Dict:
        """Generate a quick, focused answer"""
        return self.summarize_search_results(search_data, "quick")
    
    def generate_comprehensive_summary(self, search_data: Dict) -> Dict:
        """Generate a comprehensive legal summary"""
        return self.summarize_search_results(search_data, "comprehensive")
    
    def get_summary_stats(self, summary_data: Dict) -> Dict:
        """Get statistics about the generated summary"""
        if not summary_data.get("success", False):
            return {"error": "No valid summary data"}
        
        summary = summary_data.get("summary", "")
        
        return {
            "word_count": len(summary.split()),
            "character_count": len(summary),
            "citation_count": len(summary_data.get("citations", [])),
            "source_count": summary_data.get("source_count", 0),
            "summary_type": summary_data.get("summary_type", "unknown"),
            "processing_time": summary_data.get("timestamp", "")
        }

# Example usage and testing
if __name__ == "__main__":
    # Mock search data for testing
    mock_search_data = {
        "success": True,
        "query": "What is the difference between void and voidable contracts in Canadian law?",
        "results": [
            {
                "content": "In Canadian contract law, a void contract is one that has no legal effect from the beginning. It is treated as if it never existed. Examples include contracts for illegal purposes or contracts lacking essential elements like consideration. A voidable contract, on the other hand, is valid but can be cancelled by one of the parties due to factors like misrepresentation, duress, or undue influence.",
                "source": "Legal Database"
            },
            {
                "content": "The distinction between void and voidable contracts is crucial in Canadian jurisprudence. Void contracts cannot be enforced by either party and are considered null ab initio. Voidable contracts remain valid until the affected party chooses to void them. Provincial legislation and common law principles govern these concepts across Canada.",
                "source": "Canadian Law Review"
            }
        ]
    }
    
    # Initialize summarizer
    summarizer = LegalSummarizer(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # Test comprehensive summary
    result = summarizer.generate_comprehensive_summary(mock_search_data)
    print(json.dumps(result, indent=2))
    
    # Test quick answer
    quick_result = summarizer.generate_quick_answer(mock_search_data)
    print("\nQuick Answer:")
    print(json.dumps(quick_result, indent=2))