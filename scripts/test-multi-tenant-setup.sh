#!/bin/bash

# Test script for multi-tenant setup
# This script demonstrates the complete workflow for setting up a multi-tenant system

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_BASE="http://localhost:8000/v1"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Multi-Tenant System Setup Test${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to make API call and extract ID
api_post() {
    local endpoint=$1
    local data=$2
    local description=$3

    echo -e "${YELLOW}→${NC} ${description}"
    response=$(curl -s -X POST "${API_BASE}${endpoint}" \
        -H "Content-Type: application/json" \
        -d "${data}")

    echo "Response: ${response}" | head -c 200
    echo ""

    # Extract ID from response
    id=$(echo "${response}" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "${id}"
}

api_get() {
    local endpoint=$1
    local description=$2

    echo -e "${YELLOW}→${NC} ${description}"
    curl -s "${API_BASE}${endpoint}" | jq '.' || echo "(jq not installed, showing raw)"
    echo ""
}

# Step 1: Create Organization
echo -e "${GREEN}Step 1: Create Organization${NC}"
ORG_DATA='{
  "name": "Acme Corporation",
  "slug": "acme",
  "plan_tier": "pro",
  "contact_email": "admin@acme.com",
  "contact_name": "Admin User"
}'

ORG_ID=$(api_post "/organizations" "${ORG_DATA}" "Creating organization 'Acme Corporation'")
echo -e "${GREEN}✓${NC} Organization ID: ${ORG_ID}"
echo ""

# Step 2: Create Workspace
echo -e "${GREEN}Step 2: Create Workspace${NC}"
WORKSPACE_DATA='{
  "name": "Customer Support",
  "slug": "support",
  "description": "Customer support knowledge base",
  "settings": {"default_search_limit": 10}
}'

WORKSPACE_ID=$(api_post "/organizations/${ORG_ID}/workspaces" "${WORKSPACE_DATA}" "Creating workspace 'Customer Support'")
echo -e "${GREEN}✓${NC} Workspace ID: ${WORKSPACE_ID}"
echo ""

# Step 3: Create Agent
echo -e "${GREEN}Step 3: Create Agent${NC}"
AGENT_DATA='{
  "name": "Support Bot",
  "slug": "support-bot",
  "description": "Helpful customer support agent",
  "system_prompt": "You are a helpful customer support agent. Use the knowledge base to answer questions accurately and professionally.",
  "model_provider": "openai",
  "model_name": "gpt-4",
  "temperature": 0.7,
  "enabled_tools": ["vector_search", "hybrid_search", "list_documents"]
}'

AGENT_ID=$(api_post "/workspaces/${WORKSPACE_ID}/agents" "${AGENT_DATA}" "Creating agent 'Support Bot'")
echo -e "${GREEN}✓${NC} Agent ID: ${AGENT_ID}"
echo ""

# Step 4: Create API Key
echo -e "${GREEN}Step 4: Create API Key${NC}"
API_KEY_DATA='{
  "name": "Production Key",
  "scopes": ["chat", "search"],
  "rate_limit_per_minute": 100
}'

API_KEY_RESPONSE=$(curl -s -X POST "${API_BASE}/workspaces/${WORKSPACE_ID}/api-keys" \
    -H "Content-Type: application/json" \
    -d "${API_KEY_DATA}")

API_KEY=$(echo "${API_KEY_RESPONSE}" | grep -o '"key":"[^"]*"' | cut -d'"' -f4)
echo -e "${GREEN}✓${NC} API Key: ${API_KEY}"
echo -e "${YELLOW}⚠${NC}  Save this key securely! It won't be shown again."
echo ""

# Step 5: List Resources
echo -e "${GREEN}Step 5: Verify Setup${NC}"

echo -e "${BLUE}Organization Details:${NC}"
api_get "/organizations/${ORG_ID}" "Fetching organization"

echo -e "${BLUE}Workspace Details:${NC}"
api_get "/workspaces/${WORKSPACE_ID}" "Fetching workspace"

echo -e "${BLUE}Agent Details:${NC}"
api_get "/workspaces/${WORKSPACE_ID}/agents/${AGENT_ID}" "Fetching agent"

echo -e "${BLUE}List All Workspaces:${NC}"
api_get "/organizations/${ORG_ID}/workspaces" "Listing all workspaces"

echo -e "${BLUE}List All Agents:${NC}"
api_get "/workspaces/${WORKSPACE_ID}/agents" "Listing all agents in workspace"

# Summary
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Resource IDs:"
echo -e "  Organization: ${BLUE}${ORG_ID}${NC}"
echo -e "  Workspace:    ${BLUE}${WORKSPACE_ID}${NC}"
echo -e "  Agent:        ${BLUE}${AGENT_ID}${NC}"
echo -e "  API Key:      ${BLUE}${API_KEY}${NC}"
echo ""
echo "Next steps:"
echo "1. Run migrations: ./scripts/run-migrations.sh"
echo "2. Ingest documents for workspace: python -m ingestion.ingest --workspace-id ${WORKSPACE_ID}"
echo "3. Test chat: curl -X POST ${API_BASE}/workspaces/${WORKSPACE_ID}/chat \\"
echo "              -H 'Authorization: Bearer ${API_KEY}' \\"
echo "              -d '{\"agent_id\":\"${AGENT_ID}\",\"query\":\"Hello\"}'"
echo ""
