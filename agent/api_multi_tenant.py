"""
Multi-tenant API endpoints for workspace and agent management.
"""

import os
import logging
import hashlib
import secrets
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

from .models import (
    Organization,
    Workspace,
    Agent,
    APIKey,
    CreateOrganizationRequest,
    CreateWorkspaceRequest,
    CreateAgentRequest,
    UpdateAgentRequest,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    MultiTenantChatRequest,
    ChatResponse
)
from .db_utils import (
    create_organization,
    get_organization,
    create_workspace,
    get_workspace,
    list_workspaces,
    create_agent,
    get_agent,
    list_agents,
    update_agent,
    delete_agent,
    create_api_key,
    get_api_key_by_prefix,
    update_api_key_last_used,
    revoke_api_key,
    increment_workspace_requests
)

logger = logging.getLogger(__name__)

# Create router for multi-tenant endpoints
router = APIRouter(prefix="/v1", tags=["multi-tenant"])


# ====================
# Helper Functions
# ====================

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        Tuple of (full_key, key_prefix, key_hash)
    """
    # Generate random key
    random_bytes = secrets.token_bytes(32)
    full_key = f"apikey_live_{secrets.token_urlsafe(32)}"

    # Create prefix (first 15 chars for lookup)
    key_prefix = full_key[:15]

    # Hash full key for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()

    return full_key, key_prefix, key_hash


def verify_api_key_hash(full_key: str, stored_hash: str) -> bool:
    """Verify API key matches stored hash."""
    computed_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return computed_hash == stored_hash


# ====================
# Organization Endpoints
# ====================

@router.post("/organizations", response_model=Organization)
async def create_organization_endpoint(
    request: CreateOrganizationRequest
):
    """Create a new organization."""
    try:
        org_id = await create_organization(
            name=request.name,
            slug=request.slug,
            plan_tier=request.plan_tier,
            contact_email=request.contact_email,
            contact_name=request.contact_name
        )

        org = await get_organization(org_id)
        if not org:
            raise HTTPException(500, "Failed to retrieve created organization")

        return Organization(**org)

    except Exception as e:
        logger.error(f"Failed to create organization: {e}")
        raise HTTPException(500, f"Failed to create organization: {str(e)}")


@router.get("/organizations/{org_id}", response_model=Organization)
async def get_organization_endpoint(org_id: str):
    """Get organization by ID."""
    org = await get_organization(org_id)
    if not org:
        raise HTTPException(404, "Organization not found")

    return Organization(**org)


@router.get("/organizations", response_model=List[Organization])
async def list_organizations_endpoint():
    """List all organizations."""
    from .db_utils import list_organizations
    orgs = await list_organizations()
    return [Organization(**org) for org in orgs]


# ====================
# Workspace Endpoints
# ====================

@router.post("/organizations/{org_id}/workspaces", response_model=Workspace)
async def create_workspace_endpoint(
    org_id: str,
    request: CreateWorkspaceRequest
):
    """Create a new workspace within an organization."""
    try:
        # Verify organization exists
        org = await get_organization(org_id)
        if not org:
            raise HTTPException(404, "Organization not found")

        workspace_id = await create_workspace(
            organization_id=org_id,
            name=request.name,
            slug=request.slug,
            description=request.description,
            settings=request.settings
        )

        workspace = await get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(500, "Failed to retrieve created workspace")

        return Workspace(**workspace)

    except Exception as e:
        logger.error(f"Failed to create workspace: {e}")
        raise HTTPException(500, f"Failed to create workspace: {str(e)}")


@router.get("/workspaces/{workspace_id}", response_model=Workspace)
async def get_workspace_endpoint(workspace_id: str):
    """Get workspace by ID."""
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(404, "Workspace not found")

    return Workspace(**workspace)


@router.get("/organizations/{org_id}/workspaces", response_model=List[Workspace])
async def list_workspaces_endpoint(org_id: str):
    """List all workspaces for an organization."""
    # Verify organization exists
    org = await get_organization(org_id)
    if not org:
        raise HTTPException(404, "Organization not found")

    workspaces = await list_workspaces(org_id)
    return [Workspace(**w) for w in workspaces]


# ====================
# Agent Endpoints
# ====================

@router.post("/workspaces/{workspace_id}/agents", response_model=Agent)
async def create_agent_endpoint(
    workspace_id: str,
    request: CreateAgentRequest
):
    """Create a new agent within a workspace."""
    try:
        # Verify workspace exists
        workspace = await get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(404, "Workspace not found")

        agent_id = await create_agent(
            workspace_id=workspace_id,
            name=request.name,
            slug=request.slug,
            system_prompt=request.system_prompt,
            description=request.description,
            model_provider=request.model_provider,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            enabled_tools=request.enabled_tools,
            tool_config=request.tool_config
        )

        agent = await get_agent(agent_id)
        if not agent:
            raise HTTPException(500, "Failed to retrieve created agent")

        return Agent(**agent)

    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(500, f"Failed to create agent: {str(e)}")


@router.get("/workspaces/{workspace_id}/agents", response_model=List[Agent])
async def list_agents_endpoint(
    workspace_id: str,
    include_inactive: bool = False
):
    """List all agents for a workspace."""
    # Verify workspace exists
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(404, "Workspace not found")

    agents = await list_agents(workspace_id, include_inactive)
    return [Agent(**a) for a in agents]


@router.get("/workspaces/{workspace_id}/agents/{agent_id}", response_model=Agent)
async def get_agent_endpoint(
    workspace_id: str,
    agent_id: str
):
    """Get agent by ID."""
    agent = await get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    # Verify agent belongs to workspace
    if agent["workspace_id"] != workspace_id:
        raise HTTPException(403, "Agent does not belong to this workspace")

    return Agent(**agent)


@router.patch("/workspaces/{workspace_id}/agents/{agent_id}", response_model=Agent)
async def update_agent_endpoint(
    workspace_id: str,
    agent_id: str,
    request: UpdateAgentRequest
):
    """Update an agent."""
    # Verify agent exists and belongs to workspace
    agent = await get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    if agent["workspace_id"] != workspace_id:
        raise HTTPException(403, "Agent does not belong to this workspace")

    # Build updates dict from request (only include non-None values)
    updates = {
        k: v for k, v in request.dict(exclude_unset=True).items()
        if v is not None
    }

    if not updates:
        # No updates provided, return current agent
        return Agent(**agent)

    # Update agent
    success = await update_agent(agent_id, updates)
    if not success:
        raise HTTPException(500, "Failed to update agent")

    # Fetch updated agent
    updated_agent = await get_agent(agent_id)
    return Agent(**updated_agent)


@router.delete("/workspaces/{workspace_id}/agents/{agent_id}")
async def delete_agent_endpoint(
    workspace_id: str,
    agent_id: str
):
    """Delete an agent."""
    # Verify agent exists and belongs to workspace
    agent = await get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    if agent["workspace_id"] != workspace_id:
        raise HTTPException(403, "Agent does not belong to this workspace")

    success = await delete_agent(agent_id)
    if not success:
        raise HTTPException(500, "Failed to delete agent")

    return {"status": "success", "message": "Agent deleted"}


# ====================
# API Key Endpoints
# ====================

@router.post("/workspaces/{workspace_id}/api-keys", response_model=CreateAPIKeyResponse)
async def create_api_key_endpoint(
    workspace_id: str,
    request: CreateAPIKeyRequest
):
    """
    Create a new API key for a workspace.

    WARNING: The full API key is only returned once at creation time.
    Store it securely as it cannot be retrieved later.
    """
    try:
        # Verify workspace exists
        workspace = await get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(404, "Workspace not found")

        # Generate API key
        full_key, key_prefix, key_hash = generate_api_key()

        # Create in database
        api_key_id = await create_api_key(
            workspace_id=workspace_id,
            name=request.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=request.scopes,
            rate_limit_per_minute=request.rate_limit_per_minute,
            expires_at=request.expires_at
        )

        return CreateAPIKeyResponse(
            id=UUID(api_key_id),
            name=request.name,
            key=full_key,  # Only time full key is shown
            key_prefix=key_prefix,
            workspace_id=UUID(workspace_id),
            created_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(500, f"Failed to create API key: {str(e)}")


@router.get("/workspaces/{workspace_id}/api-keys", response_model=List[APIKey])
async def list_api_keys_endpoint(workspace_id: str):
    """
    List API keys for a workspace.

    Note: Full keys are never returned in list operations.
    """
    # Verify workspace exists
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(404, "Workspace not found")

    # TODO: Implement list_api_keys in db_utils
    # For now, return empty list
    return []


@router.delete("/workspaces/{workspace_id}/api-keys/{key_id}")
async def revoke_api_key_endpoint(
    workspace_id: str,
    key_id: str
):
    """Revoke an API key."""
    # TODO: Verify key belongs to workspace
    success = await revoke_api_key(key_id)
    if not success:
        raise HTTPException(404, "API key not found")

    return {"status": "success", "message": "API key revoked"}


# ====================
# Multi-Tenant Chat Endpoint
# ====================

@router.post("/workspaces/{workspace_id}/chat", response_model=ChatResponse)
async def workspace_chat_endpoint(
    workspace_id: str,
    request: MultiTenantChatRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Chat with an agent in a workspace.

    Requires valid API key for the workspace.
    """
    # TODO: Validate API key
    # For now, this endpoint is unprotected (will add auth middleware)

    # Verify workspace exists
    workspace = await get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(404, "Workspace not found")

    # Verify agent exists and belongs to workspace
    agent = await get_agent(str(request.agent_id))
    if not agent:
        raise HTTPException(404, "Agent not found")

    if agent["workspace_id"] != workspace_id:
        raise HTTPException(403, "Agent does not belong to this workspace")

    # Verify agent is active
    if not agent["is_active"]:
        raise HTTPException(400, "Agent is not active")

    # Increment workspace request counter
    await increment_workspace_requests(workspace_id)

    # TODO: Implement actual chat logic with workspace-aware agent
    # For now, return placeholder
    raise HTTPException(501, "Multi-tenant chat not yet implemented. Need to integrate with agent system.")


# ====================
# Health Check
# ====================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "multi_tenant": True,
        "version": "1.0.0"
    }
