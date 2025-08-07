"""
Semantic Search Tool for searching code repositories using Pinecone and Relace embeddings.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
import os

import pinecone
import httpx

from agno.tools import Toolkit

logger = logging.getLogger(__name__)


class SemanticSearchTools(Toolkit):
    """Toolkit for semantic search through code repositories"""
    
    def __init__(self, **kwargs):
        # Get API keys from environment variables
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "codebase-index-v2")
        
        self.relace_api_key = os.getenv("RELACE_API_KEY")
        self.relace_embeddings_url = os.getenv("RELACE_EMBEDDINGS_URL", "https://embeddings.endpoint.relace.run/v1/code/embed")
        
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        if not self.relace_api_key:
            raise ValueError("RELACE_API_KEY environment variable is required")
        
        # Initialize Pinecone
        self.pc = pinecone.Pinecone(api_key=self.pinecone_api_key)
        self.index = self._get_or_create_index()
        
        # Relace headers
        self.relace_headers = {
            "Authorization": f"Bearer {self.relace_api_key}",
            "Content-Type": "application/json"
        }
        
        # Create tools list
        tools = [
            self.search_code,
            self.list_repositories,
            self.get_repository_stats,
        ]
        
        super().__init__(name="semantic_search_tools", tools=tools, **kwargs)
    
    def _get_or_create_index(self):
        """Get existing index or create a new one."""
        try:
            # Check if index exists
            if self.pinecone_index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {self.pinecone_index_name}")
                
                self.pc.create_index(
                    name=self.pinecone_index_name,
                    dimension=1024,  # Standard dimension for Relace embeddings
                    metric="cosine",
                    metadata_config={
                        "indexed": [
                            "repo_id", 
                            "file_path", 
                            "language", 
                            "function_name",
                            "class_name"
                        ]
                    }
                )
                
                # Wait for index to be ready
                import time
                time.sleep(10)
            
            return self.pc.Index(self.pinecone_index_name)
            
        except Exception as e:
            logger.error(f"Error getting/creating Pinecone index: {e}")
            raise
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Relace.ai."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.relace_embeddings_url,
                    headers=self.relace_headers,
                    json={
                        "model": "relace-embed-v1",
                        "input": [text]
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                if "results" in data and len(data["results"]) > 0:
                    return data["results"][0]["embedding"]
                else:
                    raise ValueError("No embedding data in response")
                    
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise
    
    def search_code(self, query: str, repo_name: Optional[str] = None, top_k: int = 10, file_type: Optional[str] = None) -> str:
        """
        Search for code using semantic similarity.
        
        Args:
            query: The search query
            repo_name: Optional repository name to search in
            top_k: Number of results to return
            file_type: Optional file type filter (e.g., "python", "javascript")
            
        Returns:
            JSON string with search results
        """
        try:
            # Get embedding for the query
            query_embedding = asyncio.run(self._get_embedding(query))
            
            # Build filter dictionary
            filter_dict = {}
            if repo_name:
                filter_dict["repo_id"] = {"$eq": repo_name}
            if file_type:
                filter_dict["language"] = {"$eq": file_type}
            
            # Search Pinecone
            if repo_name:
                # Search in specific namespace
                query_response = self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None,
                    namespace=repo_name
                )
            else:
                # Search across all namespaces
                query_response = self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None
                )
            
            # Convert results to serializable format
            results = []
            for match in query_response.matches:
                metadata = match.metadata or {}
                result = {
                    "id": match.id,
                    "score": match.score,
                    "content": metadata.get('content', ''),
                    "file_path": metadata.get('file_path', ''),
                    "language": metadata.get('language', ''),
                    "function_name": metadata.get('function_name'),
                    "class_name": metadata.get('class_name')
                }
                results.append(result)
            
            return json.dumps({
                "query": query,
                "repo_name": repo_name,
                "results": results,
                "total_results": len(results)
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Search failed: {str(e)}",
                "query": query,
                "repo_name": repo_name
            })
    
    def list_repositories(self) -> str:
        """
        List all available repository namespaces.
        
        Returns:
            JSON string with list of repository namespaces
        """
        try:
            stats = self.index.describe_index_stats()
            namespaces = list(stats.namespaces.keys())
            
            return json.dumps({
                "repositories": namespaces,
                "total_repositories": len(namespaces)
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to list repositories: {str(e)}"
            })
    
    def get_repository_stats(self, repo_name: str) -> str:
        """
        Get statistics for a specific repository namespace.
        
        Args:
            repo_name: The repository namespace to get stats for
            
        Returns:
            JSON string with repository statistics
        """
        try:
            stats = self.index.describe_index_stats()
            namespace_stats = stats.namespaces.get(repo_name, {})
            
            return json.dumps({
                "namespace": repo_name,
                "statistics": {
                    "vector_count": namespace_stats.get("vector_count", 0),
                    "dimension": stats.dimension,
                    "index_fullness": stats.index_fullness,
                    "total_vector_count": stats.total_vector_count
                }
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "error": f"Failed to get repository stats: {str(e)}",
                "namespace": repo_name
            }) 