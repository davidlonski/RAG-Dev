#!/usr/bin/env python3
"""
Test script to check ChromaDB collections and their contents.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pptx_rag_quizzer.rag_core import RAGCore
from database.rag_quizzer_server import RAGQuizzerServer

def test_chromadb_collections():
    """Test ChromaDB collections and their contents."""
    print("🧪 Testing ChromaDB Collections")
    
    # Initialize RAG core
    try:
        rag_core = RAGCore()
        print("✅ RAG Core initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize RAG Core: {e}")
        return
    
    # Get all collections
    try:
        collections = rag_core.chroma_client.list_collections()
        print(f"📚 Found {len(collections)} collections:")
        for collection in collections:
            print(f"  - {collection.name}")
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return
    
    # Get RAG quizzers from database
    rag_server = RAGQuizzerServer()
    quizzers = rag_server.get_rag_quizzers_by_teacher(1)  # Teacher ID 1
    
    print(f"\n📋 Found {len(quizzers)} RAG quizzers in database:")
    for quizzer in quizzers:
        print(f"  - {quizzer['name']} (Collection: {quizzer['collection_id']})")
        
        # Check if collection exists in ChromaDB
        try:
            collection = rag_core.chroma_client.get_collection(name=quizzer['collection_id'])
            collection_data = collection.get()
            print(f"    ✅ Collection exists with {len(collection_data['documents'])} documents")
            
            # Show first few documents
            for i, doc in enumerate(collection_data['documents'][:3]):
                print(f"      Doc {i+1}: {doc[:100]}...")
                
        except Exception as e:
            print(f"    ❌ Collection not found: {e}")

if __name__ == "__main__":
    test_chromadb_collections()
