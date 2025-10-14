"""
Pydantic models for data validation and serialization.
"""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SearchType(str, Enum):
    """Search type enumeration."""

    VECTOR = "vector"
    HYBRID = "hybrid"
    GRAPH = "graph"


# Request Models
class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity"
    )
    user_id: Optional[str] = Field(None, description="User identifier")
    workspace_id: Optional[str] = Field(
        None, description="Workspace ID for multi-tenant support"
    )
    agent_id: Optional[str] = Field(
        None, description="Agent ID for workspace-specific agents"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    search_type: SearchType = Field(
        default=SearchType.HYBRID, description="Type of search to perform"
    )

    model_config = ConfigDict(use_enum_values=True)


class SearchRequest(BaseModel):
    """Search request model."""

    query: str = Field(..., description="Search query")
    search_type: SearchType = Field(
        default=SearchType.HYBRID, description="Type of search"
    )
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")

    model_config = ConfigDict(use_enum_values=True)


# OpenAI-compatible Models for Open WebUI integration
class OpenAIMessage(BaseModel):
    """OpenAI-compatible message model."""

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")


class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str = Field(default="riddly-rag", description="Model identifier")
    messages: List[OpenAIMessage] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(
        default=0.7, ge=0, le=2, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        default=2000, ge=1, description="Maximum tokens to generate"
    )
    stream: Optional[bool] = Field(
        default=False, description="Whether to stream responses"
    )
    search_type: Optional[SearchType] = Field(
        default=SearchType.HYBRID, description="RAG search type"
    )


class OpenAIChoice(BaseModel):
    """OpenAI-compatible choice model."""

    index: int = Field(..., description="Choice index")
    message: OpenAIMessage = Field(..., description="Generated message")
    finish_reason: Literal["stop", "length", "content_filter"] = Field(
        ..., description="Why generation stopped"
    )


class OpenAIUsage(BaseModel):
    """OpenAI-compatible usage model."""

    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: int = Field(..., description="Tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")


class OpenAIChatResponse(BaseModel):
    """OpenAI-compatible chat completion response."""

    id: str = Field(..., description="Unique identifier")
    object: Literal["chat.completion"] = Field(
        default="chat.completion", description="Object type"
    )
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used")
    choices: List[OpenAIChoice] = Field(..., description="Generated choices")
    usage: OpenAIUsage = Field(..., description="Token usage")


class OpenAIStreamChoice(BaseModel):
    """OpenAI-compatible streaming choice model."""

    index: int = Field(..., description="Choice index")
    delta: Dict[str, Any] = Field(..., description="Delta update")
    finish_reason: Optional[Literal["stop", "length", "content_filter"]] = Field(
        None, description="Why generation stopped"
    )


class OpenAIStreamResponse(BaseModel):
    """OpenAI-compatible streaming response."""

    id: str = Field(..., description="Unique identifier")
    object: Literal["chat.completion.chunk"] = Field(
        default="chat.completion.chunk", description="Object type"
    )
    created: int = Field(..., description="Unix timestamp")
    model: str = Field(..., description="Model used")
    choices: List[OpenAIStreamChoice] = Field(..., description="Generated choices")


class OpenAIModel(BaseModel):
    """OpenAI-compatible model information."""

    id: str = Field(..., description="Model identifier")
    object: Literal["model"] = Field(default="model", description="Object type")
    created: int = Field(..., description="Unix timestamp")
    owned_by: str = Field(..., description="Model owner")


class OpenAIModelList(BaseModel):
    """OpenAI-compatible model list response."""

    object: Literal["list"] = Field(default="list", description="Object type")
    data: List[OpenAIModel] = Field(..., description="Available models")


# Response Models
class DocumentMetadata(BaseModel):
    """Document metadata model."""

    id: str
    title: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = None


class ChunkResult(BaseModel):
    """Chunk search result model."""

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    document_title: str
    document_source: str

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        """Ensure score is between 0 and 1."""
        return max(0.0, min(1.0, v))


class GraphSearchResult(BaseModel):
    """Knowledge graph search result model."""

    fact: str
    uuid: str
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    source_node_uuid: Optional[str] = None


class EntityRelationship(BaseModel):
    """Entity relationship model."""

    from_entity: str
    to_entity: str
    relationship_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[ChunkResult] = Field(default_factory=list)
    graph_results: List[GraphSearchResult] = Field(default_factory=list)
    total_results: int = 0
    search_type: SearchType
    query_time_ms: float


class ToolCall(BaseModel):
    """Tool call information model."""

    tool_name: str
    args: Dict[str, Any] = Field(default_factory=dict)
    tool_call_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""

    message: str
    session_id: str
    sources: List[DocumentMetadata] = Field(default_factory=list)
    tools_used: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamDelta(BaseModel):
    """Streaming response delta."""

    content: str
    delta_type: Literal["text", "tool_call", "end"] = "text"
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Multi-Tenancy Models
class Organization(BaseModel):
    """Organization model (billing entity)."""

    id: UUID
    name: str
    slug: str
    plan_tier: Literal["free", "starter", "pro", "enterprise"] = "free"
    max_workspaces: int = 1
    max_documents_per_workspace: int = 100
    max_monthly_requests: int = 10000
    contact_email: str
    contact_name: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class Workspace(BaseModel):
    """Workspace model (isolated knowledge base)."""

    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    document_count: int = 0
    monthly_requests: int = 0
    created_at: datetime
    updated_at: datetime


class Agent(BaseModel):
    """Agent model (behavior configuration)."""

    id: UUID
    workspace_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    system_prompt: str
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    enabled_tools: List[str] = Field(default_factory=list)
    tool_config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class APIKey(BaseModel):
    """API Key model (workspace-scoped)."""

    id: UUID
    workspace_id: UUID
    name: str
    key_prefix: str  # For display: "sk_live_abc123..."
    scopes: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int = 60
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None


# Request/Response Models for Multi-Tenancy
class CreateOrganizationRequest(BaseModel):
    """Request to create an organization."""

    name: str
    slug: str
    plan_tier: Literal["free", "starter", "pro", "enterprise"] = "free"
    contact_email: str
    contact_name: Optional[str] = None


class CreateWorkspaceRequest(BaseModel):
    """Request to create a workspace."""

    name: str
    slug: str
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""

    name: str
    slug: str
    description: Optional[str] = None
    system_prompt: str
    model_provider: str = "openai"
    model_name: str = "gpt-4"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    enabled_tools: List[str] = Field(default_factory=list)
    tool_config: Dict[str, Any] = Field(default_factory=dict)


class UpdateAgentRequest(BaseModel):
    """Request to update an agent."""

    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = None
    enabled_tools: Optional[List[str]] = None
    tool_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class CreateAPIKeyRequest(BaseModel):
    """Request to create an API key."""

    name: str
    scopes: List[str] = Field(default=["chat", "search"])
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)
    expires_at: Optional[datetime] = None


class CreateAPIKeyResponse(BaseModel):
    """Response with new API key (only time full key is returned)."""

    id: UUID
    name: str
    key: str  # Full key, only shown once
    key_prefix: str
    workspace_id: UUID
    created_at: datetime


# Updated Chat Request for multi-tenancy
class MultiTenantChatRequest(BaseModel):
    """Multi-tenant chat request model."""

    agent_id: UUID = Field(..., description="Agent to chat with")
    query: str = Field(..., description="User message", min_length=1)
    session_id: Optional[UUID] = Field(
        None, description="Session ID for conversation continuity"
    )
    user_id: Optional[str] = Field(None, description="User identifier")
    stream: bool = Field(default=False, description="Whether to stream response")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# Database Models
class Document(BaseModel):
    """Document model."""

    id: Optional[str] = None
    workspace_id: Optional[UUID] = None
    title: str
    source: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Chunk(BaseModel):
    """Document chunk model."""

    id: Optional[str] = None
    document_id: str
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    token_count: Optional[int] = None
    created_at: Optional[datetime] = None

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        """Validate embedding dimensions."""
        if v is not None and len(v) != 1536:  # OpenAI text-embedding-3-small
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class Session(BaseModel):
    """Session model."""

    id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class Message(BaseModel):
    """Message model."""

    id: Optional[str] = None
    session_id: str
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    model_config = ConfigDict(use_enum_values=True)


# Agent Models
class AgentDependencies(BaseModel):
    """Dependencies for the agent."""

    session_id: str
    workspace_id: Optional[str] = None
    database_url: Optional[str] = None
    neo4j_uri: Optional[str] = None
    openai_api_key: Optional[str] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class AgentContext(BaseModel):
    """Agent execution context."""

    session_id: str
    messages: List[Message] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    search_results: List[ChunkResult] = Field(default_factory=list)
    graph_results: List[GraphSearchResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Ingestion Models
class IngestionConfig(BaseModel):
    """Configuration for document ingestion."""

    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)
    max_chunk_size: int = Field(default=2000, ge=500, le=10000)
    use_semantic_chunking: bool = True
    extract_entities: bool = True
    # New option for faster ingestion
    skip_graph_building: bool = Field(
        default=False, description="Skip knowledge graph building for faster ingestion"
    )

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Ensure overlap is less than chunk size."""
        chunk_size = info.data.get("chunk_size", 1000)
        if v >= chunk_size:
            raise ValueError(
                f"Chunk overlap ({v}) must be less than chunk size ({chunk_size})"
            )
        return v


class IngestionResult(BaseModel):
    """Result of document ingestion."""

    document_id: str
    title: str
    chunks_created: int
    entities_extracted: int
    relationships_created: int
    processing_time_ms: float
    errors: List[str] = Field(default_factory=list)


# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


# Health Check Models
class HealthStatus(BaseModel):
    """Health check status."""

    status: Literal["healthy", "degraded", "unhealthy"]
    database: bool
    graph_database: bool
    llm_connection: bool
    version: str
    timestamp: datetime
