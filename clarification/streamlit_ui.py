"""
Legal Clarification System - Streamlit UI
Production-ready interface for legal query processing and summarization
"""

import streamlit as st
import os
import json
import time
from datetime import datetime
from typing import Dict, Optional
import logging
from pathlib import Path

# Import our custom modules
try:
    from graphSearch import LegalSearchGraph
    from summarize import LegalSummarizer
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Legal AI Clarification System",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    .query-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f4e79;
        margin: 1rem 0;
        color: #222;
    }
    
    .result-section {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        color: #222;
    }
    
    .citation-item {
        background-color: #e8f4f8;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 5px;
        border-left: 3px solid #1f4e79;
        color: #222;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #222;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #222;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
        color: #222;
    }
    
    /* Ensure all text is dark by default */
    body, div, span, p, h1, h2, h3, h4, h5, h6, label, input, textarea, button {
        color: #222 !important;
    }
</style>
""", unsafe_allow_html=True)

class LegalAIApp:
    """Main application class for the Legal AI Clarification System"""
    
    def __init__(self):
        self.initialize_session_state()
        # self.setup_sidebar()  # REMOVE SIDEBAR
        # Load API keys from environment only
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        # Set default summary options
        self.summary_type = "comprehensive"
        self.max_sources = 5
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        if 'current_query' not in st.session_state:
            st.session_state.current_query = ""
        if 'search_system' not in st.session_state:
            st.session_state.search_system = None
        if 'summarizer' not in st.session_state:
            st.session_state.summarizer = None
    
    def initialize_systems(self) -> tuple:
        """Initialize the search and summarization systems"""
        try:
            if not st.session_state.search_system or not st.session_state.summarizer:
                with st.spinner("Initializing AI systems..."):
                    st.session_state.search_system = LegalSearchGraph(
                        groq_api_key=self.groq_key,
                        gemini_api_key=self.gemini_key
                    )
                    st.session_state.summarizer = LegalSummarizer(
                        groq_api_key=self.groq_key,
                        gemini_api_key=self.gemini_key
                    )
                    st.success("✅ AI systems initialized successfully!")
            return st.session_state.search_system, st.session_state.summarizer
        except Exception as e:
            st.error(f"❌ Failed to initialize AI systems: {str(e)}")
            logger.error(f"System initialization error: {e}")
            return None, None
    
    def display_main_interface(self):
        """Display the main user interface"""
        st.markdown('<h1 class="main-header">⚖️ Legal AI Clarification System</h1>', 
                   unsafe_allow_html=True)
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Disclaimer:</strong> This system provides educational information about legal concepts only. 
            It does not constitute legal advice. Always consult with qualified legal professionals for specific legal matters.
        </div>
        """, unsafe_allow_html=True)
        # Query input section
        st.subheader("🔍 Ask Your Legal Question")
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_area(
                "Enter your legal question:",
                value=st.session_state.current_query,
                height=100,
                placeholder="e.g., What is the difference between void and voidable contracts in Canadian law?",
                help="Ask specific questions about Canadian legal concepts, statutes, or case law",
                key="legal_query_input"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            search_button = st.button("🔎 Search & Analyze", type="primary", use_container_width=True)
            clear_button = st.button("🗑️ Clear", use_container_width=True)
        if clear_button:
            st.session_state.current_query = ""
            st.rerun()
        # Example queries
        st.markdown("### 💡 Example Queries")
        example_col1, example_col2 = st.columns(2)
        with example_col1:
            if st.button("📄 Contract Law Example"):
                st.session_state.current_query = "What is the difference between void and voidable contracts in Canadian law?"
                st.rerun()
            if st.button("🏠 Property Law Example"):
                st.session_state.current_query = "What are the requirements for adverse possession in Ontario?"
                st.rerun()
        with example_col2:
            if st.button("⚖️ Tort Law Example"):
                st.session_state.current_query = "What constitutes negligence under Canadian tort law?"
                st.rerun()
            if st.button("👥 Family Law Example"):
                st.session_state.current_query = "How is child custody determined in Canadian family courts?"
                st.rerun()
        return query, search_button
    
    def process_legal_query(self, query: str, search_system, summarizer, summary_type: str):
        """Process the legal query through search and summarization"""
        
        if not query.strip():
            st.warning("⚠️ Please enter a legal question to search.")
            return
        
        # Store current query
        st.session_state.current_query = query
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Search
            status_text.text("🔍 Searching legal databases...")
            progress_bar.progress(25)
            
            search_results = search_system.search_legal_query(query)
            
            if not search_results.get("success", False):
                st.error(f"❌ Search failed: {search_results.get('error', 'Unknown error')}")
                return
            
            # Step 2: Summarize
            status_text.text("🤖 Analyzing and summarizing results...")
            progress_bar.progress(75)
            
            if summary_type == "comprehensive":
                summary_results = summarizer.generate_comprehensive_summary(search_results)
            else:
                summary_results = summarizer.generate_quick_answer(search_results)
            
            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")
            
            # Clear progress indicators
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            self.display_results(query, search_results, summary_results, summary_type)
            
            # Add to history
            self.add_to_history(query, search_results, summary_results)
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Processing failed: {str(e)}")
            logger.error(f"Query processing error: {e}")
    
    def display_results(self, query: str, search_results: Dict, summary_results: Dict, summary_type: str):
        """Display the search and summary results"""
        
        st.markdown("---")
        st.subheader("📋 Analysis Results")
        
        # Query display
        st.markdown(f"""
        <div class="query-box">
            <strong>🔍 Your Question:</strong><br>
            {query}
        </div>
        """, unsafe_allow_html=True)
        
        # Results tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📄 Summary", "🔍 Search Details", "📚 Citations", "📊 Statistics"])
        
        with tab1:
            self.display_summary_tab(summary_results, summary_type)
        
        with tab2:
            self.display_search_tab(search_results)
        
        with tab3:
            self.display_citations_tab(summary_results)
        
        with tab4:
            self.display_statistics_tab(search_results, summary_results)
    
    def display_summary_tab(self, summary_results: Dict, summary_type: str):
        """Display the summary results tab"""
        
        if not summary_results.get("success", False):
            st.error(f"❌ Summary generation failed: {summary_results.get('error', 'Unknown error')}")
            return
        
        summary = summary_results.get("summary", "")
        
        if summary_type == "comprehensive":
            st.markdown("### 📖 Comprehensive Legal Analysis")
        else:
            st.markdown("### ⚡ Quick Answer")
        
        st.markdown(f"""
        <div class="result-section">
            {summary.replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.code(summary, language=None)
        
        with col2:
            st.download_button(
                label="💾 Download as Text",
                data=summary,
                file_name=f"legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col3:
            # Convert to JSON for download
            full_data = {
                "query": summary_results.get("query", ""),
                "summary": summary,
                "timestamp": summary_results.get("timestamp", ""),
                "type": summary_type
            }
            st.download_button(
                label="📦 Download as JSON",
                data=json.dumps(full_data, indent=2),
                file_name=f"legal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def display_search_tab(self, search_results: Dict):
        """Display the search results tab"""
        
        st.markdown("### 🔍 Search Process Details")
        
        # Keywords used
        keywords = search_results.get("keywords", [])
        if keywords:
            st.markdown("**🏷️ Keywords Extracted:**")
            keyword_tags = " ".join([f"`{kw}`" for kw in keywords])
            st.markdown(keyword_tags)
        
        # LLM used
        llm_used = search_results.get("llm_used", "Unknown")
        st.markdown(f"**🤖 AI Model Used:** `{llm_used}`")
        
        # Search results
        results = search_results.get("results", [])
        st.markdown(f"**📊 Sources Found:** {len(results)}")
        
        if results:
            for i, result in enumerate(results, 1):
                with st.expander(f"📄 Source {i}"):
                    content = result.get("content", "")
                    source = result.get("source", "Unknown")
                    
                    st.markdown(f"**Source:** {source}")
                    st.markdown("**Content Preview:**")
                    
                    # Truncate long content
                    if len(content) > 500:
                        content_preview = content[:500] + "..."
                    else:
                        content_preview = content
                    
                    st.text(content_preview)
    
    def display_citations_tab(self, summary_results: Dict):
        """Display the citations tab"""
        
        st.markdown("### 📚 Legal Sources & Citations")
        
        citations = summary_results.get("citations", [])
        
        if citations:
            st.markdown(f"**Found {len(citations)} legal sources:**")
            
            for i, citation in enumerate(citations, 1):
                st.markdown(f"""
                <div class="citation-item">
                    <strong>{i}.</strong> {citation}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No specific citations were extracted from the analyzed content.")
        
        # Disclaimer
        st.markdown("""
        <div class="warning-box">
            <strong>⚠️ Citation Note:</strong> These citations are extracted from search results and may require verification. 
            Always cross-reference with official legal databases and consult legal professionals for authoritative sources.
        </div>
        """, unsafe_allow_html=True)
    
    def display_statistics_tab(self, search_results: Dict, summary_results: Dict):
        """Display statistics about the analysis"""
        
        st.markdown("### 📊 Analysis Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔍 Search Metrics")
            
            # Search stats
            keywords_count = len(search_results.get("keywords", []))
            sources_count = len(search_results.get("results", []))
            
            st.metric("Keywords Extracted", keywords_count)
            st.metric("Sources Found", sources_count)
            st.metric("LLM Used", search_results.get("llm_used", "N/A"))
        
        with col2:
            st.markdown("#### 📝 Summary Metrics")
            
            if summary_results.get("success", False):
                summary = summary_results.get("summary", "")
                word_count = len(summary.split())
                char_count = len(summary)
                citation_count = len(summary_results.get("citations", []))
                
                st.metric("Word Count", word_count)
                st.metric("Character Count", char_count)
                st.metric("Citations Found", citation_count)
            else:
                st.error("Summary statistics unavailable")
        
        # Processing time
        timestamp = summary_results.get("timestamp", "")
        if timestamp:
            st.markdown(f"**⏱️ Processed at:** {timestamp}")
    
    def add_to_history(self, query: str, search_results: Dict, summary_results: Dict):
        """Add the current query to search history"""
        
        history_item = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "success": summary_results.get("success", False),
            "summary_preview": summary_results.get("summary", "")[:200] + "..." if summary_results.get("summary", "") else "",
            "sources_count": len(search_results.get("results", [])),
            "llm_used": search_results.get("llm_used", "Unknown")
        }
        
        st.session_state.search_history.insert(0, history_item)
        
        # Keep only last 10 items
        if len(st.session_state.search_history) > 10:
            st.session_state.search_history = st.session_state.search_history[:10]
    
    def display_search_history(self):
        """Display search history in sidebar"""
        
        if st.session_state.search_history:
            st.sidebar.markdown("---")
            st.sidebar.subheader("📜 Recent Searches")
            
            for i, item in enumerate(st.session_state.search_history[:5]):  # Show last 5
                with st.sidebar.expander(f"Query {i+1}: {item['query'][:30]}..."):
                    st.sidebar.markdown(f"**Time:** {item['timestamp'][:19]}")
                    st.sidebar.markdown(f"**Status:** {'✅' if item['success'] else '❌'}")
                    st.sidebar.markdown(f"**Sources:** {item['sources_count']}")
                    st.sidebar.markdown(f"**LLM:** {item['llm_used']}")
                    
                    if st.sidebar.button(f"🔄 Rerun Query {i+1}", key=f"rerun_{i}"):
                        st.session_state.current_query = item['query']
                        st.rerun()
    
    def run(self):
        """Main application runner"""
        
        # Initialize systems
        search_system, summarizer = self.initialize_systems()
        
        if not search_system or not summarizer:
            st.error("❌ Failed to initialize AI systems. Please check your API keys and try again.")
            st.stop()
        
        # Display main interface
        query, search_button = self.display_main_interface()
        
        # Process query if search button is clicked
        if search_button and query.strip():
            self.process_legal_query(query, search_system, summarizer, self.summary_type)

# Main execution
def main():
    """Main function to run the Streamlit app"""
    try:
        app = LegalAIApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()