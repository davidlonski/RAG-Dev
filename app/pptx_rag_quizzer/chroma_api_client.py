"""
ChromaDB API Client
Pure HTTP-based client that makes REST API calls to ChromaDB server.
No ChromaDB Python client dependencies required - only uses requests library.
Perfect for separating ChromaDB dependencies from the main application.
"""

import requests
import json
import uuid
import random
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

load_dotenv()


class ChromaDBAPIClient:
    """
    Pure HTTP-based ChromaDB client.
    Makes REST API calls to ChromaDB server without requiring ChromaDB Python client.
    This allows the main app to run without heavy ML dependencies like torch, sentence-transformers, etc.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize the ChromaDB API client.
        
        Args:
            host: ChromaDB server host (overrides environment variable)
            port: ChromaDB server port (overrides environment variable)
        """
        self.host = host or os.getenv("CHROMA_SERVER_HOST", "localhost")
        self.port = int(port or os.getenv("CHROMA_SERVER_HTTP_PORT", "8000"))
        self.base_url = f"http://{self.host}:{self.port}"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        print(f"✅ ChromaDB API client initialized for {self.host}:{self.port}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the ChromaDB API.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            data: Request data for POST requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"ChromaDB API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            raise Exception(f"ChromaDB API request failed: {str(e)}")
    
    def health_check(self) -> bool:
        """
        Check if the ChromaDB API is healthy.
        
        Returns:
            True if API is responding
        """
        try:
            # Try to list collections as health check
            self._make_request("GET", "api/v1/collections")
            print(f"✅ ChromaDB API health check passed ({self.host}:{self.port})")
            return True
        except Exception as e:
            print(f"❌ ChromaDB API health check failed: {e}")
            return False
    
    def create_collection(self, collection_name: str) -> Dict:
        """
        Create a new collection in ChromaDB.
        
        Args:
            collection_name: Name of the collection to create
            
        Returns:
            Collection information
        """
        data = {
            "name": collection_name,
            "metadata": {}
        }
        
        try:
            result = self._make_request("POST", "api/v1/collections", data)
            print(f"✅ Collection '{collection_name}' created successfully")
            return result
        except Exception as e:
            print(f"❌ Failed to create collection '{collection_name}': {e}")
            raise
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection from ChromaDB.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if successful
        """
        try:
            self._make_request("DELETE", f"api/v1/collections/{collection_name}")
            print(f"✅ Collection '{collection_name}' deleted successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to delete collection '{collection_name}': {e}")
            raise
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: List[Dict], ids: List[str]) -> Dict:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of document IDs
            
        Returns:
            Result of the add operation
        """
        data = {
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }
        
        try:
            result = self._make_request("POST", f"api/v1/collections/{collection_name}/add", data)
            print(f"✅ Added {len(documents)} documents to collection '{collection_name}'")
            return result
        except Exception as e:
            print(f"❌ Failed to add documents to collection '{collection_name}': {e}")
            raise
    
    def query_collection(self, collection_name: str, query_texts: List[str], 
                        n_results: int = 1, include: List[str] = None) -> Dict:
        """
        Query a collection for similar documents.
        
        Args:
            collection_name: Name of the collection
            query_texts: List of query texts
            n_results: Number of results to return
            include: What to include in results (documents, metadatas, embeddings)
            
        Returns:
            Query results
        """
        if include is None:
            include = ["documents", "metadatas", "embeddings"]
        
        data = {
            "query_texts": query_texts,
            "n_results": n_results,
            "include": include
        }
        
        try:
            result = self._make_request("POST", f"api/v1/collections/{collection_name}/query", data)
            return result
        except Exception as e:
            print(f"❌ Failed to query collection '{collection_name}': {e}")
            raise
    
    def get_collection_data(self, collection_name: str, include: List[str] = None) -> Dict:
        """
        Get all documents from a collection.
        
        Args:
            collection_name: Name of the collection
            include: What to include in results
            
        Returns:
            Collection data
        """
        if include is None:
            include = ["documents", "metadatas", "embeddings"]
        
        data = {
            "include": include
        }
        
        try:
            result = self._make_request("POST", f"api/v1/collections/{collection_name}/get", data)
            return result
        except Exception as e:
            print(f"❌ Failed to get collection data '{collection_name}': {e}")
            raise
    
    def get_collections(self) -> List[Dict]:
        """
        Get list of all collections.
        
        Returns:
            List of collection information
        """
        try:
            result = self._make_request("GET", "api/v1/collections")
            return result.get("data", [])
        except Exception as e:
            print(f"❌ Failed to get collections: {e}")
            raise
    
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            collection_name: Name of the collection to check
            
        Returns:
            True if collection exists
        """
        try:
            collections = self.get_collections()
            collection_names = [col.get("name", "") for col in collections]
            return collection_name in collection_names
        except Exception as e:
            print(f"❌ Failed to check if collection exists: {e}")
            return False


# Global cache for the API client
_chroma_api_client_cache = None


def get_chroma_api_client(host: Optional[str] = None, port: Optional[int] = None) -> ChromaDBAPIClient:
    """
    Get a singleton instance of the ChromaDB API client.
    
    Args:
        host: ChromaDB server host (for production environments)
        port: ChromaDB server port (for production environments)
    
    Returns:
        ChromaDBAPIClient instance
    """
    global _chroma_api_client_cache
    
    # Create new instance if host/port are provided (for production)
    if host is not None or port is not None:
        return ChromaDBAPIClient(host=host, port=port)
    
    # Use cached instance for default configuration
    if _chroma_api_client_cache is None:
        _chroma_api_client_cache = ChromaDBAPIClient()
    
    return _chroma_api_client_cache
