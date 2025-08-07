"""
Async Pinecone-Relace Retriever for Agno Knowledge System

This module provides an async retriever function that integrates Pinecone vector search
with Relace embeddings and reranking, following the Agno pattern for custom retrievers.
Based on: https://github.com/agno-agi/agno/tree/main/cookbook/agent_concepts/knowledge/custom
"""

import asyncio
import os
from typing import List, Dict, Any, Optional

from agno.agent import Agent
from agno.document import Document
from agno.utils.log import logger
from agno.vectordb.pineconedb import PineconeDb
from embedder import RelaceEmbedder
from reranker import RelaceReranker


async def retriever(
    query: str,
    agent: Optional[Agent] = None,
    namespace: Optional[str] = None,
    rerank: bool = True,
    top_k_after_rerank: Optional[int] = None,
    **kwargs
) -> Optional[List[Document]]:
    """
    Async retriever function to search Pinecone with Relace embeddings and optional reranking.
    
    This retriever assumes the Pinecone index is already populated with documents using
    Relace embeddings. It performs a two-stage retrieval:
    1. Pinecone vector search using Relace embeddings
    2. Optional Relace reranking for improved relevance
    
    Args:
        query (str): The search query string
        agent (Optional[Agent]): The agent instance making the query
        namespace (Optional[str]): Pinecone namespace to search within
        rerank (bool): Whether to apply Relace reranking (default: True)
        top_k_after_rerank (Optional[int]): Number of documents to return after reranking
        num_documents (int): Number of documents to retrieve (default: 5)
        **kwargs: Additional keyword arguments
        
    Returns:
        Optional[List[Document]]: List of retrieved documents or None if search fails
    """
    try:
        # Environment setup
        pinecone_api_key = os.getenv("PINECONE_API_KEY")
        relace_api_key = os.getenv("RELACE_API_KEY")  
        pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "codebase-index")
        
        if not pinecone_api_key:
            logger.error("PINECONE_API_KEY environment variable is required")
            return None
            
        if not relace_api_key:
            logger.error("RELACE_API_KEY environment variable is required")
            return None
        
        # Get num_documents from kwargs or use default
        num_documents = kwargs.get('num_documents', 5)
        
        logger.info(f"Starting async retrieval for query: {query}")
        logger.info(f"Namespace: {namespace}, num_documents: {num_documents}, rerank: {rerank}")
        logger.info(f"DEBUG: Retriever function called with query: {query}")
        
        # Initialize Relace embedder
        embedder = RelaceEmbedder(api_key=relace_api_key)
        
        # Initialize Relace reranker
        reranker = RelaceReranker(
            api_key=relace_api_key,
            top_n=top_k_after_rerank or max(1, num_documents // 2)
        )
        
        # Initialize Pinecone vector database with Relace embedder and reranker
        vector_db = PineconeDb(
            name=pinecone_index_name,
            dimension=1024,  # Match Pinecone index dimensions
            metric="cosine", 
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
            api_key=pinecone_api_key,
            embedder=embedder,
            reranker=None,  # Disable reranker in PineconeDb, we'll handle it manually
        )
        
        try:
            # Search Pinecone vector database using query string
            # The PineconeDb will automatically use the Relace embedder to create embeddings
            logger.info(f"Searching Pinecone index: {pinecone_index_name}")
            logger.info(f"Using namespace: {namespace}")
            
            # Ensure namespace is properly passed
            search_kwargs = {
                "query": query,
                "limit": num_documents,
            }
            if namespace:
                search_kwargs["namespace"] = namespace
                
            query_response = vector_db.search(**search_kwargs)
            
            documents = []
            if query_response and isinstance(query_response, list) and len(query_response) > 0:
                logger.info(f"Found {len(query_response)} documents from Pinecone")
                
                for result in query_response:
                    if isinstance(result, Document):
                        # Set the name field from metadata for reranker compatibility
                        if result.meta_data and 'file_path' in result.meta_data:
                            result.name = result.meta_data['file_path']
                        # Fix content extraction - Pinecone stores content in metadata.content
                        if result.meta_data and 'content' in result.meta_data and not result.content:
                            result.content = result.meta_data['content']
                        # Add namespace info
                        result.meta_data = result.meta_data or {}
                        result.meta_data["namespace"] = namespace or "default"
                        documents.append(result)
                    else:
                        # Handle dict format if returned
                        metadata = result.get('metadata', {}) if isinstance(result, dict) else {}
                        
                        # Create document following Agno knowledge format
                        document = Document(
                            content=metadata.get('content', ''),  # Use 'content' field from metadata
                            id=result.get('id', '') if isinstance(result, dict) else str(result),
                            name=metadata.get('file_path', ''),
                            meta_data={
                                "file_path": metadata.get('file_path', ''),
                                "language": metadata.get('language', ''),
                                "function_name": metadata.get('function_name'),
                                "class_name": metadata.get('class_name'),
                                "repo_id": metadata.get('repo_id', ''),
                                "namespace": namespace or "default",
                                "pinecone_score": result.get('score', 0.0) if isinstance(result, dict) else 0.0,
                            }
                        )
                        documents.append(document)
                
                # Apply manual reranking if enabled
                if rerank and reranker and documents:
                    logger.info(f"Applying manual reranking to {len(documents)} documents")
                    try:
                        documents = await reranker.rerank_async(query=query, documents=documents)
                        logger.info(f"After reranking: {len(documents)} documents")
                    except Exception as e:
                        logger.error(f"Error during reranking: {e}")
                        # Continue with original documents if reranking fails
                
                # Convert documents to the format expected by Agno agent
                # The agent expects either strings or dictionaries, not Document objects
                formatted_documents = []
                for doc in documents:
                    # Create a dictionary format that the agent can process
                    doc_dict = {
                        "content": doc.content,
                        "id": doc.id,
                        "name": doc.name,
                        "metadata": doc.meta_data or {}
                    }
                    formatted_documents.append(doc_dict)
                
                # Return Documents directly, same format as Agno's PineconeDb.search()
                logger.info(f"DEBUG: Returning {len(formatted_documents)} documents from retriever")
                return formatted_documents
            else:
                logger.info(f"No documents found for query: {query}")
                return []
                
        finally:
            # Clean up embedder if needed
            if hasattr(embedder, 'close'):
                await embedder.close()
            
    except Exception as e:
        logger.error(f"Error during async retrieval: {e}")
        return None


async def amain():
    """Async main function to demonstrate agent usage."""
    # Initialize agent with custom retriever
    # Remember to set search_knowledge=True to use agentic_rag or add_reference=True for traditional RAG
    # search_knowledge=True is default when you add a knowledge base but is needed here
    agent = Agent(
        retriever=retriever,
        search_knowledge=True,
        instructions="Search the knowledge base for information",
        show_tool_calls=True,
    )

    # Example query
    query = "Find functions related to authentication"
    await agent.aprint_response(query, markdown=True)


def main():
    """Synchronous wrapper for main function"""
    asyncio.run(amain())


if __name__ == "__main__":
    main() 