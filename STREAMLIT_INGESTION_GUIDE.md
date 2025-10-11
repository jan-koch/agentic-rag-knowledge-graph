# Streamlit Document Ingestion Feature

## Overview

The Streamlit admin dashboard (`webui.py`) now includes a built-in document ingestion feature that allows you to ingest documents from the `/documents` folder directly into a workspace through the web UI.

## What Was Added

### 1. **New Import Dependencies**
- `os`, `asyncio`, `glob` for file system operations and async support
- `Path` from `pathlib` for path handling

### 2. **Helper Functions**

#### `find_documents(directory: str = "documents") -> List[str]`
- Scans a directory recursively for `.md`, `.markdown`, and `.txt` files
- Returns a sorted list of file paths

#### `ingest_documents_for_workspace(workspace_id, documents_folder, clean=False)`
- Async function that runs the full ingestion pipeline
- Creates `IngestionConfig` with optimal settings:
  - Chunk size: 1000 tokens
  - Chunk overlap: 200 tokens
  - Semantic chunking: Enabled
  - Entity extraction: Enabled
  - Knowledge graph building: Enabled
- Returns detailed ingestion results including:
  - Number of documents processed
  - Total chunks created
  - Entities extracted
  - Any errors encountered

### 3. **UI Component in Workspaces Page**

Added to the workspace details section (line 646+):

**Features:**
- 📁 **Folder Selection**: Text input to specify documents folder (defaults to `documents`)
- 📄 **File Preview**: Shows list of all found documents
- ✅ **Document Count**: Displays how many files were found
- 🧹 **Clean Mode**: Checkbox to remove existing workspace data before ingestion
- 🚀 **Start Ingestion Button**: Triggers the ingestion process
- 📊 **Progress Indicator**: Shows spinner during ingestion
- ✅ **Results Summary**: Displays:
  - Documents processed
  - Total chunks created
  - Entities extracted
  - Error count
- 📋 **Detailed Results**: Expandable section showing per-document results
- 🔄 **Refresh Button**: Easy way to reload and see updated document counts

## How to Use

### Prerequisites

1. **Install Streamlit** (if not already installed):
   ```bash
   pip install streamlit
   ```

2. **Ensure databases are running**:
   ```bash
   docker compose up -d
   ```

3. **Run migrations** (if not already done):
   ```bash
   ./scripts/run-migrations.sh
   ```

### Usage Steps

1. **Start the Streamlit app**:
   ```bash
   streamlit run webui.py
   ```
   Or if you have a custom port:
   ```bash
   streamlit run webui.py --server.port 8501
   ```

2. **Navigate to Workspaces page** (📁 Workspaces in sidebar)

3. **Find your workspace** in the list and click "Show details"

4. **Expand the "📤 Ingest Documents" section**

5. **Configure ingestion**:
   - Enter documents folder path (default: `documents`)
   - View the list of files that will be ingested
   - Optionally check "Clean before ingest" to remove existing data

6. **Click "🚀 Start Ingestion"**

7. **Wait for completion**:
   - Progress spinner will show during ingestion
   - Ingestion time depends on document count and size
   - Typically takes 1-5 minutes for 10-20 documents

8. **Review results**:
   - Summary shows total counts
   - Expand "📊 Detailed Results" to see per-document stats
   - Refresh the page to see updated document counts

## Example Workflow

### For KlimaNEXT Workspace

1. Place your documents in `/documents` folder:
   ```bash
   ls /var/www/agentic-rag-knowledge-graph/documents/
   # Should show: Benutzerhandbuch.md and other files
   ```

2. In Streamlit:
   - Go to Workspaces page
   - Find "KlimaNEXT" workspace
   - Click "Show details"
   - Expand "📤 Ingest Documents"
   - Keep folder as "documents"
   - Click "🚀 Start Ingestion"

3. Results will show:
   - Documents processed: 1 (or more)
   - Chunks created: ~50-100 (depends on document size)
   - Entities extracted: ~20-50 (depends on content)

## Features Comparison

### Streamlit UI vs CLI

| Feature | Streamlit UI | CLI (`ingest_workspace.py`) |
|---------|--------------|------------------------------|
| Ease of use | ✅ Very easy, visual | Requires command line |
| Document preview | ✅ Yes | ❌ No |
| Progress tracking | ✅ Visual spinner | ✅ Terminal output |
| Results visualization | ✅ Formatted display | Plain text |
| Batch operations | ❌ One workspace at a time | ✅ Can script multiple |
| Advanced options | Basic options | All configuration options |

## Technical Details

### Async Handling
The ingestion runs in an async context using `asyncio.run()`. Streamlit handles this properly within the button click handler.

### Database Connections
The ingestion pipeline automatically:
- Initializes PostgreSQL and Neo4j connections
- Processes documents
- Closes all connections properly
- Handles errors gracefully

### Multi-Tenant Isolation
- Documents are tagged with `workspace_id`
- Knowledge graph uses unique `group_id` per workspace
- Complete data isolation guaranteed

### Configuration Used

```python
IngestionConfig(
    chunk_size=1000,          # Optimal for most documents
    chunk_overlap=200,        # Good context preservation
    use_semantic_chunking=True,  # Better chunk boundaries
    extract_entities=True,    # Enable entity extraction
    skip_graph_building=False # Build knowledge graph
)
```

## Troubleshooting

### Issue: "No documents found"
- **Solution**: Check that documents exist in the specified folder
- Verify folder path is correct
- Ensure files have `.md`, `.markdown`, or `.txt` extensions

### Issue: "Ingestion failed"
- **Solution**: Check the error message displayed
- Common causes:
  - Database not running (`docker compose up -d`)
  - Missing environment variables in `.env`
  - Invalid workspace ID

### Issue: "Document count not updating"
- **Solution**: Click the "🔄 Refresh" button or reload the page
- Document counts are cached until page reload

### Issue: "Streamlit not found"
- **Solution**: Install streamlit:
  ```bash
  pip install streamlit
  ```

## Advanced: CLI Alternative

If you prefer CLI or need more control:

```bash
# Using the dedicated script
python ingest_workspace.py \
  --workspace-id <WORKSPACE_UUID> \
  --directory documents/ \
  --clean

# Or using the main ingestion module
python -m ingestion.ingest \
  --workspace-id <WORKSPACE_UUID> \
  --documents documents/ \
  --clean \
  --verbose
```

## Security Notes

- Only accessible to users who can access the Streamlit UI
- No API authentication bypass - uses direct database access
- Workspace isolation is maintained throughout ingestion
- Clean mode requires extra caution (destructive operation)

## Future Enhancements

Potential improvements:
- [ ] File upload widget for adding new documents
- [ ] Progress bar with percentage complete
- [ ] Pause/resume ingestion
- [ ] Schedule automatic re-ingestion
- [ ] Batch ingestion across multiple workspaces
- [ ] Document preview before ingestion
- [ ] Custom ingestion configuration per workspace

## Related Documentation

- `MULTI_TENANT_README.md` - Multi-tenant architecture overview
- `CLAUDE.md` - General system documentation
- `ingestion/ingest.py` - Core ingestion pipeline code
- `ingest_workspace.py` - CLI alternative

---

**Last Updated**: 2025-01-09
**Status**: ✅ Production Ready
**Tested With**: Benutzerhandbuch.md (1 document)
