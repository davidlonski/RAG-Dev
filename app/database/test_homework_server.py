from homework_server import HomeworkServer

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

def get_assignment(assignment_id):
    homework_server = HomeworkServer()
    assignment = homework_server.get_assignment(assignment_id, True, True)
    for v, k in assignment.items():
        if v == "questions":
            for q in k:
                for v2, k2 in q.items():
                    if v2 == "image_bytes":
                        print(f"🔍 {v2}: {k2}\n")
                    else:
                        print(f"🔍 {v2}: {k2}\n")
        else:
            print(f"🔍 {v}: {k}\n")

def list_assignments():
    homework_server = HomeworkServer()
    assignments = homework_server.list_assignments()
    for assignment in assignments:
        print(f"🔍 Assignment ID: {assignment['id']}")

def get_assignment_questions(assignment_id):
    homework_server = HomeworkServer()
    questions = homework_server.get_assignment_questions(assignment_id, True)
    for question in questions:
        print(f"🔍 Question ID: {question['id']}")
        
def update_assignment_status(assignment_id, status):
    homework_server = HomeworkServer()
    homework_server.update_assignment_status(assignment_id, status)
    print(f"🔍 Assignment Status Updated: {status}")

if __name__ == "__main__":
    update_assignment_status(20, "archived");
