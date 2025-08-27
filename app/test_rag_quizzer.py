#!/usr/bin/env python3
"""
Test script to verify RAG quizzer database operations.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.rag_quizzer_server import RAGQuizzerServer
from database.user_server import UserServer

def test_rag_quizzer_operations():
    """Test RAG quizzer database operations."""
    print("🧪 Testing RAG Quizzer Operations")
    
    # Initialize servers
    rag_server = RAGQuizzerServer()
    user_server = UserServer()
    
    # Get all users
    users = user_server.list_users()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  - {user['username']} (ID: {user['id']}, Role: {user['role']})")
    
    # Test getting RAG quizzers for each teacher
    teachers = [user for user in users if user['role'] == 'teacher']
    print(f"\nFound {len(teachers)} teachers:")
    
    for teacher in teachers:
        print(f"\n📚 Testing teacher: {teacher['username']} (ID: {teacher['id']})")
        quizzers = rag_server.get_rag_quizzers_by_teacher(teacher['id'])
        print(f"  Found {len(quizzers)} RAG quizzers:")
        
        for quizzer in quizzers:
            print(f"    - {quizzer['name']} (ID: {quizzer['id']}, Collection: {quizzer['collection_id']})")
            print(f"      Slides: {quizzer['num_slides']}, Text: {quizzer['num_text_items']}, Images: {quizzer['num_image_items']}")
    
    # Test creating a sample RAG quizzer
    if teachers:
        teacher = teachers[0]
        print(f"\n➕ Creating test RAG quizzer for teacher {teacher['username']}...")
        
        test_data = {
            'teacher_id': teacher['id'],
            'name': 'Test Presentation',
            'collection_id': 'test_collection_123',
            'presentation_name': 'Test.pptx',
            'num_slides': 5,
            'num_text_items': 10,
            'num_image_items': 3,
            'slides': [
                {'slide_number': 1, 'content': ['Test slide 1']},
                {'slide_number': 2, 'content': ['Test slide 2']}
            ]
        }
        
        quizzer_id = rag_server.create_rag_quizzer(test_data)
        if quizzer_id:
            print(f"✅ Test RAG quizzer created with ID: {quizzer_id}")
            
            # Verify it was created
            quizzer = rag_server.get_rag_quizzer_by_id(quizzer_id)
            if quizzer:
                print(f"✅ Retrieved quizzer: {quizzer['name']}")
            else:
                print("❌ Failed to retrieve created quizzer")
        else:
            print("❌ Failed to create test RAG quizzer")

if __name__ == "__main__":
    test_rag_quizzer_operations()
