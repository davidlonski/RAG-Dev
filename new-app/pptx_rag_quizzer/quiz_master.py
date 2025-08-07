import re
import time
import base64
from pptx_rag_quizzer.image_server import ImageServer
from pptx_rag_quizzer.rag_core import RAGCore

class QuizMaster:
    """Manages the quiz logic, including question generation and grading for both text and image content."""

    image_server = ImageServer()

    def __init__(self, rag_core: RAGCore):
        """
        Initializes the QuizMaster.

        Args:
            rag_controller (RAGController): An instance of the RAGController to get context from.
        """
        self.rag_core = rag_core

    def generate_text_question(self, collection_id: str):
        """
        Generates a text-based short answer question based on a random context from the document.

        Returns:
            dict or None: A dictionary containing the question, answer, and context,
                          or None if generation fails.

        Example:
        {
            "question": "What is the capital of France?",
            "answer": "Paris",
            "context": "The capital of France is Paris.",
            "type": "text"
        }
        """
        try:
            # Get text content from the collection
            text_context = self.rag_core.get_random_slide_context(collection_id)

            if isinstance(text_context, dict):
                text_context = text_context["documents"]

            if text_context is None:
                print("No text context available")
                return None

            # Generate short answer question using the context
            question_prompt = f"""
            Based on this content: "{text_context}"
            
            Write ONE open-ended, short answer question that tests understanding of a key concept in the text.
            Also provide the correct answer (1-2 sentences) based only on the text. Respond in this exact JSON format:
            {{
                "question": "Your short answer question here",
                "answer": "The correct answer here."
            }}
            """

            response = self.rag_core.prompt_gemini(question_prompt)

            # Regex to extract the question and answer
            question_match = re.search(r'"question":\s*"([^"]+)"', response)
            answer_match = re.search(r'"answer":\s*"([^"]+)"', response)

            if question_match and answer_match:
                question = question_match.group(1)
                answer = answer_match.group(1)
                question_data = {
                    "question": question,
                    "answer": answer,
                    "context": text_context,
                    "type": "text",
                }
                return question_data
            else:
                print(f"Error extracting question and answer from response: {response}")
                return None

        except Exception as e:
            print(f"Error generating text question: {e}")
            return None

    def generate_image_question(self, collection_id: str):
        """
        Generates an image-based short answer question based on a random context from the document.

        Returns:
            dict or None: A dictionary containing the question, answer, context, type, image_extension, and image_bytes,
                          or None if generation fails.

        Example:
        {
            "question": "What is the capital of France?",
            "answer": "Paris",
            "context": "The capital of France is Paris.",
            "type": "image",
            "image_extension": "png",
            "image_bytes": "base64_encoded_image_bytes"
        }
        """
        try:
            chunk = self.rag_core.get_random_slide_with_image(collection_id)
            if isinstance(chunk, dict):
                context = chunk["documents"]
                metadata = chunk["metadatas"]
            else:
                print("No image context available")
                return None
            
            image_id = None
            image_extension = None
            for key, value in metadata.items():
                if key.endswith("image_id"):
                    image_id = value
                if key.endswith("image_extension"):
                    image_extension = value
            
            if image_id is not None:
                image_bytes = self.image_server.get_image(image_id)
                if image_bytes and len(image_bytes) > 0:
                    image_bytes = image_bytes[0]
                else:
                    print("No image bytes found")
                    return None
            else:
                print("No image id found")
                return None

            question_prompt = f"""
            Based on this image:
            
            Write ONE open-ended, short answer question that tests understanding of a key concept in the image.
            Also provide the correct answer (1-2 sentences) based only on the image. Respond in this exact JSON format:
            
            You may use the following context to help you generate the question:
            {context}

            Remember, the question should be based on the image and the context may only be used if it directly clarifies or adds significant understanding to the image's visual elements. Do not include context that merely repeats what's obvious in the image or is irrelevant.
            
            {{
                "question": "Your short answer question here",
                "answer": "The correct answer here."
            }}
            """

            response = self.rag_core.prompt_gemini_with_image(
                question_prompt, image_bytes, image_extension
            )

            question_match = re.search(r'"question":\s*"([^"]+)"', response)
            answer_match = re.search(r'"answer":\s*"([^"]+)"', response)

            if question_match and answer_match:
                question = question_match.group(1)
                answer = answer_match.group(1)

                image_bytes_encoded = base64.b64encode(image_bytes).decode("utf-8")

                question_data = {
                    "question": question,
                    "answer": answer,
                    "context": context,
                    "type": "image",
                    "image_extension": image_extension,
                    "image_bytes": image_bytes_encoded,
                }
                return question_data
            else:
                print(f"Error extracting question and answer from response: {response}")
                return None

        except Exception as e:
            print(f"Error generating image question: {e}")
            return None
