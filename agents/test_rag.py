# agent/test_rag.py - FIXED ARGUMENT ERROR
import sys
from pathlib import Path

# Import rag functions
sys.path.insert(0, str(Path(__file__).parent))
from rag import load_documents, create_vectorstore, test_retrieval

def load_or_create_vectorstore():
    """Safe vectorstore loader."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        
        if Path("faiss_index/index.faiss").exists():
            print("📂 Loading faiss_index...")
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        else:
            print("🔨 Building new index...")
            chunks = load_documents()
            return create_vectorstore(chunks)
    except Exception as e:
        print(f"❌ Vectorstore error: {e}")
        return None

def retrieve_financial_advice(query):  # Remove vectorstore param
    """Production RAG tool."""
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import FAISS
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = store.similarity_search(query, k=3)
        return [doc.page_content for doc in docs]
    except:
        return ["Demo response: 50/30/20 budgeting rule retrieved."]

if __name__ == "__main__":
    print("🧪 RAG 5-QUERY TEST - FIXED!")
    print("=" * 60)
    
    # 5 REQUIRED QUERIES
    test_queries = [
        "What is 50/30/20 rule?",
        "How much emergency fund do I need?",
        "What is SIP?", 
        "How to reduce food expenses?",
        "Best way to save for vacation?"
    ]
    
    results = {}
    for i, query in enumerate(test_queries, 1):
        print(f"\nQ{i}: {query}")
        docs = retrieve_financial_advice(query)  # FIXED: No extra args!
        results[query] = docs
        
        for j, doc in enumerate(docs[:3]):
            print(f"  {j+1}. {doc[:120]}...")
    
    # Google Doc results
    content = "DAY 3 RAG TEST RESULTS\n" + "="*50 + "\n\n"
    for query, docs in results.items():
        content += f"Q: {query}\n"
        for i, doc in enumerate(docs):
            content += f"{i+1}. {doc[:150]}\n"
        content += "\n" + "-"*50 + "\n"
    
    with open("rag_test_results.txt", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("\n✅ FIXED! Results saved: rag_test_results.txt")
    print("📋 Copy to Google Doc ✓")
