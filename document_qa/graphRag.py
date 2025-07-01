import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import tempfile
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentQAState(TypedDict):
    """State for the Document QA workflow"""
    documents: List[Document]
    query: str
    context: List[Document]
    answer: str
    error: Optional[str]
    embeddings_created: bool
    retriever_ready: bool

class DocumentProcessor:
    """Handles document loading and text splitting"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_document(self, file_path: str, file_type: str) -> List[Document]:
        """Load document based on file type"""
        try:
            if file_type.lower() == 'pdf':
                loader = PyPDFLoader(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                loader = Docx2txtLoader(file_path)
            elif file_type.lower() == 'txt':
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} pages from {file_path}")
            return documents
        
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            raise
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        try:
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split documents into {len(chunks)} chunks")
            return chunks
        except Exception as e:
            logger.error(f"Error splitting documents: {e}")
            raise

class VectorStoreManager:
    """Manages vector store operations with ChromaDB"""
    
    def __init__(self, collection_name: str = "document_qa", persist_directory: str = "./chroma_db"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embeddings = self._initialize_embeddings()
        self.vectorstore = None
        self.retriever = None
        
        # Ensure persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
    
    def _initialize_embeddings(self) -> HuggingFaceEmbeddings:
        """Initialize HuggingFace embeddings"""
        try:
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("HuggingFace embeddings initialized successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            raise
    
    def create_vectorstore(self, documents: List[Document]) -> bool:
        """Create or update vector store with documents"""
        try:
            if not documents:
                raise ValueError("No documents provided")
            
            # Create ChromaDB client
            client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create vector store
            self.vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name=self.collection_name,
                persist_directory=self.persist_directory,
                client=client
            )
            
            # Create retriever
            self.retriever = self.vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            logger.info(f"Vector store created with {len(documents)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            return False
    
    def get_retriever(self):
        """Get the retriever instance"""
        if not self.retriever:
            raise ValueError("Vector store not initialized. Call create_vectorstore first.")
        return self.retriever

class LLMManager:
    """Manages LLM instances with fallback mechanism"""
    
    def __init__(self, groq_api_key: str = None, google_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.primary_llm = None
        self.fallback_llm = None
        self._initialize_llms()
    
    def _initialize_llms(self):
        """Initialize LLM instances"""
        # Initialize Groq LLM (Primary)
        if self.groq_api_key:
            try:
                self.primary_llm = ChatGroq(
                    groq_api_key=self.groq_api_key,
                    model_name="llama3-70b-8192",
                    temperature=0.3,
                    max_tokens=500
                )
                logger.info("Groq LLM initialized as primary")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq LLM: {e}")
        
        # Initialize Gemini 2.pre LLM (Fallback)
        if self.google_api_key:
            try:
                self.fallback_llm = ChatGoogleGenerativeAI(
                    google_api_key=self.google_api_key,
                    model="gemini-2.5-pro",
                    temperature=0.3,
                    max_tokens=500
                )
                logger.info("Gemini 2.pre LLM initialized as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini LLM: {e}")
        
        if not self.primary_llm and not self.fallback_llm:
            raise ValueError("No LLM could be initialized. Check your API keys.")
    
    def get_llm(self, use_fallback: bool = False):
        """Get LLM instance with fallback logic"""
        try:
            if not use_fallback and self.primary_llm:
                return self.primary_llm
            elif self.fallback_llm:
                return self.fallback_llm
            else:
                raise ValueError("No LLM available")
        except Exception as e:
            logger.error(f"Error getting LLM: {e}")
            raise

class DocumentQARAG:
    """Main RAG system using LangGraph"""
    
    def __init__(self, groq_api_key: str = None, google_api_key: str = None):
        self.document_processor = DocumentProcessor()
        self.vector_manager = VectorStoreManager()
        self.llm_manager = LLMManager(groq_api_key, google_api_key)
        self.workflow = self._create_workflow()
        self.system_prompt = (
        "You are a helpful AI assistant specialized in answering user questions based on retrieved documents and context. "
        "Use ONLY the information provided in the retrieved context to answer the question. Do not use prior knowledge or make assumptions. "
        "If the answer is not present in the context, say \"I couldn't find the answer based on the provided information.\" "
        "Use a maximum of three sentences and keep the response concise. "
        "If the context contains conflicting information, acknowledge it and do not guess."
        "\n\n"
        "{context}"
)

    
    def _create_workflow(self) -> CompiledStateGraph:
        """Create LangGraph workflow"""
        workflow = StateGraph(DocumentQAState)
        
        # Add nodes
        workflow.add_node("process_documents", self._process_documents)
        workflow.add_node("create_embeddings", self._create_embeddings)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("fallback_generate", self._fallback_generate)
        
        # Add edges
        workflow.set_entry_point("process_documents")
        workflow.add_edge("process_documents", "create_embeddings")
        workflow.add_edge("create_embeddings", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_answer")
        workflow.add_edge("fallback_generate", END)
        
        # Add conditional edge for fallback
        workflow.add_conditional_edges(
            "generate_answer",
            self._should_use_fallback,
            {
                "fallback": "fallback_generate",
                "end": END
            }
        )
        
        return workflow.compile()
    
    def _process_documents(self, state: DocumentQAState) -> DocumentQAState:
        """Process and chunk documents"""
        try:
            if state.get("documents"):
                chunks = self.document_processor.split_documents(state["documents"])
                state["documents"] = chunks
                logger.info("Documents processed successfully")
            return state
        except Exception as e:
            state["error"] = f"Document processing error: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _create_embeddings(self, state: DocumentQAState) -> DocumentQAState:
        """Create vector embeddings"""
        try:
            if state.get("documents") and not state.get("error"):
                success = self.vector_manager.create_vectorstore(state["documents"])
                state["embeddings_created"] = success
                state["retriever_ready"] = success
                if success:
                    logger.info("Embeddings created successfully")
                else:
                    state["error"] = "Failed to create embeddings"
            return state
        except Exception as e:
            state["error"] = f"Embedding creation error: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _retrieve_context(self, state: DocumentQAState) -> DocumentQAState:
        """Retrieve relevant context"""
        try:
            if state.get("retriever_ready") and state.get("query") and not state.get("error"):
                retriever = self.vector_manager.get_retriever()
                context = retriever.invoke(state["query"])
                state["context"] = context
                logger.info(f"Retrieved {len(context)} context documents")
            return state
        except Exception as e:
            state["error"] = f"Context retrieval error: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _generate_answer(self, state: DocumentQAState) -> DocumentQAState:
        """Generate answer using primary LLM"""
        try:
            if state.get("context") and state.get("query") and not state.get("error"):
                llm = self.llm_manager.get_llm(use_fallback=False)
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("human", "{input}"),
                ])
                
                question_answer_chain = create_stuff_documents_chain(llm, prompt)
                rag_chain = create_retrieval_chain(
                    self.vector_manager.get_retriever(), 
                    question_answer_chain
                )
                
                response = rag_chain.invoke({"input": state["query"]})
                state["answer"] = response.get("answer", "No answer generated")
                logger.info("Answer generated using primary LLM")
                
            return state
        except Exception as e:
            state["error"] = f"Primary LLM error: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _fallback_generate(self, state: DocumentQAState) -> DocumentQAState:
        """Generate answer using fallback LLM"""
        try:
            if state.get("context") and state.get("query"):
                llm = self.llm_manager.get_llm(use_fallback=True)
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    ("human", "{input}"),
                ])
                
                question_answer_chain = create_stuff_documents_chain(llm, prompt)
                rag_chain = create_retrieval_chain(
                    self.vector_manager.get_retriever(), 
                    question_answer_chain
                )
                
                response = rag_chain.invoke({"input": state["query"]})
                state["answer"] = response.get("answer", "No answer generated")
                state["error"] = None  # Clear error since fallback worked
                logger.info("Answer generated using fallback LLM")
                
            return state
        except Exception as e:
            state["error"] = f"Fallback LLM error: {str(e)}"
            logger.error(state["error"])
            return state
    
    def _should_use_fallback(self, state: DocumentQAState) -> str:
        """Decide whether to use fallback LLM"""
        if state.get("error") and not state.get("answer"):
            return "fallback"
        return "end"
    
    def process_document_and_query(self, file_path: str, file_type: str, query: str) -> Dict[str, Any]:
        """Process document and answer query"""
        try:
            # Load documents
            documents = self.document_processor.load_document(file_path, file_type)
            
            # Initialize state
            initial_state = DocumentQAState(
                documents=documents,
                query=query,
                context=[],
                answer="",
                error=None,
                embeddings_created=False,
                retriever_ready=False
            )
            
            # Run workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "answer": final_state.get("answer", "No answer generated"),
                "error": final_state.get("error"),
                "success": bool(final_state.get("answer") and not final_state.get("error"))
            }
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "answer": "",
                "error": str(e),
                "success": False
            }
    
    def query_existing_documents(self, query: str) -> Dict[str, Any]:
        """Query against already processed documents"""
        try:
            if not self.vector_manager.retriever:
                return {
                    "answer": "",
                    "error": "No documents loaded. Please upload a document first.",
                    "success": False
                }
            
            initial_state = DocumentQAState(
                documents=[],
                query=query,
                context=[],
                answer="",
                error=None,
                embeddings_created=True,
                retriever_ready=True
            )
            
            # Skip document processing and embedding creation
            state = self._retrieve_context(initial_state)
            state = self._generate_answer(state)
            
            if state.get("error") and not state.get("answer"):
                state = self._fallback_generate(state)
            
            return {
                "answer": state.get("answer", "No answer generated"),
                "error": state.get("error"),
                "success": bool(state.get("answer") and not state.get("error"))
            }
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return {
                "answer": "",
                "error": str(e),
                "success": False
            }

# Example usage
if __name__ == "__main__":
    # Initialize the RAG system
    rag_system = DocumentQARAG(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # Process document and query
    result = rag_system.process_document_and_query(
        file_path="./example.pdf",
        file_type="pdf",
        query="What is the main topic of this document?"
    )
    
    print(f"Answer: {result['answer']}")
    if result['error']:
        print(f"Error: {result['error']}")