
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from agno.embedder.base import Embedder
from agno.utils.log import logger
from clients import RelaceClient


@dataclass
class RelaceEmbedder(Embedder):
    """Relace embedder for generating embeddings using Relace.ai API"""
    
    id: str = "relace-embed-v1"
    api_key: Optional[str] = None
    request_params: Optional[Dict[str, Any]] = None
    client_params: Optional[Dict[str, Any]] = None
    relace_client: Optional[RelaceClient] = None
    dimensions: Optional[int] = 1024

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

    def response(self, text: str) -> Dict[str, Any]:
        """Get embedding response from Relace API - sync version for compatibility"""
        return self.client.generate_embeddings_sync(
            texts=[text],
            model=self.id,
            request_params=self.request_params
        )

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text synchronously"""
        try:
            response = self.response(text=text)
            
            # Extract embedding from response - Relace API uses "results" key
            if "results" in response and len(response["results"]) > 0:
                return response["results"][0]["embedding"]
            elif "data" in response and len(response["data"]) > 0:
                # Fallback for different response format
                return response["data"][0]["embedding"]
            else:
                logger.warning("No embeddings found in response")
                return []
                
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []

    def get_embedding_and_usage(self, text: str) -> Tuple[List[float], Optional[Dict[str, Any]]]:
        """Get embedding and usage information for text"""
        try:
            response = self.response(text=text)
            
            # Extract embedding and usage from response - Relace API uses "results" key
            embedding: List[float] = []
            usage: Optional[Dict[str, Any]] = None
            
            if "results" in response and len(response["results"]) > 0:
                embedding = response["results"][0]["embedding"]
            elif "data" in response and len(response["data"]) > 0:
                # Fallback for different response format
                embedding = response["data"][0]["embedding"]
            
            if "usage" in response:
                usage = response["usage"]
            
            return embedding, usage
            
        except Exception as e:
            logger.error(f"Error getting embedding and usage: {e}")
            return [], None

    async def get_embedding_async(self, text: str) -> List[float]:
        """Get embedding for text asynchronously"""
        try:
            response = await self.client.generate_embeddings(
                texts=[text],
                model=self.id,
                request_params=self.request_params
            )
            
            # Extract embedding from response - Relace API uses "results" key
            if "results" in response and len(response["results"]) > 0:
                return response["results"][0]["embedding"]
            elif "data" in response and len(response["data"]) > 0:
                # Fallback for different response format
                return response["data"][0]["embedding"]
            else:
                logger.warning("No embeddings found in response")
                return []
                
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return []

    async def get_embedding_and_usage_async(self, text: str) -> Tuple[List[float], Optional[Dict[str, Any]]]:
        """Get embedding and usage information for text asynchronously"""
        try:
            response = await self.client.generate_embeddings(
                texts=[text],
                model=self.id,
                request_params=self.request_params
            )
            
            # Extract embedding and usage from response - Relace API uses "results" key
            embedding: List[float] = []
            usage: Optional[Dict[str, Any]] = None
            
            if "results" in response and len(response["results"]) > 0:
                embedding = response["results"][0]["embedding"]
            elif "data" in response and len(response["data"]) > 0:
                # Fallback for different response format
                embedding = response["data"][0]["embedding"]
            
            if "usage" in response:
                usage = response["usage"]
            
            return embedding, usage
            
        except Exception as e:
            logger.error(f"Error getting embedding and usage: {e}")
            return [], None 