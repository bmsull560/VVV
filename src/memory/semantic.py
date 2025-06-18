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


from src.memory.types import MemoryEntity, KnowledgeEntity, MemoryTier, DataSensitivity
from src.memory.storage_backend import StorageBackend

logger = logging.getLogger(__name__)

class SemanticMemory:
    """
    Semantic Memory implementation - stores knowledge entities with
    vector embeddings for semantic search and retrieval.
    
    This is a persistent store optimized for semantic similarity search.
    """
    
    def __init__(self, backend: StorageBackend, model_name='all-MiniLM-L6-v2', embedding_path="./data/semantic/embeddings"):
        """
        Initialize semantic memory store.

        Args:
            backend: The storage backend for persisting entities.
            model_name: Name of the sentence-transformer model to use.
            embedding_path: Path to store embedding indexes.
        """
        self._backend = backend
        self._embedding_path = embedding_path
        os.makedirs(self._embedding_path, exist_ok=True)

        self._st_model = None
        self._embedding_dim = 384  # Default dimension

        if SentenceTransformer:
            try:
                self._st_model = SentenceTransformer(model_name)
                self._embedding_dim = self._st_model.get_sentence_embedding_dimension()
                logger.info(f"SentenceTransformer model '{model_name}' loaded. Embedding dimension: {self._embedding_dim}")
            except Exception as e:
                logger.warning(f"Failed to load SentenceTransformer model '{model_name}': {e}. Semantic search will be degraded.")
        else:
            logger.warning("sentence-transformers is not installed. Semantic search will be degraded. Run `pip install sentence-transformers`")

        self._embedding_index = None
        self._load_embedding_index()
        logger.info("Semantic Memory initialized")
        

        
    def _load_embedding_index(self):
        """Load embedding index from storage."""
        embeddings_path = os.path.join(self._embedding_path, "embeddings.npy")
        embeddings_id_path = os.path.join(self._embedding_path, "embedding_ids.json")
        if os.path.exists(embeddings_path) and os.path.exists(embeddings_id_path):
            try:
                # Load embeddings matrix
                embeddings = np.load(embeddings_path)
                
                # Load mapping of embeddings to entity IDs
                with open(embeddings_id_path, 'r') as f:
                    embedding_ids = json.load(f)
                    
                self._embedding_index = {
                    'embeddings': embeddings,
                    'ids': embedding_ids
                }
                logger.info(f"Loaded embedding index with {len(embedding_ids)} vectors")
            except Exception as e:
                logger.error(f"Failed to load embeddings index: {e}")
                self._embedding_index = None
                

            
    def _save_embedding_index(self):
        """Save embedding index to storage."""
        if not self._embedding_index:
            return
            
        embeddings_path = os.path.join(self._embedding_path, "embeddings.npy")
        embeddings_id_path = os.path.join(self._embedding_path, "embedding_ids.json")
        
        try:
            # Save embeddings matrix
            np.save(embeddings_path, self._embedding_index['embeddings'])
            
            # Save mapping of embeddings to entity IDs
            with open(embeddings_id_path, 'w') as f:
                json.dump(self._embedding_index['ids'], f)
        except Exception as e:
            logger.error(f"Failed to save embeddings index: {e}")
            

        
    def _index_entity(self, entity: KnowledgeEntity):
        """Index a knowledge entity for efficient searching."""
        # Update embedding index if entity has embeddings
        if entity.vector_embedding:
            self._update_embedding_index(entity)
            
    def _update_embedding_index(self, entity: KnowledgeEntity):
        """Update the embedding index with a new entity vector."""
        if not entity.vector_embedding:
            return
            
        # Ensure embedding is the correct dimension
        if len(entity.vector_embedding) != self._embedding_dim:
            logger.warning(f"Embedding dimension mismatch: expected {self._embedding_dim}, got {len(entity.vector_embedding)}")
            return
            
        # Initialize embedding index if not exists
        if not self._embedding_index:
            self._embedding_index = {
                'embeddings': np.array([entity.vector_embedding], dtype=np.float32),
                'ids': [entity.id]
            }
        else:
            # Check if entity already exists in index
            if entity.id in self._embedding_index['ids']:
                # Update existing embedding
                idx = self._embedding_index['ids'].index(entity.id)
                self._embedding_index['embeddings'][idx] = entity.vector_embedding
            else:
                # Append new embedding
                new_embedding = np.array([entity.vector_embedding], dtype=np.float32)
                self._embedding_index['embeddings'] = np.vstack([self._embedding_index['embeddings'], new_embedding])
                self._embedding_index['ids'].append(entity.id)
                
        # Save updated index
        self._save_embedding_index()
        
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate vector embedding for text using the configured sentence-transformer model.

        Args:
            text: Text to embed
        Returns:
            Optional[List[float]]: Vector embedding, or None if model is not available or fails.
        """
        if not self._st_model:
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
        self._index_entity(entity)
            
        logger.info(f"Stored knowledge entity {entity.id} in semantic memory")
        return entity.id

    async def retrieve(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """Retrieve an entity by its ID."""
        return await self._backend.retrieve(entity_id)

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by its ID."""
        # Also remove from embedding index
        if self._embedding_index and entity_id in self._embedding_index['ids']:
            idx = self._embedding_index['ids'].index(entity_id)
            self._embedding_index['ids'].pop(idx)
            self._embedding_index['embeddings'] = np.delete(self._embedding_index['embeddings'], idx, axis=0)
            self._save_embedding_index()

        return await self._backend.delete(entity_id)

    async def search(self, query: Dict[str, Any], limit: int = 10) -> List[KnowledgeEntity]:
        """Search for entities based on metadata filters."""
        return await self._backend.search(query, limit)

    async def semantic_search(self, query_text: str, top_k: int = 5) -> List[Tuple[KnowledgeEntity, float]]:
        """
        Perform semantic search using vector embeddings.

        Args:
            query_text: The text to search for.
            top_k: The number of results to return.

        Returns:
            A list of tuples, each containing a retrieved entity and its similarity score.
        """
        if not self._st_model or not self._embedding_index:
            logger.warning("Semantic search is not available.")
            return []

        query_embedding = self._generate_embedding(query_text)
        if query_embedding is None:
            return []

        query_embedding = np.array(query_embedding, dtype=np.float32)
        
        # Cosine similarity
        embeddings = self._embedding_index['embeddings']
        scores = np.dot(embeddings, query_embedding) / (np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding))
        
        # Get top_k results
        top_k_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_k_indices:
            entity_id = self._embedding_index['ids'][idx]
            score = scores[idx]
            entity = await self.retrieve(entity_id)
            if entity:
                results.append((entity, float(score)))

    async def retrieve(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """
        Retrieve a knowledge entity from semantic memory.

        Args:
            entity_id: ID of the entity to retrieve

        Returns:
            Optional[KnowledgeEntity]: The retrieved entity or None if not found
        """
        if not self._backend:
            logger.error("Storage backend not configured for Semantic Memory.")
            return None
        
        try:
            entity = await self._backend.retrieve(entity_id)
            if entity and isinstance(entity, KnowledgeEntity):
                return entity
            elif entity:
                logger.warning(f"Retrieved entity {entity_id} is not a KnowledgeEntity, but {type(entity)}.")
            return None
        except Exception as e:
            logger.error(f"Error retrieving entity {entity_id} from backend: {e}")
            return None

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by its ID."""
        if not self._backend:
            logger.error("Storage backend not configured for Semantic Memory.")
            return False
            
        deleted_from_backend = await self._backend.delete(entity_id)
        if not deleted_from_backend:
            return False

        # Also remove from embedding index
        if self._embedding_index and entity_id in self._embedding_index['ids']:
            try:
                idx = self._embedding_index['ids'].index(entity_id)
                self._embedding_index['ids'].pop(idx)
                self._embedding_index['embeddings'] = np.delete(self._embedding_index['embeddings'], idx, axis=0)
                self._save_embedding_index()
            except ValueError:
                logger.warning(f"Entity ID {entity_id} not found in embedding index during delete, though backend delete succeeded.")
            except Exception as e:
                logger.error(f"Error removing {entity_id} from embedding index: {e}")
                # Backend delete succeeded, but embedding index might be inconsistent. 
                # Depending on desired robustness, might raise an error or specific status.
        return True

    async def search(self, query: Dict[str, Any], limit: int = 10, offset: int = 0) -> List[KnowledgeEntity]:
        """Search for entities based on metadata filters."""
        if not self._backend:
            logger.error("Storage backend not configured for Semantic Memory.")
            return []
        return await self._backend.search(query, limit=limit, offset=offset)

    async def semantic_search(self, query_text: str, top_k: int = 5) -> List[Tuple[KnowledgeEntity, float]]:
        """
        Perform semantic search using vector embeddings.

        Args:
            query_text: The text to search for.
            top_k: The number of results to return.

        Returns:
            A list of tuples, each containing a retrieved entity and its similarity score.
        """
        if not self._st_model:
            logger.warning("SentenceTransformer model not available for semantic search.")
            return []
        if not self._embedding_index or not self._embedding_index['ids']:
            logger.warning("Embedding index is not available or empty for semantic search.")
            return []

        query_embedding = self._generate_embedding(query_text)
        if query_embedding is None:
            logger.error("Failed to generate embedding for query text.")
            return []

        query_embedding_np = np.array(query_embedding, dtype=np.float32)
        
        embeddings_np = self._embedding_index['embeddings']
        if embeddings_np.shape[0] == 0:
             logger.warning("Embedding index is empty, cannot perform search.")
             return []

        # Cosine similarity
        # Ensure embeddings_np is 2D
        if embeddings_np.ndim == 1:
            embeddings_np = embeddings_np.reshape(1, -1)
            
        scores = np.dot(embeddings_np, query_embedding_np) / (np.linalg.norm(embeddings_np, axis=1) * np.linalg.norm(query_embedding_np))
        
        # Get top_k results, ensuring we don't request more than available
        actual_top_k = min(top_k, len(self._embedding_index['ids']))
        if actual_top_k == 0:
            return []
            
        top_k_indices = np.argsort(scores)[-actual_top_k:][::-1]
        
        results = []
        for idx in top_k_indices:
            entity_id = self._embedding_index['ids'][idx]
            score = scores[idx]
            entity = await self.retrieve(entity_id)
            if entity and isinstance(entity, KnowledgeEntity):
                results.append((entity, float(score)))
            elif entity:
                logger.warning(f"Semantic search retrieved entity {entity_id} of type {type(entity)}, expected KnowledgeEntity.")
        
        return results

