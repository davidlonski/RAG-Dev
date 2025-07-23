from pptx_rag_quizzer.rag_core import RAGCore
import random
from google.generativeai.types import GenerationConfig
import time
from PIL import Image
import io
import re


class RAGController:
    def __init__(self):
        self.rag_core = RAGCore()

    def build_collection(self, extracted_data, collection_name: str):
        if collection_name == "picture":
            self.rag_core.build_picture_collection(extracted_data)
        elif collection_name == "quiz":
            self.rag_core.build_quiz_collection(extracted_data)
        else:
            raise ValueError(f"Invalid collection name: {collection_name}")

    def query_collection(
        self, query_text: str, collection_name: str, n_results: int = 1
    ):
        """
        This function is used to get the context of collection.

        Args:
            query_text (str): The text to search for in the vector store.
            collection_name (str): The name of the collection to query.
            n_results (int): The number of results to return.

        Returns:
            str: The context of the retrieved documents.
        """
        if collection_name == "picture":
            retrieved_results = self.rag_core.picture_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "embeddings"],
            )
            relevant_passage = retrieved_results["documents"][0]
        elif collection_name == "quiz":
            retrieved_results = self.rag_core.quiz_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "embeddings"],
            )
            relevant_passage = retrieved_results["documents"][0]
        else:
            raise ValueError(f"Invalid collection name: {collection_name}")

        return relevant_passage

    def query_collection_multiple(
        self, query_text: str, collection_name: str, n_results: int = 3
    ):
        """
        This function is used to get multiple documents from the collection.
        """
        if collection_name == "picture":
            retrieved_results = self.rag_core.picture_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "embeddings"],
            )
        elif collection_name == "quiz":
            retrieved_results = self.rag_core.quiz_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                include=["documents", "metadatas", "embeddings"],
            )
        else:
            raise ValueError(f"Invalid collection name: {collection_name}")

        return retrieved_results

    def prompt_gemini(self, prompt: str, max_output_tokens: int = 200):
        """
        This function is used to prompt the Gemini model.
        It handles quota exhaustion and retries.

        Args:
            prompt (str): The prompt to use for the Gemini model.
            max_output_tokens (int): The maximum number of tokens to output.

        Returns:
            str: The response from the Gemini model.
        """
        max_retries = 3
        delay = 1
        quota_refill_delay = 60
        generation_config = GenerationConfig(max_output_tokens=max_output_tokens)
        for attempt in range(max_retries):
            try:
                response = self.rag_core.llm_model.generate_content(
                    contents=[prompt], generation_config=generation_config
                )
                return response.text
            except Exception as e:
                if "Resource has been exhausted" in str(e):
                    print(
                        f"Quota exhausted, waiting {quota_refill_delay} seconds for refill..."
                    )
                    time.sleep(quota_refill_delay)
                else:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    def prompt_gemini_with_image(
        self,
        prompt: str,
        image_bytes: bytes,
        image_format: str = "png",
        max_output_tokens: int = 200,
    ):
        """
        This function is used to prompt the Gemini model with an image.
        It handles quota exhaustion and retries.

        Args:
            prompt (str): The prompt to use for the Gemini model.
            image_bytes (bytes): The image to use for the Gemini model.
            image_format (str): The format of the image.
            max_output_tokens (int): The maximum number of tokens to output.

        Returns:
            str: The response from the Gemini model.
        """
        max_retries = 3
        delay = 1
        quota_refill_delay = 60
        generation_config = GenerationConfig(max_output_tokens=max_output_tokens)

        # Validate image format and convert if necessary
        try:

            # Open and validate the image
            img = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary (some formats like PNG with transparency cause issues)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            # Save as PNG to ensure compatibility
            img_buffer = io.BytesIO()
            img.save(img_buffer, format="PNG")
            img_buffer.seek(0)
            validated_image_bytes = img_buffer.getvalue()
            validated_format = "png"

        except Exception as e:
            print(f"Error validating image: {e}")
            # Use original image if validation fails
            validated_image_bytes = image_bytes
            validated_format = image_format

        for attempt in range(max_retries):
            try:
                image_part = {
                    "inline_data": {
                        "mime_type": f"image/{validated_format}",
                        "data": validated_image_bytes,
                    }
                }
                response = self.rag_core.llm_model.generate_content(
                    contents=[image_part, "\n", prompt],
                    generation_config=generation_config,
                )
                return response.text
            except Exception as e:
                if "Resource has been exhausted" in str(e):
                    print(
                        f"Quota exhausted, waiting {quota_refill_delay} seconds for refill..."
                    )
                    time.sleep(quota_refill_delay)
                else:
                    print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    def get_random_slide_context(self):
        """
        This function is used to get the context of a random slide.
        """
        collection_data = self.rag_core.quiz_collection.get()
        return random.choice(collection_data["documents"])

    def get_random_image_context(self):
        """
        This function is used to get the context of a random image.
        """
        max_attempts = 10  # Prevent infinite loop
        attempts = 0

        while attempts < max_attempts:
            try:
                collection_data = self.rag_core.quiz_collection.get()

                # Find items with image metadata
                image_items = []
                for i, item in enumerate(collection_data["metadatas"]):
                    if item.get("image_metadata") != "none":
                        image_items.append(i)

                if not image_items:
                    print("No images found in collection")
                    return None, None, None

                # Pick a random image
                random_index = random.choice(image_items)
                item = collection_data["metadatas"][random_index]
                image_metadata = item.get("image_metadata")

                # Extract extension
                ext_match = re.search(r"ext:([^,]+)", image_metadata)
                image_extension = ext_match.group(1) if ext_match else None

                # Extract bytes - this is base64 encoded
                bytes_match = re.search(r"bytes:([^,]+)", image_metadata)
                image_bytes_encoded = bytes_match.group(1) if bytes_match else None

                if image_extension and image_bytes_encoded:
                    try:
                        # Decode base64 bytes
                        import base64

                        image_bytes = base64.b64decode(image_bytes_encoded)
                        document = collection_data["documents"][random_index]
                        return image_extension, image_bytes, document
                    except Exception as e:
                        print(f"Failed to decode image bytes: {e}")
                        attempts += 1
                        continue
                else:
                    print(
                        f"Failed to extract image data from metadata: {image_metadata}"
                    )
                    attempts += 1
                    continue

            except Exception as e:
                print(f"Error getting random image context: {e}")
                attempts += 1
                time.sleep(1)  # Brief delay before retry

        print(f"Failed to get image context after {max_attempts} attempts")
        return None, None, None

    def get_context_from_slide_number(self, slide_number: int):
        """
        Get context from the picture collection using slide number.

        Args:
            slide_number (int): The slide number to search for

        Returns:
            str: Combined context from slides related to the slide number
        """
        if slide_number is None or slide_number == "":
            return ""

        collection_data = self.rag_core.picture_collection.get()

        context = []

        for i, metadata in enumerate(collection_data["metadatas"]):
            if metadata.get("slide_number") == slide_number:
                context.append(collection_data["documents"][i])

        context = "\n\n".join(context)

        return context
