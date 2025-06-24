"""
Semantic Memory for B2BValue Memory Architecture.

This module implements the Semantic Memory tier, which provides
long-term knowledge storage with vector embeddings and semantic search.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
import json
import os
import numpy as np
from datetime import datetime, timezone

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


from memory.memory_types import MemoryEntity, KnowledgeEntity, MemoryTier, DataSensitivity
from memory.storage_backend import StorageBackend

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    Semantic Memory implementation - stores knowledge entities with
    vector embeddings for semantic search and retrieval.
    
    This is a persistent store optimized for semantic similarity search.
    """
    
    def __init__(self, backend: StorageBackend, model_name='all-MiniLM-L6-v2'):
        """
        Constructs the SemanticMemory instance.
        Call initialize() before using the instance.

        Args:
            backend: The storage backend for persisting entities.
            model_name: Name of the sentence-transformer model to use.
        """
        self._backend = backend
        self._model_name = model_name
        self._st_model = None
        self._embedding_dim = None
        self.initialized = False

    def initialize(self):
        """
        Initializes the semantic memory.
        This method should be called before any operations are performed.
        """
        if self.initialized:
            return
        
        logger.info("Semantic Memory initialized, model will be loaded on first use.")
        self.initialized = True

    def _get_model(self):
        """Lazy-loads the SentenceTransformer model."""
        if self._st_model is None:
            if SentenceTransformer:
                try:
                    self._st_model = SentenceTransformer(self._model_name)
                    self._embedding_dim = self._st_model.get_sentence_embedding_dimension()
                    logger.info(f"SentenceTransformer model '{self._model_name}' loaded. Embedding dimension: {self._embedding_dim}")
                except Exception as e:
                    logger.error(f"Failed to load SentenceTransformer model '{self._model_name}': {e}")
                    # Set to a dummy value to prevent repeated load attempts
                    self._st_model = 'failed'
            else:
                logger.warning("sentence-transformers is not installed. Semantic search is disabled.")
                self._st_model = 'failed'
        return self._st_model if self._st_model != 'failed' else None

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate vector embedding for text using the configured sentence-transformer model.

        Args:
            text: Text to embed
        Returns:
            Optional[List[float]]: Vector embedding, or None if model is not available or fails.
        """
        model = self._get_model()
        if not model:
            logger.warning("SentenceTransformer model not available, cannot generate embedding.")
            return None

        try:
            embedding = self._st_model.encode(text, convert_to_numpy=True)
            logger.info(f"Generated embedding for text of length {len(text)}")
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: '{text[:100]}...': {e}")
            return None
    
    async def store(self, entity: KnowledgeEntity) -> str:
        """
        Store a knowledge entity in semantic memory.
        
        Args:
            entity: The knowledge entity to store
            
        Returns:
            str: ID of the stored entity
        """
        if not isinstance(entity, KnowledgeEntity):
            raise TypeError("Semantic Memory can only store KnowledgeEntity objects")
            
        entity.tier = MemoryTier.SEMANTIC
        entity.updated_at = datetime.now(timezone.utc)
        
        if entity.content and not entity.vector_embedding:
            entity.vector_embedding = self._generate_embedding(entity.content)
            
        await self._backend.store(entity)
            
        logger.info(f"Stored knowledge entity {entity.id} in semantic memory")
        return entity.id

    async def retrieve(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """Retrieve an entity by its ID."""
        return await self._backend.retrieve(entity_id)

    async def semantic_search(self, query_text: str, top_k: int = 5) -> List[KnowledgeEntity]:
        """
        Performs semantic search for entities related to the query text.

        Args:
            query_text: The text to search for.
            top_k: The number of results to return.

        Returns:
            A list of the most relevant KnowledgeEntity objects.
        """
        query_embedding = self._generate_embedding(query_text)
        if not query_embedding:
            logger.warning("Could not generate query embedding. Cannot perform semantic search.")
            return []

        search_query = {"vector": query_embedding}
        return await self._backend.search(search_query, limit=top_k)

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by its ID."""
        return await self._backend.delete(entity_id)

