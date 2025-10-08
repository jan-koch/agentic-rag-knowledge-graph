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
    ["📊 Dashboard", "🏢 Organizations", "📁 Workspaces", "🤖 Agents", "🔑 API Keys", "💬 Chat", "🏥 Health"]
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
# DASHBOARD PAGE
# ==========================================
if page == "📊 Dashboard":
    st.markdown('<div class="section-header">System Overview</div>', unsafe_allow_html=True)

    # Fetch all data for dashboard
    orgs_result = api_request("GET", "/organizations")

    if orgs_result.get("success") and orgs_result["data"]:
        organizations = orgs_result["data"]
        total_orgs = len(organizations)
        total_workspaces = 0
        total_documents = 0
        total_agents = 0
        total_requests = 0

        workspace_data = []
        agent_data = []

        # Collect all workspace and agent data
        for org in organizations:
            ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")
            if ws_result.get("success") and ws_result["data"]:
                workspaces = ws_result["data"]
                total_workspaces += len(workspaces)

                for ws in workspaces:
                    total_documents += ws.get('document_count', 0)
                    total_requests += ws.get('monthly_requests', 0)
                    workspace_data.append({
                        'org': org['name'],
                        'workspace': ws['name'],
                        'docs': ws.get('document_count', 0),
                        'requests': ws.get('monthly_requests', 0)
                    })

                    # Get agents for this workspace
                    agents_result = api_request("GET", f"/workspaces/{ws['id']}/agents")
                    if agents_result.get("success") and agents_result["data"]:
                        agents = agents_result["data"]
                        total_agents += len(agents)
                        for agent in agents:
                            agent_data.append({
                                'workspace': ws['name'],
                                'agent': agent['name'],
                                'active': agent['is_active']
                            })

        # Display high-level metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🏢 Organizations", total_orgs)
        with col2:
            st.metric("📁 Workspaces", total_workspaces)
        with col3:
            st.metric("📄 Total Documents", total_documents)
        with col4:
            st.metric("🤖 Active Agents", total_agents)

        st.markdown("---")

        # Second row of metrics
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.metric("📊 Monthly Requests", total_requests)
        with col6:
            avg_docs_per_workspace = total_documents / total_workspaces if total_workspaces > 0 else 0
            st.metric("📈 Avg Docs/Workspace", f"{avg_docs_per_workspace:.1f}")
        with col7:
            plan_distribution = {}
            for org in organizations:
                plan = org['plan_tier']
                plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
            most_common_plan = max(plan_distribution, key=plan_distribution.get) if plan_distribution else "N/A"
            st.metric("💼 Most Common Plan", most_common_plan.upper())
        with col8:
            active_workspaces = sum(1 for ws in workspace_data if ws['docs'] > 0)
            st.metric("✅ Active Workspaces", active_workspaces)

        st.markdown("---")

        # Top workspaces by documents
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### 📊 Top Workspaces by Documents")
            if workspace_data:
                sorted_workspaces = sorted(workspace_data, key=lambda x: x['docs'], reverse=True)[:5]
                for idx, ws in enumerate(sorted_workspaces, 1):
                    st.markdown(f"""
                    <div class="info-card">
                    <strong>{idx}. {ws['workspace']}</strong> ({ws['org']})<br>
                    📄 {ws['docs']} documents | 📊 {ws['requests']} requests
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No workspace data available")

        with col_right:
            st.markdown("### 🤖 Agents Status")
            if agent_data:
                active_agents = sum(1 for a in agent_data if a['active'])
                inactive_agents = len(agent_data) - active_agents

                st.markdown(f"""
                <div class="info-card">
                <strong>Total Agents:</strong> {len(agent_data)}<br>
                ✅ Active: {active_agents}<br>
                ❌ Inactive: {inactive_agents}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Recent Agents:**")
                for agent in agent_data[:5]:
                    status_icon = "✅" if agent['active'] else "❌"
                    st.caption(f"{status_icon} {agent['agent']} ({agent['workspace']})")
            else:
                st.info("No agents configured")

        st.markdown("---")

        # Organization breakdown
        st.markdown("### 🏢 Organization Breakdown")
        for org in organizations:
            ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")
            ws_count = len(ws_result["data"]) if ws_result.get("success") else 0
            docs_count = sum(ws.get('document_count', 0) for ws in ws_result["data"]) if ws_result.get("success") else 0

            col_org1, col_org2, col_org3, col_org4 = st.columns([3, 2, 2, 2])
            with col_org1:
                st.markdown(f"**{org['name']}** ({org['slug']})")
            with col_org2:
                st.caption(f"Plan: {org['plan_tier'].upper()}")
            with col_org3:
                st.caption(f"Workspaces: {ws_count} / {org['max_workspaces']}")
            with col_org4:
                st.caption(f"Documents: {docs_count}")

        st.markdown("---")

        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        with action_col1:
            if st.button("🏢 Create Organization", use_container_width=True):
                st.switch_page = "🏢 Organizations"
                st.info("Navigate to Organizations page to create")
        with action_col2:
            if st.button("📁 Create Workspace", use_container_width=True):
                st.info("Navigate to Workspaces page to create")
        with action_col3:
            if st.button("🤖 Create Agent", use_container_width=True):
                st.info("Navigate to Agents page to create")
        with action_col4:
            if st.button("💬 Start Chatting", use_container_width=True):
                st.info("Navigate to Chat page to start")

    else:
        st.warning("⚠️ No organizations found. Create your first organization to get started!")

        st.markdown("### Getting Started")
        st.markdown("""
        1. **Create an Organization** - Set up your first organization with a plan tier
        2. **Create a Workspace** - Add a workspace under your organization
        3. **Ingest Documents** - Use `python ingest_workspace.py` to add documents
        4. **Create an Agent** - Configure an AI agent for your workspace
        5. **Start Chatting** - Use the Chat page to interact with your agent
        """)


# ==========================================
# ORGANIZATIONS PAGE
# ==========================================
elif page == "🏢 Organizations":
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
    st.markdown("### Workspaces Overview")

    # Fetch all organizations and their workspaces
    orgs_result = api_request("GET", "/organizations")

    if orgs_result.get("success") and orgs_result["data"]:
        total_workspaces = 0
        total_documents = 0

        for org in orgs_result["data"]:
            with st.expander(f"🏢 {org['name']} ({org['slug']}) - {org['plan_tier'].upper()}", expanded=True):
                ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")

                if ws_result.get("success") and ws_result["data"]:
                    workspaces = ws_result["data"]
                    total_workspaces += len(workspaces)

                    # Create metrics row
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Workspaces", f"{len(workspaces)} / {org['max_workspaces']}")
                    with col_b:
                        total_docs_in_org = sum(ws.get('document_count', 0) for ws in workspaces)
                        total_documents += total_docs_in_org
                        st.metric("Total Documents", total_docs_in_org)
                    with col_c:
                        total_requests = sum(ws.get('monthly_requests', 0) for ws in workspaces)
                        st.metric("Monthly Requests", f"{total_requests} / {org['max_monthly_requests']}")

                    st.markdown("---")

                    # Display each workspace with details
                    for ws in workspaces:
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

                        with col1:
                            st.markdown(f"**📁 {ws['name']}**")
                            st.caption(f"Slug: `{ws['slug']}`")

                        with col2:
                            doc_count = ws.get('document_count', 0)
                            max_docs = org['max_documents_per_workspace']
                            doc_percentage = (doc_count / max_docs * 100) if max_docs > 0 else 0
                            st.metric("Documents", doc_count)
                            if doc_percentage > 80:
                                st.caption(f"⚠️ {doc_percentage:.0f}% capacity")
                            else:
                                st.caption(f"✅ {doc_percentage:.0f}% capacity")

                        with col3:
                            st.metric("Requests", ws.get('monthly_requests', 0))

                        with col4:
                            # Check if workspace has been recently updated
                            updated_at = ws.get('updated_at')
                            if updated_at:
                                from datetime import datetime, timedelta
                                try:
                                    updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                                    now = datetime.now(updated.tzinfo)
                                    hours_since_update = (now - updated).total_seconds() / 3600

                                    if hours_since_update < 1:
                                        st.success("🟢 Active")
                                        st.caption("< 1 hour ago")
                                    elif hours_since_update < 24:
                                        st.info("🟡 Recent")
                                        st.caption(f"{int(hours_since_update)}h ago")
                                    else:
                                        days = int(hours_since_update / 24)
                                        st.warning("⚪ Idle")
                                        st.caption(f"{days}d ago")
                                except:
                                    st.caption("Unknown")
                            else:
                                st.caption("No activity")

                        # Show workspace details in a collapsible section
                        with st.container():
                            if st.checkbox(f"Show details", key=f"details_{ws['id']}"):
                                detail_col1, detail_col2 = st.columns(2)

                                with detail_col1:
                                    st.markdown(f"""
                                    **Workspace ID:** `{ws['id']}`
                                    **Description:** {ws.get('description', 'N/A')}
                                    **Created:** {format_datetime(ws['created_at'])}
                                    """)

                                with detail_col2:
                                    st.markdown(f"""
                                    **Updated:** {format_datetime(ws['updated_at'])}
                                    **Status:** {'🟢 Active' if ws.get('document_count', 0) > 0 else '⚪ Empty'}
                                    """)

                                # Show ingestion actions
                                st.markdown("**Quick Actions:**")
                                action_col1, action_col2 = st.columns(2)
                                with action_col1:
                                    if st.button("📤 Ingest Documents", key=f"ingest_{ws['id']}"):
                                        st.info("Use `python ingest_workspace.py --workspace-id " + ws['id'] + " --path /path/to/docs`")
                                with action_col2:
                                    if st.button("📊 View Details", key=f"view_{ws['id']}"):
                                        st.json(ws)

                        st.markdown("---")
                else:
                    st.info("No workspaces in this organization")

        # Overall summary at the top
        st.markdown("### 📊 Overall Summary")
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        with summary_col1:
            st.metric("Total Organizations", len(orgs_result["data"]))
        with summary_col2:
            st.metric("Total Workspaces", total_workspaces)
        with summary_col3:
            st.metric("Total Documents", total_documents)
    else:
        st.warning("No organizations found. Create an organization first!")


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

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'selected_workspace' not in st.session_state:
        st.session_state.selected_workspace = None
    if 'selected_agent' not in st.session_state:
        st.session_state.selected_agent = None

    # Configuration sidebar
    with st.sidebar:
        st.markdown("### Chat Configuration")

        # Fetch organizations and workspaces
        orgs_result = api_request("GET", "/organizations")
        workspace_options = {}

        if orgs_result.get("success") and orgs_result["data"]:
            for org in orgs_result["data"]:
                ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")
                if ws_result.get("success") and ws_result["data"]:
                    for ws in ws_result["data"]:
                        workspace_options[f"{ws['name']} ({ws['slug']}) - {org['name']}"] = ws['id']

        if workspace_options:
            selected_workspace_label = st.selectbox(
                "Select Workspace",
                options=list(workspace_options.keys()),
                key="chat_workspace_select"
            )
            selected_workspace_id = workspace_options[selected_workspace_label]

            # Fetch agents for selected workspace
            agents_result = api_request("GET", f"/workspaces/{selected_workspace_id}/agents")
            agent_options = {}

            if agents_result.get("success") and agents_result["data"]:
                for agent in agents_result["data"]:
                    if agent['is_active']:
                        agent_options[f"{agent['name']} ({agent['slug']})"] = agent['id']

            if agent_options:
                selected_agent_label = st.selectbox(
                    "Select Agent",
                    options=list(agent_options.keys()),
                    key="chat_agent_select"
                )
                selected_agent_id = agent_options[selected_agent_label]

                st.session_state.selected_workspace = selected_workspace_id
                st.session_state.selected_agent = selected_agent_id

                if st.button("🗑️ Clear Chat History"):
                    st.session_state.messages = []
                    st.session_state.current_session_id = None
                    st.rerun()
            else:
                st.warning("No active agents found in this workspace")
        else:
            st.warning("No workspaces available. Create a workspace and agent first!")

    # Main chat interface
    if st.session_state.selected_workspace and st.session_state.selected_agent:
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Show tool usage if available
                if message.get("tool_calls"):
                    with st.expander("🔧 Tool Usage"):
                        for tool_call in message["tool_calls"]:
                            st.json(tool_call)

        # Chat input
        if prompt := st.chat_input("Ask a question..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    # Make API request (using the regular chat endpoint for now)
                    # TODO: Update to use workspace-specific endpoint when available
                    chat_data = {
                        "message": prompt,
                        "session_id": st.session_state.current_session_id,
                        "workspace_id": st.session_state.selected_workspace,
                        "agent_id": st.session_state.selected_agent
                    }

                    # Chat endpoint is at root level, not under /v1
                    chat_url = "http://localhost:8058/chat"
                    try:
                        response = requests.post(chat_url, json=chat_data)
                        if response.status_code == 200:
                            result = {"success": True, "data": response.json()}
                        else:
                            result = {"success": False, "error": response.json().get("detail", response.text)}
                    except Exception as e:
                        result = {"success": False, "error": str(e)}

                    if result.get("success"):
                        response_data = result["data"]
                        response_text = response_data.get("message", "No response")

                        st.markdown(response_text)

                        # Store session ID
                        if response_data.get("session_id"):
                            st.session_state.current_session_id = response_data["session_id"]

                        # Show tool usage
                        if response_data.get("tool_calls"):
                            with st.expander("🔧 Tool Usage"):
                                for tool_call in response_data["tool_calls"]:
                                    st.json(tool_call)

                        # Add assistant response to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_text,
                            "tool_calls": response_data.get("tool_calls", [])
                        })
                    else:
                        error_msg = f"❌ Error: {result.get('error')}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })

        # Show session info
        if st.session_state.current_session_id:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Session Info")
            st.sidebar.caption(f"Session ID: `{st.session_state.current_session_id[:8]}...`")
            st.sidebar.caption(f"Messages: {len(st.session_state.messages)}")
    else:
        st.info("👈 Select a workspace and agent from the sidebar to start chatting")


# ==========================================
# HEALTH PAGE
# ==========================================
elif page == "🏥 Health":
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
