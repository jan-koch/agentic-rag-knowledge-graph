"""
Multi-Tenant RAG Admin Dashboard

A Streamlit-based web UI for managing organizations, workspaces, agents, and API keys.
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8058/v1"

# Page configuration
st.set_page_config(
    page_title="Multi-Tenant RAG Admin",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #f0f2f6;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Helper functions
def api_request(method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make API request."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            return {"error": f"Unsupported method: {method}"}

        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.json().get("detail", response.text)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def format_datetime(dt_str: str) -> str:
    """Format datetime string."""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str


# Sidebar navigation
st.sidebar.markdown("# 🤖 Multi-Tenant RAG")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["🏢 Organizations", "📁 Workspaces", "🤖 Agents", "🔑 API Keys", "💬 Chat", "📊 Health"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Stats")

# Get health status
health = api_request("GET", "/health")
if health.get("success"):
    health_data = health["data"]
    st.sidebar.success(f"✅ Status: {health_data['status'].upper()}")
    st.sidebar.info(f"🏗️ Multi-Tenant: {health_data['multi_tenant']}")
    st.sidebar.info(f"📦 Version: {health_data['version']}")
else:
    st.sidebar.error("❌ API Unavailable")


# Main content
st.markdown('<div class="main-header">Multi-Tenant RAG Admin Dashboard</div>', unsafe_allow_html=True)


# ==========================================
# ORGANIZATIONS PAGE
# ==========================================
if page == "🏢 Organizations":
    st.markdown('<div class="section-header">Organizations Management</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Create New Organization")
        with st.form("create_org_form"):
            org_name = st.text_input("Organization Name", placeholder="Acme Corporation")
            org_slug = st.text_input("Slug (URL-friendly)", placeholder="acme")
            org_email = st.text_input("Contact Email", placeholder="admin@acme.com")
            org_contact_name = st.text_input("Contact Name (Optional)", placeholder="John Doe")
            org_plan = st.selectbox("Plan Tier", ["free", "starter", "pro", "enterprise"])

            if st.form_submit_button("Create Organization", type="primary"):
                result = api_request("POST", "/organizations", {
                    "name": org_name,
                    "slug": org_slug,
                    "contact_email": org_email,
                    "contact_name": org_contact_name or None,
                    "plan_tier": org_plan
                })

                if result.get("success"):
                    st.success(f"✅ Organization '{org_name}' created successfully!")
                    st.json(result["data"])
                else:
                    st.error(f"❌ Failed to create organization: {result.get('error')}")

    with col2:
        st.markdown("### Get Organization")
        org_id = st.text_input("Organization ID", placeholder="uuid")
        if st.button("Fetch Organization"):
            if org_id:
                result = api_request("GET", f"/organizations/{org_id}")
                if result.get("success"):
                    org = result["data"]
                    st.success("✅ Organization found!")
                    st.markdown(f"""
                    <div class="info-card">
                    <strong>{org['name']}</strong><br>
                    Slug: {org['slug']}<br>
                    Plan: {org['plan_tier']}<br>
                    Email: {org['contact_email']}<br>
                    Max Workspaces: {org['max_workspaces']}<br>
                    Created: {format_datetime(org['created_at'])}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ {result.get('error')}")

    st.markdown("---")
    st.markdown("### All Organizations")

    if st.button("Refresh Organizations List", key="refresh_orgs"):
        st.rerun()

    result = api_request("GET", "/organizations")
    if result.get("success"):
        orgs = result["data"]
        if orgs:
            st.success(f"✅ Found {len(orgs)} organization(s)")

            for org in orgs:
                with st.expander(f"🏢 {org['name']} ({org['slug']}) - {org['plan_tier'].upper()}"):
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.markdown(f"""
                        **ID:** `{org['id']}`
                        **Slug:** {org['slug']}
                        **Plan:** {org['plan_tier']}
                        **Contact:** {org['contact_email']}
                        """)

                    with col_b:
                        st.markdown(f"""
                        **Max Workspaces:** {org['max_workspaces']}
                        **Max Docs/Workspace:** {org['max_documents_per_workspace']}
                        **Max Monthly Requests:** {org['max_monthly_requests']}
                        **Created:** {format_datetime(org['created_at'])}
                        """)

                    if st.button(f"Copy ID", key=f"copy_org_{org['id']}", help="Click to copy organization ID"):
                        st.code(org['id'], language=None)
        else:
            st.info("No organizations found. Create one above!")
    else:
        st.error(f"❌ Failed to load organizations: {result.get('error')}")


# ==========================================
# WORKSPACES PAGE
# ==========================================
elif page == "📁 Workspaces":
    st.markdown('<div class="section-header">Workspaces Management</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Create New Workspace")

        # Fetch organizations for dropdown
        orgs_result = api_request("GET", "/organizations")
        org_options = {}

        if orgs_result.get("success") and orgs_result["data"]:
            for org in orgs_result["data"]:
                org_options[f"{org['name']} ({org['slug']}) - {org['plan_tier']}"] = org['id']

        with st.form("create_workspace_form"):
            if org_options:
                selected_org = st.selectbox(
                    "Select Organization",
                    options=list(org_options.keys()),
                    help="Choose which organization this workspace belongs to"
                )
                ws_org_id = org_options[selected_org]
                st.caption(f"Organization ID: `{ws_org_id}`")
            else:
                st.warning("⚠️ No organizations found. Create an organization first!")
                ws_org_id = st.text_input("Organization ID (manual)", placeholder="uuid")

            ws_name = st.text_input("Workspace Name", placeholder="Customer Support")
            ws_slug = st.text_input("Slug", placeholder="support")
            ws_desc = st.text_area("Description", placeholder="Customer support knowledge base")

            if st.form_submit_button("Create Workspace", type="primary"):
                if not ws_org_id:
                    st.error("❌ Please select an organization")
                else:
                    result = api_request("POST", f"/organizations/{ws_org_id}/workspaces", {
                        "name": ws_name,
                        "slug": ws_slug,
                        "description": ws_desc,
                        "settings": {}
                    })

                    if result.get("success"):
                        st.success(f"✅ Workspace '{ws_name}' created successfully!")
                        st.json(result["data"])
                    else:
                        st.error(f"❌ Failed to create workspace: {result.get('error')}")

    with col2:
        st.markdown("### Get Workspace")
        ws_id = st.text_input("Workspace ID", placeholder="uuid")
        if st.button("Fetch Workspace"):
            if ws_id:
                result = api_request("GET", f"/workspaces/{ws_id}")
                if result.get("success"):
                    ws = result["data"]
                    st.success("✅ Workspace found!")
                    st.markdown(f"""
                    <div class="info-card">
                    <strong>{ws['name']}</strong><br>
                    Slug: {ws['slug']}<br>
                    Description: {ws.get('description', 'N/A')}<br>
                    Documents: {ws['document_count']}<br>
                    Monthly Requests: {ws['monthly_requests']}<br>
                    Created: {format_datetime(ws['created_at'])}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ {result.get('error')}")

    st.markdown("---")
    st.markdown("### List Workspaces")
    list_org_id = st.text_input("Organization ID (for listing)", placeholder="uuid", key="list_ws_org")
    if st.button("List All Workspaces"):
        if list_org_id:
            result = api_request("GET", f"/organizations/{list_org_id}/workspaces")
            if result.get("success"):
                workspaces = result["data"]
                st.success(f"✅ Found {len(workspaces)} workspace(s)")
                for ws in workspaces:
                    with st.expander(f"📁 {ws['name']} ({ws['slug']})"):
                        st.json(ws)
            else:
                st.error(f"❌ {result.get('error')}")


# ==========================================
# AGENTS PAGE
# ==========================================
elif page == "🤖 Agents":
    st.markdown('<div class="section-header">Agents Management</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Create New Agent")

        # Fetch all organizations and their workspaces
        orgs_result = api_request("GET", "/organizations")
        workspace_options = {}

        if orgs_result.get("success") and orgs_result["data"]:
            for org in orgs_result["data"]:
                # Get workspaces for this org
                ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")
                if ws_result.get("success") and ws_result["data"]:
                    for ws in ws_result["data"]:
                        workspace_options[f"{ws['name']} ({ws['slug']}) - {org['name']}"] = ws['id']

        with st.form("create_agent_form"):
            if workspace_options:
                selected_workspace = st.selectbox(
                    "Select Workspace",
                    options=list(workspace_options.keys()),
                    help="Choose which workspace this agent belongs to"
                )
                agent_ws_id = workspace_options[selected_workspace]
                st.caption(f"Workspace ID: `{agent_ws_id}`")
            else:
                st.warning("⚠️ No workspaces found. Create a workspace first!")
                agent_ws_id = st.text_input("Workspace ID (manual)", placeholder="uuid")

            agent_name = st.text_input("Agent Name", placeholder="Support Bot")
            agent_slug = st.text_input("Slug", placeholder="support-bot")
            agent_desc = st.text_area("Description", placeholder="Helpful support agent")
            agent_prompt = st.text_area("System Prompt", placeholder="You are a helpful support agent...")

            col_a, col_b = st.columns(2)
            with col_a:
                agent_provider = st.selectbox("Model Provider", ["openai", "ollama", "openrouter", "gemini"])
                agent_model = st.text_input("Model Name", placeholder="gpt-4")
            with col_b:
                agent_temp = st.slider("Temperature", 0.0, 1.0, 0.7)
                agent_max_tokens = st.number_input("Max Tokens", value=None, placeholder="Optional")

            agent_tools = st.multiselect(
                "Enabled Tools",
                ["vector_search", "hybrid_search", "graph_search", "list_documents", "get_document"],
                default=["vector_search", "hybrid_search"]
            )

            if st.form_submit_button("Create Agent", type="primary"):
                result = api_request("POST", f"/workspaces/{agent_ws_id}/agents", {
                    "name": agent_name,
                    "slug": agent_slug,
                    "description": agent_desc,
                    "system_prompt": agent_prompt,
                    "model_provider": agent_provider,
                    "model_name": agent_model,
                    "temperature": agent_temp,
                    "max_tokens": agent_max_tokens if agent_max_tokens else None,
                    "enabled_tools": agent_tools
                })

                if result.get("success"):
                    st.success(f"✅ Agent '{agent_name}' created successfully!")
                    st.json(result["data"])
                else:
                    st.error(f"❌ Failed to create agent: {result.get('error')}")

    with col2:
        st.markdown("### Get Agent")
        get_agent_ws_id = st.text_input("Workspace ID", placeholder="uuid", key="get_agent_ws")
        get_agent_id = st.text_input("Agent ID", placeholder="uuid", key="get_agent_id")
        if st.button("Fetch Agent"):
            if get_agent_ws_id and get_agent_id:
                result = api_request("GET", f"/workspaces/{get_agent_ws_id}/agents/{get_agent_id}")
                if result.get("success"):
                    agent = result["data"]
                    st.success("✅ Agent found!")
                    st.markdown(f"""
                    <div class="info-card">
                    <strong>{agent['name']}</strong><br>
                    Slug: {agent['slug']}<br>
                    Model: {agent['model_provider']} / {agent['model_name']}<br>
                    Temperature: {agent['temperature']}<br>
                    Active: {'✅' if agent['is_active'] else '❌'}<br>
                    Tools: {', '.join(agent['enabled_tools'])}<br>
                    Created: {format_datetime(agent['created_at'])}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ {result.get('error')}")

    st.markdown("---")
    st.markdown("### List Agents")
    list_agent_ws_id = st.text_input("Workspace ID (for listing)", placeholder="uuid", key="list_agent_ws")
    include_inactive = st.checkbox("Include inactive agents")
    if st.button("List All Agents"):
        if list_agent_ws_id:
            endpoint = f"/workspaces/{list_agent_ws_id}/agents"
            if include_inactive:
                endpoint += "?include_inactive=true"
            result = api_request("GET", endpoint)
            if result.get("success"):
                agents = result["data"]
                st.success(f"✅ Found {len(agents)} agent(s)")
                for agent in agents:
                    status = "✅ Active" if agent['is_active'] else "❌ Inactive"
                    with st.expander(f"🤖 {agent['name']} - {status}"):
                        st.json(agent)
            else:
                st.error(f"❌ {result.get('error')}")


# ==========================================
# API KEYS PAGE
# ==========================================
elif page == "🔑 API Keys":
    st.markdown('<div class="section-header">API Keys Management</div>', unsafe_allow_html=True)

    st.warning("⚠️ API keys are only shown once at creation time. Store them securely!")

    st.markdown("### Create New API Key")
    with st.form("create_api_key_form"):
        key_ws_id = st.text_input("Workspace ID", placeholder="uuid")
        key_name = st.text_input("Key Name", placeholder="Production Key")

        col_a, col_b = st.columns(2)
        with col_a:
            key_scopes = st.multiselect(
                "Scopes",
                ["chat", "search", "ingest", "admin"],
                default=["chat", "search"]
            )
        with col_b:
            key_rate_limit = st.number_input("Rate Limit (requests/min)", value=60, min_value=1)

        key_expires = st.checkbox("Set expiration date")
        key_expires_at = None
        if key_expires:
            key_expires_at = st.date_input("Expires at")

        if st.form_submit_button("Create API Key", type="primary"):
            data = {
                "name": key_name,
                "scopes": key_scopes,
                "rate_limit_per_minute": key_rate_limit
            }
            if key_expires_at:
                data["expires_at"] = key_expires_at.isoformat()

            result = api_request("POST", f"/workspaces/{key_ws_id}/api-keys", data)

            if result.get("success"):
                key_data = result["data"]
                st.success("✅ API Key created successfully!")
                st.markdown(f"""
                <div class="success-box">
                <strong>⚠️ SAVE THIS KEY - IT WON'T BE SHOWN AGAIN!</strong><br><br>
                <strong>API Key:</strong><br>
                <code style="font-size: 1.1rem; background: #f8f9fa; padding: 0.5rem; border-radius: 0.25rem; display: block; margin: 0.5rem 0;">
                {key_data['key']}
                </code><br>
                <strong>Key ID:</strong> {key_data['id']}<br>
                <strong>Name:</strong> {key_data['name']}<br>
                <strong>Workspace ID:</strong> {key_data['workspace_id']}<br>
                <strong>Created:</strong> {format_datetime(key_data['created_at'])}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"❌ Failed to create API key: {result.get('error')}")


# ==========================================
# CHAT PAGE
# ==========================================
elif page == "💬 Chat":
    st.markdown('<div class="section-header">Chat with Agent</div>', unsafe_allow_html=True)

    st.info("🚧 Multi-tenant chat endpoint is not yet implemented. This will be available in the next phase.")

    st.markdown("### Coming Soon:")
    st.markdown("""
    - Real-time chat with workspace agents
    - Session management
    - Tool usage tracking
    - Streaming responses
    - Message history
    """)


# ==========================================
# HEALTH PAGE
# ==========================================
elif page == "📊 Health":
    st.markdown('<div class="section-header">System Health</div>', unsafe_allow_html=True)

    if st.button("Refresh Status", type="primary"):
        st.rerun()

    health = api_request("GET", "/health")

    if health.get("success"):
        health_data = health["data"]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Status", health_data["status"].upper())
        with col2:
            st.metric("Multi-Tenant", "Enabled" if health_data["multi_tenant"] else "Disabled")
        with col3:
            st.metric("Version", health_data["version"])

        st.markdown("---")
        st.json(health_data)
    else:
        st.error(f"❌ Failed to fetch health status: {health.get('error')}")


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>Multi-Tenant RAG Admin Dashboard v1.0.0</p>
    <p>API Base: <code>{}</code></p>
</div>
""".format(API_BASE_URL), unsafe_allow_html=True)
