"""
ChromaDB HTTP Client
Pure HTTP client that makes REST API calls to the ChromaDB API service.
No ChromaDB Python client dependencies required - only uses requests library.
Perfect for the main app VM that should not have heavy ML dependencies.
"""

import requests
import json
import uuid
import random
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional, Any

load_dotenv()


class ChromaDBHTTPClient:
    """
    Pure HTTP-based ChromaDB client.
    Makes REST API calls to the ChromaDB API service without requiring ChromaDB Python client.
    This allows the main app to run without heavy ML dependencies like torch, sentence-transformers, etc.
    """
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the ChromaDB HTTP client.
        
        Args:
            api_url: ChromaDB API service URL (overrides environment variable)
        """
        self.api_url = api_url or os.getenv("CHROMA_API_URL", "http://localhost:8001")
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        print(f"✅ ChromaDB HTTP client initialized for {self.api_url}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make a request to the ChromaDB API service.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            data: Request data for POST requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If the request fails
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
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
        Check if the ChromaDB API service is healthy.
        
        Returns:
            True if API service is responding
        """
        try:
            result = self._make_request("GET", "health")
            if result.get("status") == "healthy":
                print(f"✅ ChromaDB API service health check passed ({self.api_url})")
                return True
            else:
                print(f"❌ ChromaDB API service unhealthy: {result}")
                return False
        except Exception as e:
            print(f"❌ ChromaDB API service health check failed: {e}")
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
            "metadata": {"description": f"Collection for {collection_name}"}
        }
        
        try:
            result = self._make_request("POST", "collections", data)
            if result.get("success"):
                print(f"✅ Collection '{collection_name}' created successfully")
                return result.get("collection", {})
            else:
                raise Exception(result.get("message", "Unknown error"))
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
            result = self._make_request("DELETE", f"collections/{collection_name}")
            if result.get("success"):
                print(f"✅ Collection '{collection_name}' deleted successfully")
                return True
            else:
                raise Exception(result.get("message", "Unknown error"))
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
            result = self._make_request("POST", f"collections/{collection_name}/add", data)
            if result.get("success"):
                print(f"✅ Added {len(documents)} documents to collection '{collection_name}'")
                return result
            else:
                raise Exception(result.get("message", "Unknown error"))
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
            result = self._make_request("POST", f"collections/{collection_name}/query", data)
            if result.get("success"):
                return result.get("results", {})
            else:
                raise Exception(result.get("message", "Unknown error"))
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
            result = self._make_request("POST", f"collections/{collection_name}/get", data)
            if result.get("success"):
                return result.get("data", {})
            else:
                raise Exception(result.get("message", "Unknown error"))
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
            result = self._make_request("GET", "collections")
            if result.get("success"):
                return result.get("collections", [])
            else:
                raise Exception(result.get("message", "Unknown error"))
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
            result = self._make_request("GET", f"collections/{collection_name}/exists")
            if result.get("success"):
                return result.get("exists", False)
            else:
                raise Exception(result.get("message", "Unknown error"))
        except Exception as e:
            print(f"❌ Failed to check if collection exists: {e}")
            return False


# Global cache for the HTTP client
_chroma_http_client_cache = None


def get_chroma_http_client(api_url: Optional[str] = None) -> ChromaDBHTTPClient:
    """
    Get a singleton instance of the ChromaDB HTTP client.
    
    Args:
        api_url: ChromaDB API service URL (for production environments)
    
    Returns:
        ChromaDBHTTPClient instance
    """
    global _chroma_http_client_cache
    
    # Create new instance if api_url is provided (for production)
    if api_url is not None:
        return ChromaDBHTTPClient(api_url=api_url)
    
    # Use cached instance for default configuration
    if _chroma_http_client_cache is None:
        _chroma_http_client_cache = ChromaDBHTTPClient()
    
    return _chroma_http_client_cache
