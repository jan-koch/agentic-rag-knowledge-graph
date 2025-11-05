"""
Database utilities for PostgreSQL connection and operations.
"""

import os
import json
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from collections import OrderedDict
import logging

import asyncpg
from asyncpg.pool import Pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TTLCache:
    """
    Thread-safe TTL (Time-To-Live) cache for async functions.
    Prevents excessive database queries for frequently accessed data.
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 300):
        """
        Initialize TTL cache.

        Args:
            maxsize: Maximum number of entries (default 1000)
            ttl_seconds: Time-to-live in seconds (default 300 = 5 minutes)
        """
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            if key in self.cache:
                value, expiry_time = self.cache[key]
                if time.time() < expiry_time:
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    return value
                else:
                    # Expired, remove it
                    del self.cache[key]
            return None

    async def set(self, key: str, value: Any):
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            expiry_time = time.time() + self.ttl_seconds

            # Remove if already exists
            if key in self.cache:
                del self.cache[key]

            # Check if we need to evict (LRU)
            if len(self.cache) >= self.maxsize:
                # Remove oldest (first) item
                self.cache.popitem(last=False)

            self.cache[key] = (value, expiry_time)

    async def invalidate(self, key: str):
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate
        """
        async with self._lock:
            if key in self.cache:
                del self.cache[key]

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()

    def size(self) -> int:
        """Return current cache size."""
        return len(self.cache)


# Global caches
_workspace_cache = TTLCache(
    maxsize=int(os.getenv("WORKSPACE_CACHE_SIZE", "1000")),
    ttl_seconds=int(os.getenv("WORKSPACE_CACHE_TTL", "300"))
)


async def retry_with_exponential_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Retry a function with exponential backoff.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"Function {func.__name__} failed after {max_retries} retries: {e}"
                )
                raise

            # Calculate delay with exponential backoff
            delay = min(initial_delay * (exponential_base ** attempt), max_delay)

            logger.warning(
                f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {delay:.2f}s: {e}"
            )

            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


class DatabasePool:
    """Manages PostgreSQL connection pool."""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database pool.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        self.pool: Optional[Pool] = None

    async def initialize(self):
        """Create connection pool with retry logic."""
        if not self.pool:
            async def _create_pool():
                return await asyncpg.create_pool(
                    self.database_url,
                    min_size=5,
                    max_size=20,
                    max_inactive_connection_lifetime=300,
                    command_timeout=60,
                )

            # Retry pool creation with exponential backoff
            self.pool = await retry_with_exponential_backoff(
                _create_pool,
                max_retries=3,
                initial_delay=1.0,
                max_delay=10.0,
                exceptions=(
                    asyncpg.PostgresConnectionError,
                    ConnectionRefusedError,
                    OSError,
                ),
            )
            logger.info("Database connection pool initialized")

    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as connection:
            yield connection

    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool metrics
        """
        if not self.pool:
            return {
                "initialized": False,
                "size": 0,
                "free": 0,
                "used": 0,
                "utilization_percent": 0,
            }

        size = self.pool.get_size()
        free = self.pool.get_idle_size()
        used = size - free
        max_size = self.pool.get_max_size()
        min_size = self.pool.get_min_size()

        utilization = (used / max_size * 100) if max_size > 0 else 0

        return {
            "initialized": True,
            "size": size,
            "free": free,
            "used": used,
            "min_size": min_size,
            "max_size": max_size,
            "utilization_percent": round(utilization, 2),
            "is_near_capacity": utilization > 80,  # Warn if >80% used
        }

    async def health_check(self) -> bool:
        """
        Check database connection health.

        Returns:
            True if connection is healthy
        """
        try:
            if not self.pool:
                return False

            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                return result == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database pool instance
db_pool = DatabasePool()


async def initialize_database():
    """Initialize database connection pool."""
    await db_pool.initialize()


async def close_database():
    """Close database connection pool."""
    await db_pool.close()


# Session Management Functions
async def create_session(
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout_minutes: int = 60,
) -> str:
    """
    Create a new session.

    Args:
        user_id: Optional user identifier
        workspace_id: Optional workspace ID for multi-tenant support
        metadata: Optional session metadata
        timeout_minutes: Session timeout in minutes

    Returns:
        Session ID
    """
    async with db_pool.acquire() as conn:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=timeout_minutes)

        result = await conn.fetchrow(
            """
            INSERT INTO sessions (user_id, workspace_id, metadata, expires_at)
            VALUES ($1, $2::uuid, $3, $4)
            RETURNING id::text
            """,
            user_id,
            workspace_id,
            json.dumps(metadata or {}),
            expires_at,
        )

        return result["id"]


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session by ID.

    Args:
        session_id: Session UUID

    Returns:
        Session data or None if not found/expired
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                id::text,
                user_id,
                metadata,
                created_at,
                updated_at,
                expires_at
            FROM sessions
            WHERE id = $1::uuid
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            session_id,
        )

        if result:
            return {
                "id": result["id"],
                "user_id": result["user_id"],
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat(),
                "expires_at": (
                    result["expires_at"].isoformat() if result["expires_at"] else None
                ),
            }

        return None


async def update_session(session_id: str, metadata: Dict[str, Any]) -> bool:
    """
    Update session metadata.

    Args:
        session_id: Session UUID
        metadata: New metadata to merge

    Returns:
        True if updated, False if not found
    """
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE sessions
            SET metadata = metadata || $2::jsonb
            WHERE id = $1::uuid
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            """,
            session_id,
            json.dumps(metadata),
        )

        return result.split()[-1] != "0"


# Message Management Functions
async def add_message(
    session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Add a message to a session.

    Args:
        session_id: Session UUID
        role: Message role (user/assistant/system)
        content: Message content
        metadata: Optional message metadata

    Returns:
        Message ID
    """
    async with db_pool.acquire() as conn:
        # Get workspace_id from session
        workspace_id = await conn.fetchval(
            "SELECT workspace_id FROM sessions WHERE id = $1::uuid", session_id
        )

        result = await conn.fetchrow(
            """
            INSERT INTO messages (session_id, workspace_id, role, content, metadata)
            VALUES ($1::uuid, $2::uuid, $3, $4, $5)
            RETURNING id::text
            """,
            session_id,
            workspace_id,
            role,
            content,
            json.dumps(metadata or {}),
        )

        return result["id"]


async def get_session_messages(
    session_id: str, limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get messages for a session.

    Args:
        session_id: Session UUID
        limit: Maximum number of messages to return

    Returns:
        List of messages ordered by creation time
    """
    async with db_pool.acquire() as conn:
        query = """
            SELECT 
                id::text,
                role,
                content,
                metadata,
                created_at
            FROM messages
            WHERE session_id = $1::uuid
            ORDER BY created_at
        """

        if limit:
            query += f" LIMIT {limit}"

        results = await conn.fetch(query, session_id)

        return [
            {
                "id": row["id"],
                "role": row["role"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat(),
            }
            for row in results
        ]


# Document Management Functions
async def get_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    Get document by ID.

    Args:
        document_id: Document UUID

    Returns:
        Document data or None if not found
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT 
                id::text,
                title,
                source,
                content,
                metadata,
                created_at,
                updated_at
            FROM documents
            WHERE id = $1::uuid
            """,
            document_id,
        )

        if result:
            return {
                "id": result["id"],
                "title": result["title"],
                "source": result["source"],
                "content": result["content"],
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"].isoformat(),
                "updated_at": result["updated_at"].isoformat(),
            }

        return None


async def list_documents(
    limit: int = 100, offset: int = 0, metadata_filter: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    List documents with optional filtering.

    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        metadata_filter: Optional metadata filter

    Returns:
        List of documents
    """
    async with db_pool.acquire() as conn:
        query = """
            SELECT 
                d.id::text,
                d.title,
                d.source,
                d.metadata,
                d.created_at,
                d.updated_at,
                COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
        """

        params = []
        conditions = []

        if metadata_filter:
            conditions.append(f"d.metadata @> ${len(params) + 1}::jsonb")
            params.append(json.dumps(metadata_filter))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += """
            GROUP BY d.id, d.title, d.source, d.metadata, d.created_at, d.updated_at
            ORDER BY d.created_at DESC
            LIMIT $%d OFFSET $%d
        """ % (
            len(params) + 1,
            len(params) + 2,
        )

        params.extend([limit, offset])

        results = await conn.fetch(query, *params)

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "source": row["source"],
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"].isoformat(),
                "updated_at": row["updated_at"].isoformat(),
                "chunk_count": row["chunk_count"],
            }
            for row in results
        ]


# Vector Search Functions
async def vector_search(
    embedding: List[float], workspace_id: str, limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search within a workspace.

    Args:
        embedding: Query embedding vector
        workspace_id: Workspace UUID to search within
        limit: Maximum number of results

    Returns:
        List of matching chunks ordered by similarity (best first)
    """
    async with db_pool.acquire() as conn:
        # Convert embedding to PostgreSQL vector string format
        # PostgreSQL vector format: '[1.0,2.0,3.0]' (no spaces after commas)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        results = await conn.fetch(
            "SELECT * FROM match_chunks($1::vector, $2::uuid, $3)",
            embedding_str,
            workspace_id,
            limit,
        )

        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "similarity": row["similarity"],
                "metadata": json.loads(row["metadata"]),
                "document_title": row["document_title"],
                "document_source": row["document_source"],
            }
            for row in results
        ]


async def hybrid_search(
    embedding: List[float],
    query_text: str,
    workspace_id: str,
    limit: int = 10,
    text_weight: float = 0.3,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (vector + keyword) within a workspace.

    Args:
        embedding: Query embedding vector
        query_text: Query text for keyword search
        workspace_id: Workspace UUID to search within
        limit: Maximum number of results
        text_weight: Weight for text similarity (0-1)

    Returns:
        List of matching chunks ordered by combined score (best first)
    """
    async with db_pool.acquire() as conn:
        # Convert embedding to PostgreSQL vector string format
        # PostgreSQL vector format: '[1.0,2.0,3.0]' (no spaces after commas)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"

        results = await conn.fetch(
            "SELECT * FROM hybrid_search($1::vector, $2, $3::uuid, $4, $5)",
            embedding_str,
            query_text,
            workspace_id,
            limit,
            text_weight,
        )

        return [
            {
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "content": row["content"],
                "combined_score": row["combined_score"],
                "vector_similarity": row["vector_similarity"],
                "text_similarity": row["text_similarity"],
                "metadata": json.loads(row["metadata"]),
                "document_title": row["document_title"],
                "document_source": row["document_source"],
            }
            for row in results
        ]


# Chunk Management Functions
async def get_document_chunks(document_id: str) -> List[Dict[str, Any]]:
    """
    Get all chunks for a document.

    Args:
        document_id: Document UUID

    Returns:
        List of chunks ordered by chunk index
    """
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            "SELECT * FROM get_document_chunks($1::uuid)", document_id
        )

        return [
            {
                "chunk_id": row["chunk_id"],
                "content": row["content"],
                "chunk_index": row["chunk_index"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in results
        ]


# Utility Functions
async def execute_query(query: str, *params) -> List[Dict[str, Any]]:
    """
    Execute a custom query.

    Args:
        query: SQL query
        *params: Query parameters

    Returns:
        Query results
    """
    async with db_pool.acquire() as conn:
        results = await conn.fetch(query, *params)
        return [dict(row) for row in results]


async def test_connection() -> bool:
    """
    Test database connection.

    Returns:
        True if connection successful
    """
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# ====================
# Multi-Tenancy Functions
# ====================


# Organization Functions
async def create_organization(
    name: str,
    slug: str,
    plan_tier: str = "free",
    contact_email: str = "",
    contact_name: Optional[str] = None,
    max_workspaces: int = 1,
    max_documents_per_workspace: int = 100,
    max_monthly_requests: int = 10000,
) -> str:
    """
    Create a new organization.

    Returns:
        Organization ID
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO organizations (
                name, slug, plan_tier, contact_email, contact_name,
                max_workspaces, max_documents_per_workspace, max_monthly_requests
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id::text
            """,
            name,
            slug,
            plan_tier,
            contact_email,
            contact_name,
            max_workspaces,
            max_documents_per_workspace,
            max_monthly_requests,
        )
        return result["id"]


async def get_organization(org_id: str) -> Optional[Dict[str, Any]]:
    """Get organization by ID."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT
                id::text,
                name,
                slug,
                plan_tier,
                max_workspaces,
                max_documents_per_workspace,
                max_monthly_requests,
                contact_email,
                contact_name,
                settings,
                created_at,
                updated_at
            FROM organizations
            WHERE id = $1::uuid
            """,
            org_id,
        )

        if result:
            data = dict(result)
            # Parse JSONB fields
            if isinstance(data.get("settings"), str):
                data["settings"] = json.loads(data["settings"])
            return data
        return None


async def list_organizations() -> List[Dict[str, Any]]:
    """List all organizations."""
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT
                id::text,
                name,
                slug,
                plan_tier,
                max_workspaces,
                max_documents_per_workspace,
                max_monthly_requests,
                contact_email,
                contact_name,
                settings,
                created_at,
                updated_at
            FROM organizations
            ORDER BY created_at DESC
            """
        )
        organizations = []
        for row in results:
            data = dict(row)
            # Parse JSONB fields
            if isinstance(data.get("settings"), str):
                data["settings"] = json.loads(data["settings"])
            organizations.append(data)
        return organizations


# Workspace Functions
async def create_workspace(
    organization_id: str,
    name: str,
    slug: str,
    description: Optional[str] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a new workspace.

    Returns:
        Workspace ID
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO workspaces (organization_id, name, slug, description, settings)
            VALUES ($1::uuid, $2, $3, $4, $5)
            RETURNING id::text
            """,
            organization_id,
            name,
            slug,
            description,
            json.dumps(settings or {}),
        )
        return result["id"]


async def get_workspace(workspace_id: str) -> Optional[Dict[str, Any]]:
    """
    Get workspace by ID with caching.

    Uses TTL cache to prevent excessive database queries for workspace metadata.
    Cache entries expire after WORKSPACE_CACHE_TTL seconds (default 300 = 5 minutes).
    """
    # Check cache first
    cache_key = f"workspace:{workspace_id}"
    cached_value = await _workspace_cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    # Cache miss - query database
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT
                id::text,
                organization_id::text,
                name,
                slug,
                description,
                settings,
                document_count,
                monthly_requests,
                last_request_reset_at,
                created_at,
                updated_at
            FROM workspaces
            WHERE id = $1::uuid
            """,
            workspace_id,
        )

        if result:
            data = dict(result)
            data["settings"] = json.loads(data.get("settings", "{}"))

            # Cache the result
            await _workspace_cache.set(cache_key, data)

            return data
        return None


async def list_workspaces(organization_id: str) -> List[Dict[str, Any]]:
    """List all workspaces for an organization."""
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT
                id::text,
                organization_id::text,
                name,
                slug,
                description,
                settings,
                document_count,
                monthly_requests,
                last_request_reset_at,
                created_at,
                updated_at
            FROM workspaces
            WHERE organization_id = $1::uuid
            ORDER BY created_at DESC
            """,
            organization_id,
        )
        workspaces = []
        for row in results:
            data = dict(row)
            data["settings"] = json.loads(data.get("settings", "{}"))
            workspaces.append(data)
        return workspaces


async def increment_workspace_requests(workspace_id: str):
    """Increment monthly request counter for workspace."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE workspaces
            SET monthly_requests = monthly_requests + 1
            WHERE id = $1::uuid
            """,
            workspace_id,
        )


# Agent Functions
async def create_agent(
    workspace_id: str,
    name: str,
    slug: str,
    system_prompt: str,
    description: Optional[str] = None,
    model_provider: str = "openai",
    model_name: str = "gpt-4",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    enabled_tools: Optional[List[str]] = None,
    tool_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a new agent.

    Returns:
        Agent ID
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO agents (
                workspace_id, name, slug, description, system_prompt,
                model_provider, model_name, temperature, max_tokens,
                enabled_tools, tool_config
            )
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id::text
            """,
            workspace_id,
            name,
            slug,
            description,
            system_prompt,
            model_provider,
            model_name,
            temperature,
            max_tokens,
            json.dumps(enabled_tools or []),
            json.dumps(tool_config or {}),
        )
        return result["id"]


async def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Get agent by ID."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT
                id::text,
                workspace_id::text,
                name,
                slug,
                description,
                system_prompt,
                model_provider,
                model_name,
                temperature,
                max_tokens,
                enabled_tools,
                tool_config,
                is_active,
                settings,
                created_at,
                updated_at
            FROM agents
            WHERE id = $1::uuid
            """,
            agent_id,
        )

        if result:
            data = dict(result)
            data["enabled_tools"] = json.loads(data.get("enabled_tools", "[]"))
            data["tool_config"] = json.loads(data.get("tool_config", "{}"))
            data["settings"] = json.loads(data.get("settings", "{}"))
            return data
        return None


async def list_agents(
    workspace_id: str, include_inactive: bool = False
) -> List[Dict[str, Any]]:
    """List all agents for a workspace."""
    async with db_pool.acquire() as conn:
        query = """
            SELECT
                id::text,
                workspace_id::text,
                name,
                slug,
                description,
                system_prompt,
                model_provider,
                model_name,
                temperature,
                max_tokens,
                enabled_tools,
                tool_config,
                is_active,
                settings,
                created_at,
                updated_at
            FROM agents
            WHERE workspace_id = $1::uuid
        """

        if not include_inactive:
            query += " AND is_active = true"

        query += " ORDER BY created_at DESC"

        results = await conn.fetch(query, workspace_id)
        agents = []
        for row in results:
            data = dict(row)
            data["enabled_tools"] = json.loads(data.get("enabled_tools", "[]"))
            data["tool_config"] = json.loads(data.get("tool_config", "{}"))
            data["settings"] = json.loads(data.get("settings", "{}"))
            agents.append(data)
        return agents


async def update_agent(agent_id: str, updates: Dict[str, Any]) -> bool:
    """Update agent fields."""
    if not updates:
        return False

    # Build dynamic update query
    set_clauses = []
    params = []
    param_idx = 1

    for field, value in updates.items():
        if field in ["enabled_tools", "tool_config", "settings"]:
            set_clauses.append(f"{field} = ${param_idx}::jsonb")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{field} = ${param_idx}")
            params.append(value)
        param_idx += 1

    params.append(agent_id)

    async with db_pool.acquire() as conn:
        result = await conn.execute(
            f"""
            UPDATE agents
            SET {', '.join(set_clauses)}
            WHERE id = ${param_idx}::uuid
            """,
            *params,
        )
        return result != "UPDATE 0"


async def delete_agent(agent_id: str) -> bool:
    """Delete an agent."""
    async with db_pool.acquire() as conn:
        result = await conn.execute("DELETE FROM agents WHERE id = $1::uuid", agent_id)
        return result != "DELETE 0"


# API Key Functions
async def create_api_key(
    workspace_id: str,
    name: str,
    key_prefix: str,
    key_hash: str,
    scopes: List[str],
    rate_limit_per_minute: int = 60,
    expires_at: Optional[datetime] = None,
) -> str:
    """
    Create a new API key.

    Returns:
        API key ID
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO api_keys (
                workspace_id, name, key_prefix, key_hash,
                scopes, rate_limit_per_minute, expires_at
            )
            VALUES ($1::uuid, $2, $3, $4, $5, $6, $7)
            RETURNING id::text
            """,
            workspace_id,
            name,
            key_prefix,
            key_hash,
            json.dumps(scopes),
            rate_limit_per_minute,
            expires_at,
        )
        return result["id"]


async def get_api_key_by_prefix(key_prefix: str) -> Optional[Dict[str, Any]]:
    """Get API key by prefix."""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT
                id::text,
                workspace_id::text,
                name,
                key_prefix,
                key_hash,
                scopes,
                rate_limit_per_minute,
                is_active,
                last_used_at,
                expires_at,
                created_at,
                revoked_at
            FROM api_keys
            WHERE key_prefix = $1
              AND is_active = true
              AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
              AND revoked_at IS NULL
            """,
            key_prefix,
        )

        if result:
            data = dict(result)
            data["scopes"] = json.loads(data.get("scopes", "[]"))
            return data
        return None


async def update_api_key_last_used(api_key_id: str):
    """Update API key last used timestamp."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE api_keys
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE id = $1::uuid
            """,
            api_key_id,
        )


async def revoke_api_key(api_key_id: str) -> bool:
    """Revoke an API key."""
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE api_keys
            SET is_active = false, revoked_at = CURRENT_TIMESTAMP
            WHERE id = $1::uuid
            """,
            api_key_id,
        )
        return result != "UPDATE 0"


async def list_api_keys(workspace_id: str) -> List[Dict[str, Any]]:
    """List all API keys for a workspace."""
    async with db_pool.acquire() as conn:
        results = await conn.fetch(
            """
            SELECT
                id::text,
                workspace_id::text,
                name,
                key_prefix,
                scopes,
                rate_limit_per_minute,
                is_active,
                last_used_at,
                expires_at,
                created_at,
                revoked_at
            FROM api_keys
            WHERE workspace_id = $1::uuid
            ORDER BY created_at DESC
            """,
            workspace_id,
        )

        api_keys = []
        for row in results:
            data = dict(row)
            data["scopes"] = json.loads(data.get("scopes", "[]"))
            api_keys.append(data)
        return api_keys
