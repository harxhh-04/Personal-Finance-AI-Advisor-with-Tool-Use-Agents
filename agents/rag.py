
"""
RAG Document Loader + Vector Store
"""
import os
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb

def load_documents():
    """Load all PDFs from data/rag_docs/ → chunks."""
    docs_path = Path("data/rag_docs")
    if not docs_path.exists():
        print("📁 Create data/rag_docs/ folder first!")
        return []
    
    documents = []
    for pdf_file in docs_path.glob("*.pdf"):
        print(f"📄 Loading {pdf_file.name}")
        loader = PyPDFLoader(str(pdf_file))
        docs = loader.load()
        documents.extend(docs)
    
    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ Loaded {len(chunks)} chunks from {len(documents)} docs")
    return chunks

def create_vectorstore(chunks):
    """FAISS vector store with local embeddings."""
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("faiss_index")
    print("💾 Vectorstore saved: faiss_index/")
    return vectorstore

def test_retrieval(vectorstore, query="budgeting"):
    """Test RAG retrieval."""
    docs = vectorstore.similarity_search(query, k=3)
    print(f"\n🔍 Query: '{query}'")
    for i, doc in enumerate(docs, 1):
        print(f"{i}. {doc.page_content[:200]}...")
    return docs

if __name__ == "__main__":
    # MAIN TEST
    print("🚀 RAG Pipeline Test")
    chunks = load_documents()
    
    if chunks:
        print("\n📝 First 3 chunks:")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n{i+1}. {chunk.page_content[:150]}...")
        
        # Create & test vectorstore
        vectorstore = create_vectorstore(chunks)
        test_retrieval(vectorstore, "budget")
        test_retrieval(vectorstore, "emergency")
    else:
        print("❌ No documents found - add PDFs to data/rag_docs/")
