"""
Custom Pinecone Retriever for Agno Knowledge System

This module provides a custom retriever function that integrates Pinecone vector search
with Agno's knowledge system, following the pattern from Agno documentation.
"""

import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional

import pinecone
import httpx

logger = logging.getLogger(__name__)


async def pinecone_retriever(
    query: str,
    agent=None,
    num_documents: int = 5,
    repo_namespace: Optional[str] = None,
    **kwargs
) -> Optional[List[Dict[str, Any]]]:
    """
    Custom retriever function to search the Pinecone vector database for relevant code documents.
    
    Args:
        query (str): The search query string
        agent: The agent instance making the query (unused but required by interface)
        num_documents (int): Number of documents to retrieve (default: 5)
        repo_namespace (str): Optional repository namespace to search in
        **kwargs: Additional keyword arguments
        
    Returns:
        Optional[List[Dict]]: List of retrieved documents or None if search fails
    """
    try:
        # Get API keys from environment variables
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "codebase-index-v2")
        relace_api_key = os.getenv("RELACE_API_KEY")
        relace_embeddings_url = os.getenv("RELACE_EMBEDDINGS_URL", "https://embeddings.endpoint.relace.run/v1/code/embed")
        
        if not pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        if not relace_api_key:
            raise ValueError("RELACE_API_KEY environment variable is required")
        
        # Initialize Pinecone
        pc = pinecone.Pinecone(api_key=pinecone_api_key)
        
        # Get the index
        if pinecone_index_name not in pc.list_indexes().names():
            raise ValueError(f"Pinecone index '{pinecone_index_name}' not found")
        
        index = pc.Index(pinecone_index_name)
        
        # Get embedding for the query using Relace
        async with httpx.AsyncClient() as client:
            response = await client.post(
                relace_embeddings_url,
                headers={
                    "Authorization": f"Bearer {relace_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "relace-embed-v1",
                    "input": [query]
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            data = response.json()
            if "results" not in data or len(data["results"]) == 0:
                raise ValueError("No embedding data in response")
            
            query_embedding = data["results"][0]["embedding"]
        
        # Search Pinecone
        if repo_namespace:
            # Search in specific namespace
            query_response = index.query(
                vector=query_embedding,
                top_k=num_documents,
                include_metadata=True,
                namespace=repo_namespace
            )
        else:
            # Search across all namespaces
            query_response = index.query(
                vector=query_embedding,
                top_k=num_documents,
                include_metadata=True
            )
        
        # Convert results to Agno knowledge format
        documents = []
        if hasattr(query_response, 'matches'):
            for match in query_response.matches:
                metadata = getattr(match, 'metadata', {}) or {}
                
                # Create document in Agno knowledge format
                document = {
                    "text": metadata.get('content', ''),
                    "score": getattr(match, 'score', 0.0),
                    "metadata": {
                        "id": getattr(match, 'id', ''),
                        "file_path": metadata.get('file_path', ''),
                        "language": metadata.get('language', ''),
                        "function_name": metadata.get('function_name'),
                        "class_name": metadata.get('class_name'),
                        "repo_id": metadata.get('repo_id', ''),
                        "namespace": repo_namespace or "all"
                    }
                }
                documents.append(document)
        
        logger.info(f"Retrieved {len(documents)} documents for query: {query}")
        return documents
        
    except Exception as e:
        logger.error(f"Error during Pinecone retrieval: {e}")
        return None


def create_pinecone_knowledge_base(
    repo_namespace: Optional[str] = None,
    top_k: int = 5
):
    """
    Factory function to create a Pinecone knowledge base retriever.
    
    Args:
        repo_namespace: Optional repository namespace to focus on
        top_k: Number of results to return
        
    Returns:
        Configured retriever function
    """
    def retriever(query: str, agent=None, num_documents: int = None, **kwargs):
        return asyncio.run(pinecone_retriever(
            query=query,
            agent=agent,
            num_documents=num_documents if num_documents is not None else top_k,
            repo_namespace=repo_namespace,
            **kwargs
        ))
    
    return retriever 