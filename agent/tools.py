"""
Tools for the Pydantic AI agent.
"""

import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from collections import OrderedDict
import time

from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

from .db_utils import (
    vector_search,
    hybrid_search,
    get_document,
    list_documents,
    get_document_chunks,
)
from .graph_utils import (
    search_knowledge_graph,
    get_entity_relationships,
    graph_client,
    get_workspace_graph_client,
)
from .models import ChunkResult, GraphSearchResult, DocumentMetadata
from .providers import get_embedding_client, get_embedding_model

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize embedding client with flexible provider
embedding_client = get_embedding_client()
EMBEDDING_MODEL = get_embedding_model()


class EmbeddingCache:
    """
    LRU cache with TTL for embedding vectors.
    Prevents repeated API calls for the same text.
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize embedding cache.

        Args:
            maxsize: Maximum number of cached embeddings
            ttl_seconds: Time-to-live in seconds (default 1 hour)
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[List[float], float]] = OrderedDict()
        self._lock = asyncio.Lock()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text using hash."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if exists and not expired."""
        async with self._lock:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                embedding, expiry = self.cache[cache_key]
                if time.time() < expiry:
                    # Move to end (most recently used)
                    self.cache.move_to_end(cache_key)
                    return embedding
                else:
                    # Expired, remove it
                    del self.cache[cache_key]
            return None

    async def set(self, text: str, embedding: List[float]):
        """Cache embedding with TTL."""
        async with self._lock:
            cache_key = self._get_cache_key(text)
            expiry = time.time() + self.ttl_seconds

            # Remove if exists
            if cache_key in self.cache:
                del self.cache[cache_key]

            # Evict oldest if at capacity
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)

            self.cache[cache_key] = (embedding, expiry)

    async def clear(self):
        """Clear all cached embeddings."""
        async with self._lock:
            self.cache.clear()

    def size(self) -> int:
        """Return current cache size."""
        return len(self.cache)


# Global embedding cache
_embedding_cache = EmbeddingCache(
    maxsize=int(os.getenv("EMBEDDING_CACHE_SIZE", "1000")),
    ttl_seconds=int(os.getenv("EMBEDDING_CACHE_TTL", "3600"))
)


async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using OpenAI with caching.

    Caches embeddings to avoid repeated API calls for the same text.
    Cache hits can significantly reduce latency and API costs.

    Args:
        text: Text to embed

    Returns:
        Embedding vector
    """
    # Check cache first
    cached_embedding = await _embedding_cache.get(text)
    if cached_embedding is not None:
        logger.debug(f"Embedding cache hit for text: {text[:50]}...")
        return cached_embedding

    # Cache miss - generate embedding
    try:
        response = await embedding_client.embeddings.create(
            model=EMBEDDING_MODEL, input=text
        )
        embedding = response.data[0].embedding

        # Cache the result
        await _embedding_cache.set(text, embedding)

        logger.debug(f"Generated and cached embedding for text: {text[:50]}...")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


# Tool Input Models
class VectorSearchInput(BaseModel):
    """Input for vector search tool with validation."""

    query: str = Field(
        ...,
        description="Search query",
        min_length=1,
        max_length=5000,
    )
    workspace_id: str = Field(
        ...,
        description="Workspace ID to search within",
        min_length=1,
        max_length=100,
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results",
        ge=1,
        le=100,  # Prevent excessive results
    )


class GraphSearchInput(BaseModel):
    """Input for graph search tool with validation."""

    query: str = Field(
        ...,
        description="Search query",
        min_length=1,
        max_length=5000,
    )
    workspace_id: str = Field(
        ...,
        description="Workspace ID for graph search",
        min_length=1,
        max_length=100,
    )


class HybridSearchInput(BaseModel):
    """Input for hybrid search tool with validation."""

    query: str = Field(
        ...,
        description="Search query",
        min_length=1,
        max_length=5000,
    )
    workspace_id: str = Field(
        ...,
        description="Workspace ID to search within",
        min_length=1,
        max_length=100,
    )
    limit: int = Field(
        default=10,
        description="Maximum number of results",
        ge=1,
        le=100,  # Prevent excessive results
    )
    text_weight: float = Field(
        default=0.3,
        description="Weight for text similarity (0-1)",
        ge=0.0,
        le=1.0,  # Ensure weight is in valid range
    )


class DocumentInput(BaseModel):
    """Input for document retrieval with validation."""

    document_id: str = Field(
        ...,
        description="Document ID to retrieve",
        min_length=1,
        max_length=100,
    )


class DocumentListInput(BaseModel):
    """Input for listing documents with validation."""

    limit: int = Field(
        default=20,
        description="Maximum number of documents",
        ge=1,
        le=1000,  # Prevent excessive listings
    )
    offset: int = Field(
        default=0,
        description="Number of documents to skip",
        ge=0,
        le=100000,  # Reasonable pagination limit
    )


class EntityRelationshipInput(BaseModel):
    """Input for entity relationship query with validation."""

    entity_name: str = Field(
        ...,
        description="Name of the entity",
        min_length=1,
        max_length=500,
    )
    depth: int = Field(
        default=2,
        description="Maximum traversal depth",
        ge=1,
        le=5,  # Prevent excessive graph traversal
    )


class EntityTimelineInput(BaseModel):
    """Input for entity timeline query with validation."""

    entity_name: str = Field(
        ...,
        description="Name of the entity",
        min_length=1,
        max_length=500,
    )
    start_date: Optional[str] = Field(
        None,
        description="Start date (ISO format)",
        max_length=30,  # ISO date length
    )
    end_date: Optional[str] = Field(
        None,
        description="End date (ISO format)",
        max_length=30,  # ISO date length
    )


# Tool Implementation Functions
async def vector_search_tool(input_data: VectorSearchInput) -> List[ChunkResult]:
    """
    Perform vector similarity search within a workspace.

    Args:
        input_data: Search parameters including workspace_id

    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)

        # Perform vector search
        results = await vector_search(
            embedding=embedding,
            workspace_id=input_data.workspace_id,
            limit=input_data.limit,
        )

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["similarity"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


async def graph_search_tool(input_data: GraphSearchInput) -> List[GraphSearchResult]:
    """
    Search the knowledge graph for a workspace.

    Note: Graphiti isolation is handled via group_id during client initialization.
    Each workspace should have its own GraphitiClient with unique group_id.

    Args:
        input_data: Search parameters including workspace_id

    Returns:
        List of graph search results
    """
    try:
        # Use workspace-specific Graphiti client for complete isolation
        if input_data.workspace_id:
            logger.info(
                f"Using workspace-specific graph client for workspace: {input_data.workspace_id}"
            )
            workspace_client = await get_workspace_graph_client(input_data.workspace_id)
            results = await workspace_client.search(input_data.query)
        else:
            # Fallback to global client if no workspace_id (backwards compatibility)
            logger.warning(
                "No workspace_id provided for graph search, using global client"
            )
            results = await search_knowledge_graph(query=input_data.query)

        # Convert to GraphSearchResult models
        return [
            GraphSearchResult(
                fact=r["fact"],
                uuid=r["uuid"],
                valid_at=r.get("valid_at"),
                invalid_at=r.get("invalid_at"),
                source_node_uuid=r.get("source_node_uuid"),
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Graph search failed: {e}")
        return []


async def hybrid_search_tool(input_data: HybridSearchInput) -> List[ChunkResult]:
    """
    Perform hybrid search (vector + keyword) within a workspace.

    Args:
        input_data: Search parameters including workspace_id

    Returns:
        List of matching chunks
    """
    try:
        # Generate embedding for the query
        embedding = await generate_embedding(input_data.query)

        # Perform hybrid search
        results = await hybrid_search(
            embedding=embedding,
            query_text=input_data.query,
            workspace_id=input_data.workspace_id,
            limit=input_data.limit,
            text_weight=input_data.text_weight,
        )

        # Convert to ChunkResult models
        return [
            ChunkResult(
                chunk_id=str(r["chunk_id"]),
                document_id=str(r["document_id"]),
                content=r["content"],
                score=r["combined_score"],
                metadata=r["metadata"],
                document_title=r["document_title"],
                document_source=r["document_source"],
            )
            for r in results
        ]

    except Exception as e:
        logger.error(f"Hybrid search failed: {e}")
        return []


async def get_document_tool(input_data: DocumentInput) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete document.

    Args:
        input_data: Document retrieval parameters

    Returns:
        Document data or None
    """
    try:
        document = await get_document(input_data.document_id)

        if document:
            # Also get all chunks for the document
            chunks = await get_document_chunks(input_data.document_id)
            document["chunks"] = chunks

        return document

    except Exception as e:
        logger.error(f"Document retrieval failed: {e}")
        return None


async def list_documents_tool(input_data: DocumentListInput) -> List[DocumentMetadata]:
    """
    List available documents.

    Args:
        input_data: Listing parameters

    Returns:
        List of document metadata
    """
    try:
        documents = await list_documents(
            limit=input_data.limit, offset=input_data.offset
        )

        # Convert to DocumentMetadata models
        return [
            DocumentMetadata(
                id=d["id"],
                title=d["title"],
                source=d["source"],
                metadata=d["metadata"],
                created_at=datetime.fromisoformat(d["created_at"]),
                updated_at=datetime.fromisoformat(d["updated_at"]),
                chunk_count=d.get("chunk_count"),
            )
            for d in documents
        ]

    except Exception as e:
        logger.error(f"Document listing failed: {e}")
        return []


async def get_entity_relationships_tool(
    input_data: EntityRelationshipInput,
) -> Dict[str, Any]:
    """
    Get relationships for an entity.

    Args:
        input_data: Entity relationship parameters

    Returns:
        Entity relationships
    """
    try:
        return await get_entity_relationships(
            entity=input_data.entity_name, depth=input_data.depth
        )

    except Exception as e:
        logger.error(f"Entity relationship query failed: {e}")
        return {
            "central_entity": input_data.entity_name,
            "related_entities": [],
            "relationships": [],
            "depth": input_data.depth,
            "error": str(e),
        }


async def get_entity_timeline_tool(
    input_data: EntityTimelineInput,
) -> List[Dict[str, Any]]:
    """
    Get timeline of facts for an entity.

    Args:
        input_data: Timeline query parameters

    Returns:
        Timeline of facts
    """
    try:
        # Parse dates if provided
        start_date = None
        end_date = None

        if input_data.start_date:
            start_date = datetime.fromisoformat(input_data.start_date)
        if input_data.end_date:
            end_date = datetime.fromisoformat(input_data.end_date)

        # Get timeline from graph
        timeline = await graph_client.get_entity_timeline(
            entity_name=input_data.entity_name, start_date=start_date, end_date=end_date
        )

        return timeline

    except Exception as e:
        logger.error(f"Entity timeline query failed: {e}")
        return []


# Combined search function for agent use
async def perform_comprehensive_search(
    query: str, use_vector: bool = True, use_graph: bool = True, limit: int = 10
) -> Dict[str, Any]:
    """
    Perform a comprehensive search using multiple methods.

    Args:
        query: Search query
        use_vector: Whether to use vector search
        use_graph: Whether to use graph search
        limit: Maximum results per search type (only applies to vector search)

    Returns:
        Combined search results
    """
    results = {
        "query": query,
        "vector_results": [],
        "graph_results": [],
        "total_results": 0,
    }

    tasks = []

    if use_vector:
        tasks.append(vector_search_tool(VectorSearchInput(query=query, limit=limit)))

    if use_graph:
        tasks.append(graph_search_tool(GraphSearchInput(query=query)))

    if tasks:
        search_results = await asyncio.gather(*tasks, return_exceptions=True)

        if use_vector and not isinstance(search_results[0], Exception):
            results["vector_results"] = search_results[0]

        if use_graph:
            graph_idx = 1 if use_vector else 0
            if not isinstance(search_results[graph_idx], Exception):
                results["graph_results"] = search_results[graph_idx]

    results["total_results"] = len(results["vector_results"]) + len(
        results["graph_results"]
    )

    return results
