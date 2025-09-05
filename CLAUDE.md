# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 Essential Commands

### Development Environment Setup
- **Virtual environment**: `python -m venv venv && source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- **Install dependencies**: `pip install -r requirements.txt`
- **Docker setup**: `./scripts/docker-setup.sh` (sets up PostgreSQL + Neo4j containers)
- **Alternative manual database setup**: Execute SQL in `sql/schema.sql` (adjust embedding dimensions for your model)

### Docker Database Management
- **Start databases**: `docker compose up -d` (PostgreSQL on 5432, Neo4j on 7474/7687)
- **Stop databases**: `docker compose down`
- **View logs**: `docker compose logs -f [postgres|neo4j]`
- **Restart databases**: `docker compose restart`
- **Remove volumes/reset**: `docker compose down -v` (⚠️ destroys all data)

### Running the System
- **Document ingestion**: `python -m ingestion.ingest` (required first step)
- **Clean and re-ingest**: `python -m ingestion.ingest --clean`
- **Start API server**: `python -m agent.api` (defaults to port 8058)
- **CLI interface**: `python cli.py` (connects to API at 127.0.0.1:8058)

### Testing and Quality
- **Run all tests**: `pytest` (58 tests, >80% coverage required)
- **Run with coverage**: `pytest --cov=agent --cov=ingestion --cov-report=html`
- **Run specific test modules**: `pytest tests/agent/` or `pytest tests/ingestion/`
- **Test markers available**: `-m "not slow"`, `-m integration`, `-m unit`

## 🏗 Architecture Overview

This is a hybrid RAG system combining vector search with knowledge graphs, built on:

**Core Stack**: Python 3.11+ with Pydantic AI agents, FastAPI, PostgreSQL+pgvector, Neo4j+Graphiti

**Key Components**:
- `/agent/` - Pydantic AI agent system with tools, providers, and FastAPI API
- `/ingestion/` - Document processing pipeline with semantic chunking and graph building  
- `/tests/` - Comprehensive test suite with mocks for external dependencies
- `/cli.py` - Interactive CLI with tool usage visibility and streaming responses

**Agent Tools**: The system provides vector_search, graph_search, hybrid_search, document retrieval, and entity relationship tools. Tool selection is controlled by prompts in `agent/prompts.py`.

**Provider System**: Flexible LLM support for OpenAI, Ollama, OpenRouter, and Gemini via `agent/providers.py`. Uses separate models for chat vs ingestion (configurable via `LLM_CHOICE` and `INGESTION_LLM_CHOICE`).

**Database Architecture**: 
- PostgreSQL stores documents, chunks with embeddings, sessions, and messages
- Neo4j (via Graphiti) stores temporal knowledge graph with entities and relationships  
- Both use OpenAI-compatible client configuration for consistent API interfaces
- **Docker Setup**: Automated with `./scripts/docker-setup.sh` - includes health checks and connection verification

## 📁 Key File Locations

- **Agent configuration**: `agent/prompts.py` controls tool selection behavior
- **Database utilities**: `agent/db_utils.py` (PostgreSQL) and `agent/graph_utils.py` (Neo4j/Graphiti)
- **Data models**: `agent/models.py` with Pydantic validation and ToolCall tracking
- **Environment config**: `.env` (created from `.env.example`) with Docker database URLs pre-configured
- **Database schema**: `sql/schema.sql` with pgvector setup (copied to `docker/postgres/init.sql`)
- **Docker configuration**: `docker-compose.yml` and `scripts/docker-setup.sh` for containerized databases

### 🔄 Project Awareness & Context
- **Always read `PLANNING.md`** at the start of a new conversation to understand the project's architecture, goals, style, and constraints.
- **Check `TASK.md`** before starting a new task. If the task isn’t listed, add it with a brief description and today's date.
- **Use consistent naming conventions, file structure, and architecture patterns** as described in `PLANNING.md`.

### 🧱 Code Structure & Modularity
- **Never create a file longer than 500 lines of code.** If a file approaches this limit, refactor by splitting it into modules or helper files.
- **Organize code into clearly separated modules**, grouped by feature or responsibility.
- **Use clear, consistent imports** (prefer relative imports within packages).

### 🧪 Testing & Reliability
- **Always create Pytest unit tests for new features** (functions, classes, routes, etc).
- **After updating any logic**, check whether existing unit tests need to be updated. If so, do it.
- **Tests should live in a `/tests` folder** mirroring the main app structure.
  - Include at least:
    - 1 test for expected use
    - 1 edge case
    - 1 failure case
- When testing, always activate the virtual environment in venv_linux and run python commands with 'python3'

### 🔌 MCP Server Usage

#### Crawl4AI RAG MCP Server
- **Use for external documentation**: Get docs for Pydantic AI
- **Always check available sources first**: Use `get_available_sources` to see what's crawled.
- **Code examples**: Use `search_code_examples` when looking for implementation patterns.

#### Neon MCP Server  
- **Database project management**: Use `create_project` to create new Neon database projects.
- **Execute SQL**: Use `run_sql` to execute schema and data operations.
- **Table management**: Use `get_database_tables` and `describe_table_schema` for inspection.
- **Always specify project ID**: Pass the project ID to all database operations.
- **Example workflow**:
  1. `create_project` - create new database project
  2. `run_sql` with schema SQL - set up tables
  3. `get_database_tables` - verify schema creation
  4. Use returned connection string for application config


### ✅ Task Completion
- **Mark completed tasks in `TASK.md`** immediately after finishing them.
- Add new sub-tasks or TODOs discovered during development to `TASK.md` under a “Discovered During Work” section.

### 📎 Style & Conventions
- **Use Python** as the primary language.
- **Follow PEP8**, use type hints, and format with `black`.
- **Use `pydantic` for data validation**.
- Use `FastAPI` for APIs and `SQLAlchemy` or `SQLModel` for ORM if applicable.
- Write **docstrings for every function** using the Google style:
  ```python
  def example():
      """
      Brief summary.

      Args:
          param1 (type): Description.

      Returns:
          type: Description.
      """
  ```

### 📚 Documentation & Explainability
- **Update `README.md`** when new features are added, dependencies change, or setup steps are modified.
- **Comment non-obvious code** and ensure everything is understandable to a mid-level developer.
- When writing complex logic, **add an inline `# Reason:` comment** explaining the why, not just the what.

### 🧠 AI Behavior Rules
- **Never assume missing context. Ask questions if uncertain.**
- **Never hallucinate libraries or functions** – only use known, verified Python packages.
- **Always confirm file paths and module names** exist before referencing them in code or tests.
- **Never delete or overwrite existing code** unless explicitly instructed to or if part of a task from `TASK.md`.