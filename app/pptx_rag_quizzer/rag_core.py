import chromadb
from sentence_transformers import SentenceTransformer
import uuid
import random
import os
from dotenv import load_dotenv
import google.generativeai as genai
import google.generativeai.types as types
from google.generativeai.types import GenerationConfig
from chromadb.utils import embedding_functions
import torch

load_dotenv()

# Create ChromaDB directory if it doesn't exist
os.makedirs("./chroma_db", exist_ok=True)

# Global model cache
_embedding_model_cache = None
_llm_model_cache = None


def get_embedding_model():
    """Loads and caches the sentence-transformer model."""
    global _embedding_model_cache

    if _embedding_model_cache is None:
        try:
            print("Loading embedding model (first time)...")

            # Force CPU as target device to avoid meta tensor transfer issues
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

            # Ensure model weights are loaded out of meta tensors
            if any(p.device.type == "meta" for p in model.parameters()):
                print("Model has meta parameters, trying to re-initialize...")
                model = torch.nn.Module.to_empty(model)
                model = model.to("cpu")

            _embedding_model_cache = model
            print("Embedding model loaded successfully!")
            return model
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            print(
                "Will continue without embedding model - some features may be limited"
            )
            return None
    else:
        print("Using cached embedding model")

    return _embedding_model_cache


def get_llm_model():
    """
    Configures the Google Generative AI model using the GOOGLE_API_KEY environment variable.

    Returns:
        genai.GenerativeModel: The loaded LLM model.
    """
    global _llm_model_cache

    if _llm_model_cache is None:
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print(
                    "GOOGLE_API_KEY environment variable not found. Please set it in your .env file."
                )
                return False

            print("Loading LLM model (first time)...")
            genai.configure(api_key=api_key)
            _llm_model_cache = genai.GenerativeModel("gemini-2.0-flash-lite")
            print("LLM model loaded successfully!")
        except Exception as e:
            print(f"Error loading LLM model: {e}")
            return False
    else:
        print("Using cached LLM model")

    return _llm_model_cache


class RAGCore:
    """Handles the core Retrieval-Augmented Generation pipeline."""

    def __init__(self):
        """
        Initializes the RAGCore with extracted data.

        Args:
            data (list[dict]): The parsed content from the PowerPoint.
        """
        self.embedding_model = get_embedding_model()
        self.llm_model = get_llm_model()

        # Use persistent client instead of in-memory to avoid tenant issues
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")

        # Create embedding function for ChromaDB with proper device handling
        try:
            self.embedding_function = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            )
        except Exception as e:
            print(f"Error initializing embedding function: {e}")
            # Fallback to a simpler embedding function
            self.embedding_function = None

        self.picture_collection = None
        self.quiz_collection = None

    def build_picture_collection(self, data):
        """
        Builds the a vector database to retrieve data about images

        The chunks are joined by slide number and then embedded into the vector database.

        Returns:
            bool: True if the build was successful, False otherwise.
        """

        data = self.prepare_chunks_from_pptx_for_picture_collection(data)

        all_texts = []
        all_ids = []
        all_metadatas = []

        for chunk in data:
            all_texts.append(chunk["content"])
            all_metadatas.append({"slide_number": chunk["slide_number"]})
            all_ids.append(chunk["original_ids"])

        if not all_texts:
            print("No text content available to build the knowledge base.")
            return False

        # Creating and populating ChromaDB collection with embedding function
        collection_name = f"picture_rag_{uuid.uuid4().hex}"

        if self.embedding_function:
            self.picture_collection = self.chroma_client.create_collection(
                name=collection_name, embedding_function=self.embedding_function
            )
        else:
            # Fallback without embedding function
            self.picture_collection = self.chroma_client.create_collection(
                name=collection_name
            )

        # Adding documents (ChromaDB handles embedding automatically)
        self.picture_collection.add(
            documents=all_texts, metadatas=all_metadatas, ids=all_ids
        )

        return True

    def build_quiz_collection(self, data):
        """
        Builds the vector database from the text content.

        This method extracts text, creates embeddings, and populates the
        ChromaDB collection.

        Chunks are created from the text content and image descriptions.

        Returns:
            bool: True if the build was successful, False otherwise.
        """
        prepared_data = self.prepare_chunks_from_pptx_for_quiz_collection(data)

        all_texts = []
        all_ids = []
        all_metadatas = []
        all_image_metadata = []

        for chunk in prepared_data:
            all_texts.append(chunk["content"])
            metadata_list = chunk["metadata"]
            image_metadata_list = chunk.get("image_metadata", [])
            all_types = [item["type"] for item in metadata_list]

            # Combine image metadata into a single string for ChromaDB
            image_info = []
            for img_meta in image_metadata_list:
                image_info.append(
                    f"image_id:{img_meta['image_id']},ext:{img_meta['image_extension']},bytes:{img_meta['image_bytes']}"
                )

            combined_metadata = {
                "slide_number": metadata_list[0]["slide_number"],
                "types": ",".join(all_types),
                "id": metadata_list[0]["id"],
                "image_metadata": ",".join(image_info) if image_info else "none",
            }
            all_metadatas.append(combined_metadata)
            all_ids.append(metadata_list[0]["id"])

        if not all_texts:
            print("No text content available to build the knowledge base.")
            return False

        # Create and populate ChromaDB collection with embedding function
        collection_name = f"ppt_rag_{uuid.uuid4().hex}"

        if self.embedding_function:
            self.quiz_collection = self.chroma_client.create_collection(
                name=collection_name, embedding_function=self.embedding_function
            )
        else:
            # Fallback without embedding function
            self.quiz_collection = self.chroma_client.create_collection(
                name=collection_name
            )

        # Adding documents (ChromaDB handles embedding automatically)
        self.quiz_collection.add(
            documents=all_texts, metadatas=all_metadatas, ids=all_ids
        )
        return True

    def prepare_chunks_from_pptx_for_picture_collection(self, data):
        """
        Aggregates content from parsed PPTX data into meaningful chunks.
        Combines text per slide.
        """
        chunks = {}  # Dictionary to easily group by slide_number

        for item in data:
            slide_num = item["slide_number"]
            content_type = item["type"]
            text_content = item.get("content", "")

            # Initialize the chunk entry
            if slide_num not in chunks:
                chunks[slide_num] = {
                    "text_content": [],
                    "image_descriptions": [],
                    "ids": [],
                }

            if content_type == "text" and text_content:
                chunks[slide_num]["text_content"].append(text_content.strip())
            elif content_type == "image":
                image_part = {
                    "inline_data": {
                        "mime_type": f'image/{item["extension"]}',
                        "data": item["content"],
                    }
                }
                llm_response = self.llm_model.generate_content(
                    contents=[
                        image_part,
                        "\n",
                        "Describe the image max output tokens 100.",
                    ],
                    generation_config=GenerationConfig(max_output_tokens=100),
                )
                chunks[slide_num]["image_descriptions"].append(llm_response.text)

            chunks[slide_num]["ids"].append(item["id"])

        final_chunks = []
        for slide_num, val in chunks.items():
            combined_text = []
            if val["text_content"]:
                combined_text.append("\n".join(val["text_content"]))
            if val["image_descriptions"]:
                combined_text.append("\n".join(val["image_descriptions"]))

            full_chunk_text = "\n".join(combined_text).strip()

            if full_chunk_text:
                final_chunks.append(
                    {
                        "content": full_chunk_text,
                        "original_ids": ",".join(val["ids"]),
                        "slide_number": slide_num,
                    }
                )
        return final_chunks

    def prepare_chunks_from_pptx_for_quiz_collection(self, data):
        """
        Aggregates content from parsed PPTX data into meaningful chunks.
        Combines text and image descriptions per slide.
        """
        chunks = {}  # Dictionary to easily group by slide_number

        for item in data:
            slide_num = item["slide_number"]

            if item["type"] == "text":
                text_content = item["content"]
                image_metadata = None  # No image metadata for text items
            elif item["type"] == "image":
                text_content = item["description"]
                # Encode image bytes as base64 for storage
                import base64

                image_bytes_encoded = base64.b64encode(item["content"]).decode("utf-8")
                image_metadata = {
                    "image_bytes": image_bytes_encoded,
                    "image_extension": item["extension"],
                    "image_id": item["id"],
                }

            metadata = {
                "slide_number": slide_num,
                "type": item["type"],
                "id": item["id"],
            }

            # Initialize the chunk entry
            if slide_num not in chunks:
                chunks[slide_num] = {
                    "text_content": [],
                    "metadata": [],
                    "image_metadata": [],
                }

            chunks[slide_num]["text_content"].append(text_content.strip())
            chunks[slide_num]["metadata"].append(metadata)
            if image_metadata is not None:
                chunks[slide_num]["image_metadata"].append(image_metadata)

        final_chunks = []
        for slide_num, val in chunks.items():
            combined_text = []
            if val["text_content"]:
                combined_text.append("\n".join(val["text_content"]))

            metadata = val["metadata"]
            image_metadata = val["image_metadata"]

            full_chunk_text = "\n".join(combined_text).strip()
            if full_chunk_text:
                final_chunks.append(
                    {
                        "content": full_chunk_text,
                        "metadata": metadata,
                        "image_metadata": image_metadata,
                    }
                )
        return final_chunks
