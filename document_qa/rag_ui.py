import streamlit as st
import tempfile
import os
from pathlib import Path
import time
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the RAG system
from graphRag import DocumentQARAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Legal Document QA System",
    page_icon="📄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #1f77b4;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 0.5rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #155a8a;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitDocumentQA:
    """Streamlit app wrapper for DocumentQARAG"""
    
    def __init__(self):
        self.rag_system: Optional[DocumentQARAG] = None
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'rag_system' not in st.session_state:
            try:
                st.session_state.rag_system = DocumentQARAG(
                    groq_api_key=os.getenv("GROQ_API_KEY"),
                    google_api_key=os.getenv("GEMINI_API_KEY")
                )
                logger.info("RAG system initialized")
            except Exception as e:
                st.error(f"❌ Error initializing system: {str(e)}")
                logger.error(f"System initialization error: {e}")
        if 'document_processed' not in st.session_state:
            st.session_state.document_processed = False
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_document' not in st.session_state:
            st.session_state.current_document = None
    
    def document_upload_section(self):
        """Document upload and processing section"""
        st.header("📄 Document Upload & Processing")
        
        if not st.session_state.rag_system:
            st.error("❌ Please initialize the system first.")
            st.error("❌ Please initialize the system first using the sidebar.")
            return
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Choose a document",
                type=['pdf', 'docx', 'doc', 'txt'],
                help="Upload a PDF, DOCX, or TXT file"
            )
        
        with col2:
            if uploaded_file is not None:
                st.info(f"""
                **File Details:**
                - Name: {uploaded_file.name}
                - Size: {uploaded_file.size / 1024:.1f} KB
                - Type: {uploaded_file.type}
                """)
        
        if uploaded_file is not None:
            if st.button("🚀 Process Document", type="primary"):
                self.process_uploaded_document(uploaded_file)
    
    def process_uploaded_document(self, uploaded_file):
        """Process the uploaded document"""
        try:
            with st.spinner("Processing document..."):
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Determine file type
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                # Process document
                result = st.session_state.rag_system.process_document_and_query(
                    file_path=tmp_file_path,
                    file_type=file_extension,
                    query="What is this document about?"  # Initial query to test processing
                )
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                if result['success']:
                    st.session_state.document_processed = True
                    st.session_state.current_document = uploaded_file.name
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <strong>✅ Document processed successfully!</strong><br>
                        You can now ask questions about: <strong>{uploaded_file.name}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show initial summary
                    with st.expander("📋 Document Summary", expanded=True):
                        st.write("**Initial Analysis:**")
                        st.write(result['answer'])
                    
                    logger.info(f"Document processed: {uploaded_file.name}")
                else:
                    st.markdown(f"""
                    <div class="error-box">
                        <strong>❌ Error processing document:</strong><br>
                        {result.get('error', 'Unknown error occurred')}
                    </div>
                    """, unsafe_allow_html=True)
                    logger.error(f"Document processing error: {result.get('error')}")
        
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Unexpected error:</strong><br>
                {str(e)}
            </div>
            """, unsafe_allow_html=True)
            logger.error(f"Unexpected error: {e}")
    
    def question_answer_section(self):
        """Question and answer section"""
        st.header("💬 Ask Questions")
        
        if not st.session_state.document_processed:
            st.markdown("""
            <div class="info-box">
                <strong>ℹ️ Ready to answer questions!</strong><br>
                Upload and process a document first to start asking questions.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Question input
        question = st.text_input(
            "Ask a question about your document:",
            placeholder="e.g., What are the main points discussed in this document?",
            key="question_input"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            ask_button = st.button("🤔 Ask Question", type="primary")
        with col2:
            clear_history = st.button("🗑️ Clear History")
        
        if clear_history:
            st.session_state.chat_history = []
            st.rerun()
        
        if ask_button and question:
            self.process_question(question)
        
        # Display chat history
        if st.session_state.chat_history:
            st.subheader("💭 Chat History")
            for i, (q, a, timestamp) in enumerate(reversed(st.session_state.chat_history)):
                with st.expander(f"Q{len(st.session_state.chat_history)-i}: {q[:50]}..." if len(q) > 50 else f"Q{len(st.session_state.chat_history)-i}: {q}", expanded=(i==0)):
                    st.write(f"**Question:** {q}")
                    st.write(f"**Answer:** {a}")
                    st.caption(f"Asked at: {timestamp}")
    
    def process_question(self, question: str):
        """Process user question"""
        try:
            with st.spinner("Thinking..."):
                result = st.session_state.rag_system.query_existing_documents(question)
            
            if result['success']:
                # Add to chat history
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.chat_history.append((question, result['answer'], timestamp))
                
                # Display answer
                st.markdown(f"""
                <div class="success-box">
                    <strong>🤖 Answer:</strong><br>
                    {result['answer']}
                </div>
                """, unsafe_allow_html=True)
                
                logger.info(f"Question answered: {question[:50]}...")
            else:
                st.markdown(f"""
                <div class="error-box">
                    <strong>❌ Error answering question:</strong><br>
                    {result.get('error', 'Unknown error occurred')}
                </div>
                """, unsafe_allow_html=True)
                logger.error(f"Question answering error: {result.get('error')}")
        
        except Exception as e:
            st.markdown(f"""
            <div class="error-box">
                <strong>❌ Unexpected error:</strong><br>
                {str(e)}
            </div>
            """, unsafe_allow_html=True)
            logger.error(f"Unexpected error: {e}")
    
    def run(self):
        """Run the Streamlit app"""
        # Header
        st.markdown('<h1 class="main-header">📄 Legal Document QA System</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Main content
        tab1, tab2, tab3 = st.tabs(["📄 Document Upload", "💬 Q&A Chat", "📊 Analytics"])
        
        with tab1:
            self.document_upload_section()
        
        with tab2:
            self.question_answer_section()
        
        with tab3:
            self.analytics_section()
    
    def analytics_section(self):
        """Analytics and insights section"""
        st.header("📊 Analytics & Insights")
        
        if not st.session_state.chat_history:
            st.markdown("""
            <div class="info-box">
                <strong>ℹ️ No analytics available yet</strong><br>
                Start asking questions to see analytics and insights about your interactions.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Basic statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Questions", len(st.session_state.chat_history))
        
        with col2:
            if st.session_state.current_document:
                st.metric("Current Document", "1")
            else:
                st.metric("Current Document", "0")
        
        with col3:
            avg_question_length = sum(len(q) for q, _, _ in st.session_state.chat_history) / len(st.session_state.chat_history)
            st.metric("Avg Question Length", f"{avg_question_length:.0f} chars")
        
        with col4:
            avg_answer_length = sum(len(a) for _, a, _ in st.session_state.chat_history) / len(st.session_state.chat_history)
            st.metric("Avg Answer Length", f"{avg_answer_length:.0f} chars")
        
        # Recent activity
        st.subheader("🕒 Recent Activity")
        if len(st.session_state.chat_history) >= 5:
            recent_questions = st.session_state.chat_history[-5:]
        else:
            recent_questions = st.session_state.chat_history
        
        for i, (question, answer, timestamp) in enumerate(reversed(recent_questions)):
            st.write(f"**{timestamp}:** {question[:100]}..." if len(question) > 100 else f"**{timestamp}:** {question}")
        
        # Export functionality
        st.subheader("📥 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export Chat History"):
                self.export_chat_history()
        
        with col2:
            if st.button("📊 Download Analytics Report"):
                self.download_analytics_report()
    
    def export_chat_history(self):
        """Export chat history as text file"""
        if not st.session_state.chat_history:
            st.warning("No chat history to export")
            return
        
        export_text = f"Chat History Export - {st.session_state.current_document}\n"
        export_text += "=" * 50 + "\n\n"
        
        for i, (question, answer, timestamp) in enumerate(st.session_state.chat_history, 1):
            export_text += f"Question {i} ({timestamp}):\n{question}\n\n"
            export_text += f"Answer {i}:\n{answer}\n\n"
            export_text += "-" * 30 + "\n\n"
        
        st.download_button(
            label="💾 Download Chat History",
            data=export_text,
            file_name=f"chat_history_{st.session_state.current_document}_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    def download_analytics_report(self):
        """Download analytics report"""
        if not st.session_state.chat_history:
            st.warning("No data available for analytics report")
            return
        
        report = f"Analytics Report - {st.session_state.current_document}\n"
        report += "=" * 50 + "\n\n"
        report += f"Total Questions Asked: {len(st.session_state.chat_history)}\n"
        report += f"Document Processed: {st.session_state.current_document}\n"
        report += f"Average Question Length: {sum(len(q) for q, _, _ in st.session_state.chat_history) / len(st.session_state.chat_history):.1f} characters\n"
        report += f"Average Answer Length: {sum(len(a) for _, a, _ in st.session_state.chat_history) / len(st.session_state.chat_history):.1f} characters\n\n"
        
        report += "Most Recent Questions:\n"
        report += "-" * 20 + "\n"
        recent = st.session_state.chat_history[-5:] if len(st.session_state.chat_history) >= 5 else st.session_state.chat_history
        for question, _, timestamp in recent:
            report += f"• {timestamp}: {question}\n"
        
        st.download_button(
            label="📊 Download Analytics Report",
            data=report,
            file_name=f"analytics_report_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )


def main():
    """Main function to run the Streamlit app"""
    try:
        app = StreamlitDocumentQA()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        logger.error(f"Application error: {e}")


if __name__ == "__main__":
    main()