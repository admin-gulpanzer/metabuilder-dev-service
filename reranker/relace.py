from typing import Any, Dict, List, Optional

from agno.document import Document
from agno.reranker.base import Reranker
from agno.utils.log import logger

from clients import RelaceClient


class RelaceReranker(Reranker):
    """Relace reranker for reranking documents using Relace.ai API"""
    
    model: str = "relace-rerank-v1"
    api_key: Optional[str] = None
    top_n: Optional[int] = None
    token_limit: int = 150000
    client_params: Optional[Dict[str, Any]] = None
    relace_client: Optional[RelaceClient] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def client(self) -> RelaceClient:
        """Get or create RelaceClient instance"""
        if self.relace_client:
            return self.relace_client
        
        client_params: Dict[str, Any] = {
            "api_key": self.api_key,
        }
        
        if self.client_params:
            client_params.update(self.client_params)
            
        self.relace_client = RelaceClient(**client_params)
        return self.relace_client

    async def close(self):
        """Close the client session"""
        if self.relace_client:
            await self.relace_client.close()

    async def _rerank_async(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents using Relace API asynchronously"""
        # Validate input documents and top_n
        if not documents:
            return []

        top_n = self.top_n
        if top_n and not (0 < top_n):
            logger.warning(f"top_n should be a positive integer, got {self.top_n}, setting top_n to None")
            top_n = None

        try:
            # Convert documents to codebase format expected by Relace
            codebase = []
            for i, doc in enumerate(documents):
                codebase.append({
                    "filename": doc.name or f"doc_{i}.txt",
                    "code": doc.content
                })
            
            # Use the centralized client to rank code files
            results_list = await self.client.rank_code_files(
                query=query,
                codebase=codebase,
                token_limit=self.token_limit
            )
            
            # Process the response
            compressed_docs: List[Document] = []
            
            # Map results back to documents
            filename_to_doc = {}
            for i, doc in enumerate(documents):
                filename = doc.name or f"doc_{i}.txt"
                filename_to_doc[filename] = doc
            
            for item in results_list:
                if isinstance(item, dict) and "filename" in item and "score" in item:
                    filename = item["filename"]
                    score = item["score"]
                    
                    if filename in filename_to_doc:
                        doc = filename_to_doc[filename]
                        doc.reranking_score = score
                        compressed_docs.append(doc)
            
            # Order by relevance score
            compressed_docs.sort(
                key=lambda x: x.reranking_score if x.reranking_score is not None else float("-inf"),
                reverse=True,
            )
            
            # Limit to top_n if specified
            if top_n:
                compressed_docs = compressed_docs[:top_n]
            
            return compressed_docs
                    
        except Exception as e:
            logger.error(f"Error reranking documents: {e}")
            return documents

    def _rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents using Relace API synchronously"""
        try:
            # Convert documents to codebase format expected by Relace
            codebase = []
            for i, doc in enumerate(documents):
                codebase.append({
                    "filename": doc.name or f"doc_{i}.txt",
                    "code": doc.content
                })
            
            # Use the centralized client to rank code files
            results_list = self.client.rank_code_files_sync(
                query=query,
                codebase=codebase,
                token_limit=self.token_limit
            )
            
            # Process the response
            compressed_docs: List[Document] = []
            
            # Map results back to documents
            filename_to_doc = {}
            for i, doc in enumerate(documents):
                filename = doc.name or f"doc_{i}.txt"
                filename_to_doc[filename] = doc
            
            for item in results_list:
                if isinstance(item, dict) and "filename" in item and "score" in item:
                    filename = item["filename"]
                    score = item["score"]
                    
                    if filename in filename_to_doc:
                        doc = filename_to_doc[filename]
                        doc.reranking_score = score
                        compressed_docs.append(doc)
            
            # Order by relevance score
            compressed_docs.sort(
                key=lambda x: x.reranking_score if x.reranking_score is not None else float("-inf"),
                reverse=True,
            )
            
            # Limit to top_n if specified
            top_n = self.top_n
            if top_n and (0 < top_n):
                compressed_docs = compressed_docs[:top_n]
            
            return compressed_docs
            
        except Exception as e:
            logger.error(f"Error reranking documents: {e}")
            return documents

    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents and return the reranked list"""
        try:
            return self._rerank(query=query, documents=documents)
        except Exception as e:
            logger.error(f"Error reranking documents: {e}. Returning original documents")
            return documents

    async def rerank_async(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents asynchronously and return the reranked list"""
        try:
            return await self._rerank_async(query=query, documents=documents)
        except Exception as e:
            logger.error(f"Error reranking documents: {e}. Returning original documents")
            return documents 