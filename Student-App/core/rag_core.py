
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

_llm_model_cache = None

def get_llm_model():
    """
    Configures the Google Generative AI model using the GOOGLE_API_KEY environment variable.

    Returns:
        genai.GenerativeModel: The loaded LLM model.
    """

    load_dotenv()
    
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
    def __init__(self):
        self.collection = None
        self.llm_model = get_llm_model()
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
    def get_collection(self, collection_id):
        self.collection = self.chroma_client.get_collection(collection_id)
        return self.collection
