from database.homework_server import HomeworkServer

def test_create_assignment():
    homework_server = HomeworkServer()
    assignment = {
        "name": "Test Assignment",
        "collection_id": "test_collection_id",
        "status": "active",
        "questions": [
            {
                "question": "What is the capital of France?",
                "answer": "Paris",
                "context": "France is a country in Europe.",
                "type": "text",
            }
        ],
        "num_text_questions": 1,
        "num_image_questions": 0,
    }

    assignment_id = homework_server.create_assignment(assignment)
    
    print(f"🔍 Assignment ID: {assignment_id}")

if __name__ == "__main__":
    test_create_assignment()

