from drafting.graph import LegalDocumentAgent
from clarification.graphSearch import LegalSearchGraph
from document_qa.graphRag import DocumentQARAG
import os

# Ensure output in the current directory
output_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Drafting Agent Graph
try:
    drafting_agent = LegalDocumentAgent()
    drafting_graph = drafting_agent.graph.get_graph(xray=True)
    img = drafting_graph.draw_mermaid_png()
    with open(os.path.join(output_dir, "drafting_graph.png"), "wb") as f:
        f.write(img)
    print("Drafting agent graph saved as drafting_graph.png")
except Exception as e:
    print(f"Error visualizing drafting agent graph: {e}")

# 2. Clarification Agent Graph
try:
    clarification_agent = LegalSearchGraph()
    clarification_graph = clarification_agent.graph.get_graph(xray=True)
    img = clarification_graph.draw_mermaid_png()
    with open(os.path.join(output_dir, "clarification_graph.png"), "wb") as f:
        f.write(img)
    print("Clarification agent graph saved as clarification_graph.png")
except Exception as e:
    print(f"Error visualizing clarification agent graph: {e}")

# 3. Document QA Agent Graph
try:
    docqa_agent = DocumentQARAG()
    docqa_graph = docqa_agent.workflow.get_graph(xray=True)
    img = docqa_graph.draw_mermaid_png()
    with open(os.path.join(output_dir, "document_qa_graph.png"), "wb") as f:
        f.write(img)
    print("Document QA agent graph saved as document_qa_graph.png")
except Exception as e:
    print(f"Error visualizing document QA agent graph: {e}") 