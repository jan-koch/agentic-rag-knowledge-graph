"""
Multi-Tenant RAG Admin Dashboard

A Streamlit-based web UI for managing organizations, workspaces, agents, and API keys.
"""

import streamlit as st
import requests
import json
import os
import asyncio
import glob
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

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


def find_documents(directory: str = "documents") -> List[str]:
    """Find all markdown and text files in directory."""
    if not os.path.exists(directory):
        return []

    patterns = ["*.md", "*.markdown", "*.txt"]
    files = []

    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory, "**", pattern), recursive=True))

    return sorted(files)


async def ingest_documents_for_workspace(workspace_id: str, documents_folder: str, clean: bool = False):
    """
    Ingest documents for a specific workspace.

    Args:
        workspace_id: UUID of the workspace
        documents_folder: Path to documents folder
        clean: Whether to clean existing data first

    Returns:
        Dict with ingestion results
    """
    try:
        # Import ingestion module
        import sys
        sys.path.insert(0, str(Path(__file__).parent))

        from ingestion.ingest import DocumentIngestionPipeline, IngestionConfig

        # Create configuration
        config = IngestionConfig(
            chunk_size=1000,
            chunk_overlap=200,
            use_semantic_chunking=True,
            extract_entities=True,
            skip_graph_building=False
        )

        # Create pipeline
        pipeline = DocumentIngestionPipeline(
            config=config,
            documents_folder=documents_folder,
            clean_before_ingest=clean,
            workspace_id=workspace_id
        )

        # Run ingestion
        results = await pipeline.ingest_documents()
        await pipeline.close()

        # Calculate summary
        total_chunks = sum(r.chunks_created for r in results)
        total_entities = sum(r.entities_extracted for r in results)
        total_errors = sum(len(r.errors) for r in results)

        return {
            "success": True,
            "documents_processed": len(results),
            "total_chunks": total_chunks,
            "total_entities": total_entities,
            "total_errors": total_errors,
            "results": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Sidebar navigation
st.sidebar.markdown("# 🤖 Multi-Tenant RAG")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🏢 Organizations", "📁 Workspaces", "🤖 Agents", "🔑 API Keys", "🔌 Widget Embed", "💬 Chat", "🏥 Health"]
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

                                # Document ingestion section
                                with st.expander("📤 Ingest Documents", expanded=False):
                                    # Find available documents
                                    doc_folder = st.text_input(
                                        "Documents Folder",
                                        value="documents",
                                        key=f"doc_folder_{ws['id']}",
                                        help="Path to the folder containing documents to ingest"
                                    )

                                    available_docs = find_documents(doc_folder)

                                    if available_docs:
                                        st.success(f"✅ Found {len(available_docs)} document(s)")
                                        with st.expander("📄 View Files", expanded=False):
                                            for doc in available_docs:
                                                st.caption(f"• {os.path.relpath(doc, doc_folder)}")

                                        col_ing1, col_ing2 = st.columns(2)

                                        with col_ing1:
                                            clean_mode = st.checkbox(
                                                "Clean before ingest",
                                                key=f"clean_{ws['id']}",
                                                help="Remove existing documents before ingesting new ones"
                                            )

                                        with col_ing2:
                                            if st.button(
                                                "🚀 Start Ingestion",
                                                key=f"start_ingest_{ws['id']}",
                                                type="primary"
                                            ):
                                                with st.spinner("Ingesting documents... This may take a few minutes."):
                                                    # Run ingestion in async context
                                                    result = asyncio.run(
                                                        ingest_documents_for_workspace(
                                                            workspace_id=ws['id'],
                                                            documents_folder=doc_folder,
                                                            clean=clean_mode
                                                        )
                                                    )

                                                    if result.get("success"):
                                                        st.success("✅ Ingestion completed!")
                                                        st.markdown(f"""
                                                        **Summary:**
                                                        - Documents processed: {result['documents_processed']}
                                                        - Total chunks: {result['total_chunks']}
                                                        - Entities extracted: {result['total_entities']}
                                                        - Errors: {result['total_errors']}
                                                        """)

                                                        # Show detailed results
                                                        if result.get('results'):
                                                            with st.expander("📊 Detailed Results"):
                                                                for doc_result in result['results']:
                                                                    status = "✅" if not doc_result.errors else "⚠️"
                                                                    st.markdown(f"{status} **{doc_result.title}**")
                                                                    st.caption(f"Chunks: {doc_result.chunks_created} | Entities: {doc_result.entities_extracted}")
                                                                    if doc_result.errors:
                                                                        for error in doc_result.errors:
                                                                            st.error(f"Error: {error}")

                                                        # Refresh to update document count
                                                        st.info("💡 Refresh the page to see updated document counts")
                                                    else:
                                                        st.error(f"❌ Ingestion failed: {result.get('error')}")
                                    else:
                                        st.warning(f"⚠️ No documents found in `{doc_folder}`")
                                        st.caption("Supported formats: .md, .markdown, .txt")

                                action_col1, action_col2 = st.columns(2)
                                with action_col1:
                                    if st.button("📊 View Full Details", key=f"view_{ws['id']}"):
                                        st.json(ws)
                                with action_col2:
                                    if st.button("🔄 Refresh", key=f"refresh_{ws['id']}"):
                                        st.rerun()

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

    # Fetch organizations and workspaces for dropdown
    orgs_result = api_request("GET", "/organizations")
    workspace_options = {}
    workspace_to_org = {}

    if orgs_result.get("success") and orgs_result["data"]:
        for org in orgs_result["data"]:
            ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")
            if ws_result.get("success") and ws_result["data"]:
                for ws in ws_result["data"]:
                    label = f"{ws['name']} ({ws['slug']}) - {org['name']}"
                    workspace_options[label] = ws['id']
                    workspace_to_org[ws['id']] = {
                        'org_name': org['name'],
                        'org_slug': org['slug'],
                        'plan_tier': org['plan_tier']
                    }

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Create New API Key")
        with st.form("create_api_key_form"):
            if workspace_options:
                selected_workspace = st.selectbox(
                    "Select Workspace",
                    options=list(workspace_options.keys()),
                    help="Choose which workspace this API key belongs to"
                )
                key_ws_id = workspace_options[selected_workspace]

                # Show organization context
                org_info = workspace_to_org.get(key_ws_id, {})
                st.caption(f"Organization: {org_info.get('org_name', 'Unknown')} ({org_info.get('plan_tier', 'free').upper()})")
                st.caption(f"Workspace ID: `{key_ws_id}`")
            else:
                st.warning("⚠️ No workspaces found. Create a workspace first!")
                key_ws_id = st.text_input("Workspace ID (manual)", placeholder="uuid")

            key_name = st.text_input("Key Name", placeholder="Production Key")

            col_a, col_b = st.columns(2)
            with col_a:
                key_scopes = st.multiselect(
                    "Scopes",
                    ["chat", "search", "ingest", "admin"],
                    default=["chat", "search"],
                    help="Permissions for this API key"
                )
            with col_b:
                key_rate_limit = st.number_input("Rate Limit (requests/min)", value=60, min_value=1, max_value=1000)

            key_expires = st.checkbox("Set expiration date")
            key_expires_at = None
            if key_expires:
                key_expires_at = st.date_input("Expires at")

            if st.form_submit_button("Create API Key", type="primary"):
                if not key_ws_id:
                    st.error("❌ Please select a workspace")
                else:
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
                        <strong>Created:</strong> {key_data['created_at']}
                        </div>
                        """, unsafe_allow_html=True)

                        # Provide quick action to use this key in widget embed
                        st.markdown("---")
                        st.markdown("### ⚡ Quick Actions")
                        col_action1, col_action2 = st.columns(2)
                        with col_action1:
                            # Create URL with API key parameter
                            widget_url = f"?api_key={key_data['key']}"
                            st.link_button(
                                "🔌 Use in Widget Embed",
                                url=widget_url,
                                help="Navigate to Widget Embed page with this API key pre-filled",
                                use_container_width=True,
                                type="primary"
                            )
                        with col_action2:
                            st.caption("💡 The API key will be automatically filled in the widget embed code")
                    else:
                        st.error(f"❌ Failed to create API key: {result.get('error')}")

    with col2:
        st.markdown("### Quick Info")
        st.info("""
        **API Key Features:**
        - Organization-scoped authentication
        - Per-workspace isolation
        - Customizable rate limits
        - Scope-based permissions
        - Optional expiration dates

        **Usage:**
        ```bash
        curl -H "Authorization: Bearer YOUR_KEY" \\
             https://api.example.com/v1/chat
        ```
        """)

    st.markdown("---")
    st.markdown("### API Keys by Organization")

    if orgs_result.get("success") and orgs_result["data"]:
        for org in orgs_result["data"]:
            with st.expander(f"🏢 {org['name']} ({org['plan_tier'].upper()})", expanded=False):
                ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")

                if ws_result.get("success") and ws_result["data"]:
                    for ws in ws_result["data"]:
                        st.markdown(f"#### 📁 {ws['name']} ({ws['slug']})")

                        # Fetch API keys for this workspace
                        keys_result = api_request("GET", f"/workspaces/{ws['id']}/api-keys")

                        if keys_result.get("success") and keys_result["data"]:
                            for key in keys_result["data"]:
                                col_k1, col_k2, col_k3, col_k4 = st.columns([3, 2, 2, 1])

                                with col_k1:
                                    st.markdown(f"**{key['name']}**")
                                    st.caption(f"Prefix: `{key['key_prefix']}...`")

                                with col_k2:
                                    scopes_str = ", ".join(key.get('scopes', []))
                                    st.caption(f"Scopes: {scopes_str}")

                                with col_k3:
                                    if key.get('is_active'):
                                        st.success("✅ Active")
                                    else:
                                        st.error("❌ Revoked")

                                    if key.get('last_used_at'):
                                        st.caption(f"Last used: {format_datetime(key['last_used_at'])}")
                                    else:
                                        st.caption("Never used")

                                with col_k4:
                                    if key.get('is_active') and st.button("🗑️", key=f"revoke_{key['id']}", help="Revoke this key"):
                                        revoke_result = api_request("DELETE", f"/workspaces/{ws['id']}/api-keys/{key['id']}")
                                        if revoke_result.get("success"):
                                            st.success("Key revoked")
                                            st.rerun()
                                        else:
                                            st.error("Failed to revoke")

                                st.markdown("---")
                        else:
                            st.info("No API keys created for this workspace")
                            st.caption(f"Create one above by selecting workspace '{ws['name']}'")
                else:
                    st.info("No workspaces in this organization")
    else:
        st.info("No organizations found. Create an organization first!")


# ==========================================
# WIDGET EMBED PAGE
# ==========================================
elif page == "🔌 Widget Embed":
    st.markdown('<div class="section-header">Widget Embed Code Generator</div>', unsafe_allow_html=True)

    st.info("💡 Generate embeddable chat widgets for your agents. Choose an agent and copy the embed code to add a chat interface to any website.")

    # Fetch organizations, workspaces, and agents
    orgs_result = api_request("GET", "/organizations")
    agent_options = {}
    agent_details = {}

    if orgs_result.get("success") and orgs_result["data"]:
        for org in orgs_result["data"]:
            ws_result = api_request("GET", f"/organizations/{org['id']}/workspaces")
            if ws_result.get("success") and ws_result["data"]:
                for ws in ws_result["data"]:
                    agents_result = api_request("GET", f"/workspaces/{ws['id']}/agents")
                    if agents_result.get("success") and agents_result["data"]:
                        for agent in agents_result["data"]:
                            if agent['is_active']:
                                label = f"{agent['name']} - {ws['name']} ({org['name']})"
                                agent_options[label] = agent['id']
                                agent_details[agent['id']] = {
                                    'agent_id': agent['id'],
                                    'agent_name': agent['name'],
                                    'agent_slug': agent['slug'],
                                    'workspace_id': ws['id'],
                                    'workspace_name': ws['name'],
                                    'workspace_slug': ws['slug'],
                                    'org_id': org['id'],
                                    'org_name': org['name'],
                                    'org_slug': org['slug'],
                                    'plan_tier': org['plan_tier']
                                }

    if agent_options:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Select Agent")
            selected_agent_label = st.selectbox(
                "Choose an agent to generate embed code",
                options=list(agent_options.keys())
            )

            selected_agent_id = agent_options[selected_agent_label]
            details = agent_details[selected_agent_id]

            st.markdown(f"""
            <div class="info-card">
            <strong>Agent:</strong> {details['agent_name']}<br>
            <strong>Workspace:</strong> {details['workspace_name']}<br>
            <strong>Organization:</strong> {details['org_name']} ({details['plan_tier'].upper()})<br>
            <strong>Agent ID:</strong> <code>{details['agent_id']}</code><br>
            <strong>Workspace ID:</strong> <code>{details['workspace_id']}</code>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("### Customization")
            custom_greeting = st.text_input("Custom greeting (optional)",
                                            placeholder=f"Hi! I'm {details['agent_name']}. How can I help?")

        st.markdown("---")
        st.markdown("### 📋 Floating Widget Embed Code")

        # Check for API key passed via URL parameter
        query_params = st.query_params
        prefilled_api_key = query_params.get("api_key", None)

        if not prefilled_api_key:
            st.warning("⚠️ Floating widget requires an API key. Generate one in the API Keys page first.")
        else:
            st.success("✅ API key pre-filled! You can copy the complete embed code below.")

        # Determine API base URL - use production URL for widget embeds
        api_base_url = os.getenv("API_BASE_URL", "https://botapi.kobra-dataworks.de")

        # Fetch API keys for the workspace
        keys_result = api_request("GET", f"/workspaces/{details['workspace_id']}/api-keys")

        if keys_result.get("success") and keys_result["data"]:
            active_keys = [k for k in keys_result["data"] if k.get('is_active')]

            if active_keys:
                key_options = {f"{k['name']} ({k['key_prefix']}...)": k['key_prefix'] for k in active_keys}
                selected_key_label = st.selectbox("Select API Key", list(key_options.keys()))

                # Use prefilled key if available, otherwise show placeholder
                if prefilled_api_key:
                    api_key_value = prefilled_api_key
                    st.info("🔒 Note: Your API key is embedded in the code below. Keep it secure!")
                else:
                    api_key_value = 'YOUR_API_KEY_HERE'
                    st.info("🔒 Note: Replace 'YOUR_API_KEY_HERE' with your actual API key. The key is only shown once at creation time.")

                # Escape values for JavaScript to prevent XSS
                greeting_value = custom_greeting or f"Hallo! Ich bin {details['agent_name']}. Wie kann ich Ihnen helfen?"
                agent_name_safe = json.dumps(details['agent_name'])[1:-1]  # Remove outer quotes
                greeting_safe = json.dumps(greeting_value)[1:-1]  # Remove outer quotes

                floating_code = f"""<!-- {details['agent_name']} Floating Chat Widget -->
<script>
  window.RAG_CHAT_CONFIG = {{
    apiKey: '{api_key_value}',{' // ✅ Pre-filled' if prefilled_api_key else ' // Replace with actual API key'}
    workspaceId: '{details['workspace_id']}',
    agentId: '{details['agent_id']}',
    agentName: '{agent_name_safe}',
    greeting: '{greeting_safe}',
    language: 'de', // 'de' for German, 'en' for English
    position: 'bottom-right',
    theme: 'light'
  }};
</script>
<script src="{api_base_url}/static/chat-widget-secure.js"></script>"""

                st.code(floating_code, language="html")

                with st.expander("📖 Usage Instructions"):
                    st.markdown("""
                    **How to use this floating widget:**
                    1. Generate an API key in the **🔑 API Keys** page
                    2. Replace `YOUR_API_KEY_HERE` with your actual API key
                    3. Paste the code before the closing `</body>` tag of your website
                    4. A floating chat button will appear in the bottom right corner
                    5. Users can click to open/close the chat

                    **Security:**
                    - Keep your API key private
                    - Use domain restrictions if available
                    - Monitor usage in the dashboard
                    - Rotate keys regularly
                    """)

                st.markdown("---")
                st.markdown("### 🔑 Need an API Key?")
                if st.button("→ Go to API Keys Page"):
                    st.info("Navigate to '🔑 API Keys' in the sidebar to generate a key")
            else:
                st.warning("No active API keys found for this workspace.")
                st.info("Create an API key in the **🔑 API Keys** page to use the floating widget.")
        else:
            st.error("Could not fetch API keys. Please check the workspace configuration.")

        st.markdown("---")
        st.markdown("### 🎨 Preview")

        # Show a mockup preview of the floating widget
        st.markdown("""
        <div style="position: relative; width: 100%; height: 400px; border: 2px solid #ddd;
             border-radius: 8px; background: #f5f5f5; overflow: hidden;">
            <div style="position: absolute; bottom: 20px; right: 20px; width: 60px; height: 60px;
                 border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: flex; align-items: center;
                 justify-content: center; color: white; font-size: 24px; cursor: pointer;">
                💬
            </div>
            <div style="position: absolute; bottom: 90px; right: 20px; background: white;
                 border-radius: 8px; padding: 12px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                 max-width: 200px;">
                <p style="margin: 0; font-size: 14px; color: #333;">
                Chat with us! 👋
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### ⚙️ Advanced Configuration")

        with st.expander("🎨 Theming & Styling"):
            st.markdown("""
            **Custom CSS:**
            You can customize the widget appearance by adding CSS to your page:

            ```css
            /* Customize widget colors */
            .chat-widget {
                --primary-color: #667eea;
                --text-color: #333;
                --bg-color: #ffffff;
            }
            ```

            **Available Options:**
            - Primary color
            - Background color
            - Font family
            - Border radius
            - Shadow effects
            """)

        with st.expander("🔧 JavaScript API"):
            st.markdown(f"""
            **Control the widget programmatically:**

            ```javascript
            // Open the chat widget
            window.RagChatWidget.open();

            // Close the chat widget
            window.RagChatWidget.close();

            // Toggle the chat widget
            window.RagChatWidget.toggle();

            // Check if widget is open
            if (window.RagChatWidget.isOpen()) {{
                console.log('Widget is open');
            }}

            // Reload the widget
            window.RagChatWidget.reload();
            ```
            """)

        with st.expander("🌐 Multiple Agents"):
            st.markdown("""
            **Need multiple agents on one page?**

            You can embed multiple chat widgets by:
            1. Using different iframe containers
            2. Assigning unique IDs to each widget
            3. Specifying different agent IDs

            Example:
            ```html
            <div id="support-agent">
                <!-- Support agent iframe -->
            </div>

            <div id="sales-agent">
                <!-- Sales agent iframe -->
            </div>
            ```
            """)

    else:
        st.warning("No active agents found. Create an agent first to generate embed codes.")
        st.markdown("""
        ### Getting Started
        1. **Create an Organization** in the Organizations page
        2. **Create a Workspace** under your organization
        3. **Create an Agent** with your desired configuration
        4. **Generate an API Key** (for floating widgets)
        5. Come back here to generate your embed code!
        """)


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
