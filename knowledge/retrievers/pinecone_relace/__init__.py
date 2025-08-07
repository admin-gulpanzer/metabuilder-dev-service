"""
Pinecone-Relace Retrievers Package

This package provides sync and async retriever functions that integrate Pinecone vector search
with Relace embeddings and reranking, following the Agno pattern for custom retrievers.
"""

from .retriever import retriever as sync_retriever
from .async_retriever import retriever as async_retriever

__all__ = [
    "sync_retriever",
    "async_retriever",
] 