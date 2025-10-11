# Testing Guide

This document provides comprehensive guidance on testing the Agentic RAG Knowledge Graph system.

## Table of Contents
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)

## Quick Start

### First Time Setup

```bash
# 1. Set up test environment
make setup-test-env

# 2. Install pre-commit hooks
make install-hooks

# 3. Run tests
make test
```

### Daily Workflow

```bash
# Quick check before committing
make check

# Run full test suite
make test

# Run tests in watch mode (during development)
make test-watch
```

## Test Structure

Our test suite is organized by module:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── agent/                   # Agent system tests
│   ├── test_db_utils.py    # Database utilities
│   └── test_models.py      # Data models
└── ingestion/              # Ingestion system tests
    └── test_chunker.py     # Document chunking
```

### Test Types

We use pytest markers to categorize tests:

- **`unit`**: Fast unit tests (< 1 second each)
- **`integration`**: Tests with external dependencies
- **`slow`**: Long-running tests
- **`smoke`**: Critical path tests
- **`e2e`**: End-to-end tests

## Running Tests

### Using Make (Recommended)

```bash
# Full test suite with coverage
make test

# Fast unit tests only (30 seconds)
make test-fast

# Integration tests
make test-integration

# Tests with HTML coverage report
make test-coverage

# Watch mode (auto-run on file changes)
make test-watch

# Test database management (on ports 5433, 7475, 7688)
make docker-test-up       # Start test databases
make docker-test-down     # Stop test databases
make docker-test-logs     # View test database logs
make docker-test-reset    # Reset test databases (removes all data)
```

### Using Scripts

```bash
# Full test suite
./scripts/run-tests.sh

# Fast tests
./scripts/run-tests-fast.sh

# Integration tests
./scripts/run-tests-integration.sh
```

### Using pytest Directly

```bash
# All tests
pytest

# Specific test file
pytest tests/agent/test_models.py

# Specific test function
pytest tests/agent/test_models.py::test_chat_request_validation

# Run with markers
pytest -m unit                  # Unit tests only
pytest -m "not slow"           # Exclude slow tests
pytest -m "unit and not slow"  # Fast unit tests

# Parallel execution
pytest -n auto                 # Use all CPU cores

# Stop on first failure
pytest -x

# Show test names without running
pytest --collect-only
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from agent.models import ChatRequest

def test_chat_request_validation():
    """Test that ChatRequest validates input correctly."""
    # Arrange
    valid_data = {
        "message": "Hello",
        "session_id": "test-123"
    }

    # Act
    request = ChatRequest(**valid_data)

    # Assert
    assert request.message == "Hello"
    assert request.session_id == "test-123"
```

### Using Fixtures

```python
@pytest.fixture
def sample_chat_request():
    """Fixture providing a sample chat request."""
    return ChatRequest(
        message="Test message",
        session_id="test-session"
    )

def test_with_fixture(sample_chat_request):
    """Test using a fixture."""
    assert sample_chat_request.message == "Test message"
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test an async function."""
    result = await some_async_function()
    assert result is not None
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, AsyncMock, patch

def test_with_mock(mock_database_pool):
    """Test using a mocked database."""
    # Mock is provided by conftest.py fixture
    mock_database_pool.acquire.return_value = Mock()
    # Your test code here
```

### Test Markers

```python
@pytest.mark.unit
def test_fast_unit():
    """Fast unit test."""
    pass

@pytest.mark.integration
@pytest.mark.slow
async def test_database_integration():
    """Slow integration test."""
    pass

@pytest.mark.smoke
def test_critical_feature():
    """Smoke test for critical functionality."""
    pass
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    """Test uppercase conversion with multiple inputs."""
    assert input.upper() == expected
```

## Coverage

### Minimum Requirements

- **Overall coverage**: ≥80%
- **New code**: ≥90% (enforced in pre-merge checks)

### Generating Coverage Reports

```bash
# Terminal report
pytest --cov=agent --cov=ingestion --cov-report=term-missing

# HTML report (opens in browser)
make test-coverage

# XML report (for CI)
pytest --cov=agent --cov=ingestion --cov-report=xml
```

### Viewing Coverage

```bash
# After running tests with coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## CI/CD Pipeline

### GitHub Actions Workflows

We have three main workflows:

#### 1. CI (Continuous Integration)
**Trigger**: Push to any branch, Pull Requests
**Jobs**:
- Test on Python 3.11 & 3.12
- Lint code
- Check coverage threshold
- Security scan

```yaml
# .github/workflows/ci.yml
```

#### 2. Pre-Merge Checks
**Trigger**: Pull Requests only
**Jobs**:
- Quality gates (strict)
- Integration tests
- PR size check
- Multi-version compatibility

```yaml
# .github/workflows/pre-merge.yml
```

#### 3. Nightly Tests
**Trigger**: Daily at 3 AM UTC, Manual dispatch
**Jobs**:
- Extended test suite (including slow tests)
- Dependency audit
- Docker health checks
- Performance benchmarks

```yaml
# .github/workflows/nightly.yml
```

### Pre-Commit Hooks

Automatically run before each commit:

```bash
# Install hooks
make install-hooks

# Hooks will run:
# 1. black - Code formatting
# 2. ruff - Linting
# 3. pytest-fast - Quick unit tests (5 seconds)
```

### CI Status Badges

Add to your README:

```markdown
![CI](https://github.com/your-org/your-repo/workflows/CI/badge.svg)
![Coverage](https://img.shields.io/codecov/c/github/your-org/your-repo)
```

## Local Development

### Setting Up Test Environment

```bash
# First time setup
./scripts/setup-test-env.sh

# This will:
# 1. Create .env.test file
# 2. Start Docker services (PostgreSQL + Neo4j) on alternative ports
#    - PostgreSQL: port 5433 (instead of 5432)
#    - Neo4j HTTP: port 7475 (instead of 7474)
#    - Neo4j Bolt: port 7688 (instead of 7687)
# 3. Initialize test database
# 4. Install test dependencies
```

#### Port Configuration

To avoid conflicts with production databases, the test environment uses alternative ports:

| Service | Production Port | Test Port | Purpose |
|---------|----------------|-----------|----------|
| PostgreSQL | 5432 | **5433** | Database server |
| Neo4j HTTP | 7474 | **7475** | Web interface |
| Neo4j Bolt | 7687 | **7688** | Graph queries |

This allows you to run both production and test databases simultaneously without conflicts.

### Database Services

The test environment uses `docker-compose.test.yml` with alternative ports:

```bash
# Start test services (on ports 5433, 7475, 7688)
docker compose -f docker-compose.test.yml up -d

# Check status
docker compose -f docker-compose.test.yml ps

# View logs
docker compose -f docker-compose.test.yml logs -f postgres
docker compose -f docker-compose.test.yml logs -f neo4j

# Stop services
docker compose -f docker-compose.test.yml down

# Reset (removes all test data)
docker compose -f docker-compose.test.yml down -v
```

**Production services** (on default ports 5432, 7474, 7687) continue to use:
```bash
docker compose up -d
docker compose down
```

### Running Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Smoke tests (critical path)
pytest -m smoke

# Everything except slow tests
pytest -m "not slow"
```

## Troubleshooting

### Tests Fail Locally

**Problem**: Tests pass in CI but fail locally

**Solution**:
```bash
# 1. Ensure test databases are running
docker compose -f docker-compose.test.yml ps

# 2. Reset test environment
docker compose -f docker-compose.test.yml down -v
./scripts/setup-test-env.sh

# 3. Reload environment variables
source .env.test

# 4. Clear cache
make clean

# 5. Re-run tests
make test
```

### Pre-Commit Hooks Fail

**Problem**: Commit is blocked by pre-commit hooks

**Solution**:
```bash
# 1. See what failed
git status

# 2. Fix issues automatically
make lint-fix
make format

# 3. Run hooks manually to verify
pre-commit run --all-files

# 4. Commit again
git commit
```

### Coverage Below Threshold

**Problem**: Coverage is below 80%

**Solution**:
```bash
# 1. Generate coverage report
make test-coverage

# 2. Open HTML report to see uncovered lines
open htmlcov/index.html

# 3. Add tests for uncovered code
# 4. Re-run tests
make test
```

### Slow Tests

**Problem**: Tests are taking too long

**Solution**:
```bash
# 1. Use parallel execution
pytest -n auto

# 2. Run only fast tests during development
make test-fast

# 3. Skip slow tests
pytest -m "not slow"

# 4. Profile slow tests
pytest --durations=10
```

### Import Errors

**Problem**: `ModuleNotFoundError` or import errors

**Solution**:
```bash
# 1. Ensure virtual environment is activated
source venv/bin/activate

# 2. Reinstall dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Verify Python path
python -c "import sys; print('\n'.join(sys.path))"
```

### Database Connection Errors

**Problem**: Can't connect to PostgreSQL or Neo4j

**Solution**:
```bash
# 1. Check if test services are running
docker compose -f docker-compose.test.yml ps

# 2. Check service health
docker compose -f docker-compose.test.yml logs postgres
docker compose -f docker-compose.test.yml logs neo4j

# 3. Restart services
docker compose -f docker-compose.test.yml restart

# 4. Verify connection (note the test ports)
pg_isready -h localhost -p 5433 -U test_user
curl http://localhost:7475
```

**Note**: If you see "port already in use" errors, make sure you're using the test compose file (`docker-compose.test.yml`) which uses alternative ports (5433, 7475, 7688) instead of production ports (5432, 7474, 7687).

## Best Practices

### DO ✅

- Write tests for all new features
- Keep tests isolated and independent
- Use descriptive test names
- Mock external dependencies
- Run tests before committing
- Keep tests fast (<1 second each)
- Use fixtures for common setup
- Test edge cases and error conditions

### DON'T ❌

- Don't commit without running tests
- Don't skip failing tests
- Don't use real API keys in tests
- Don't rely on external services
- Don't write tests that depend on each other
- Don't ignore coverage warnings
- Don't use print statements (use logging)

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py documentation](https://coverage.readthedocs.io/)
- [GitHub Actions documentation](https://docs.github.com/en/actions)

## Getting Help

If you encounter issues:

1. Check this documentation
2. Review test logs: `pytest -v --tb=short`
3. Check CI logs on GitHub
4. Run tests with debug mode: `pytest -vv --pdb`

---

**Last Updated**: 2025-01-11
**Maintained By**: Development Team
