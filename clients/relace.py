"""
Relace.ai client for agent-api
"""

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from loguru import logger


class RelaceClient:
    """Client for Relace.ai API services"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 embeddings_url: str = "https://embeddings.endpoint.relace.run/v1/code/embed",
                 reranker_url: str = "https://ranker.endpoint.relace.run/v2/code/rank",
                 session: Optional[aiohttp.ClientSession] = None):
        self.api_key = api_key
        self.embeddings_url = embeddings_url
        self.reranker_url = reranker_url
        self.session = session
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def generate_embeddings(self, 
                                 texts: List[str],
                                 model: str = "relace-embed-v1",
                                 request_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate embeddings using Relace Embeddings API"""
        try:
            session = await self._get_session()
            
            payload = {
                "model": model,
                "input": texts
            }
            
            if request_params:
                payload.update(request_params)
            
            async with session.post(self.embeddings_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Generated embeddings for {len(texts)} texts")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Embedding generation failed: {error_text}")
                    raise Exception(f"Relace API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def rank_code_files(self,
                             query: str,
                             codebase: List[Dict[str, str]],
                             token_limit: int = 150000) -> List[Dict[str, Any]]:
        """Rank code files by relevance using Relace Code Reranker"""
        try:
            session = await self._get_session()
            
            # Ensure codebase is not empty to avoid null length errors
            if not codebase:
                logger.warning("Empty codebase provided for ranking")
                return []
            
            payload = {
                "query": query,
                "codebase": codebase,
                "token_limit": token_limit
            }
            
            async with session.post(self.reranker_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"Ranked {len(codebase)} files by relevance")
                    
                    # Handle the actual Relace API response structure
                    if isinstance(result, dict) and "results" in result:
                        # Results are wrapped in a dict with 'results' key
                        results_list = result["results"]
                        if isinstance(results_list, list):
                            # Validate each item has required fields
                            validated_results = []
                            for item in results_list:
                                if isinstance(item, dict) and "filename" in item and "score" in item:
                                    validated_results.append(item)
                                else:
                                    logger.warning(f"Skipping invalid result item: {item}")
                            return validated_results
                        else:
                            logger.error(f"Results is not a list: {type(results_list)}")
                            return []
                    elif isinstance(result, list):
                        # Direct list response (fallback)
                        validated_results = []
                        for item in result:
                            if isinstance(item, dict) and "filename" in item and "score" in item:
                                validated_results.append(item)
                            else:
                                logger.warning(f"Skipping invalid result item: {item}")
                        return validated_results
                    else:
                        logger.error(f"Unexpected reranker response structure: {type(result)} - {result}")
                        return []
                else:
                    error_text = await response.text()
                    logger.error(f"Code ranking failed: {error_text}")
                    raise Exception(f"Relace API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to rank code files: {e}")
            raise

    def generate_embeddings_sync(self, 
                                texts: List[str],
                                model: str = "relace-embed-v1",
                                request_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate embeddings synchronously"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "input": texts
            }
            
            if request_params:
                payload.update(request_params)
            
            response = requests.post(self.embeddings_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Generated embeddings for {len(texts)} texts")
                return result
            else:
                logger.error(f"Embedding generation failed: {response.text}")
                raise Exception(f"Relace API error: {response.status_code}")
                        
        except Exception as e:
            logger.error(f"Error in sync embedding generation: {e}")
            raise

    def rank_code_files_sync(self,
                            query: str,
                            codebase: List[Dict[str, str]],
                            token_limit: int = 150000) -> List[Dict[str, Any]]:
        """Rank code files synchronously"""
        try:
            import requests
            
            # Ensure codebase is not empty to avoid null length errors
            if not codebase:
                logger.warning("Empty codebase provided for ranking")
                return []
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "query": query,
                "codebase": codebase,
                "token_limit": token_limit
            }
            
            response = requests.post(self.reranker_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Ranked {len(codebase)} files by relevance")
                
                # Handle the actual Relace API response structure
                if isinstance(result, dict) and "results" in result:
                    # Results are wrapped in a dict with 'results' key
                    results_list = result["results"]
                    if isinstance(results_list, list):
                        # Validate each item has required fields
                        validated_results = []
                        for item in results_list:
                            if isinstance(item, dict) and "filename" in item and "score" in item:
                                validated_results.append(item)
                            else:
                                logger.warning(f"Skipping invalid result item: {item}")
                        return validated_results
                    else:
                        logger.error(f"Results is not a list: {type(results_list)}")
                        return []
                elif isinstance(result, list):
                    # Direct list response (fallback)
                    validated_results = []
                    for item in result:
                        if isinstance(item, dict) and "filename" in item and "score" in item:
                            validated_results.append(item)
                        else:
                            logger.warning(f"Skipping invalid result item: {item}")
                    return validated_results
                else:
                    logger.error(f"Unexpected reranker response structure: {type(result)} - {result}")
                    return []
            else:
                logger.error(f"Code ranking failed: {response.text}")
                raise Exception(f"Relace API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error in sync code ranking: {e}")
            raise 