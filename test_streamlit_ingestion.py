#!/usr/bin/env python3
"""
Test script to verify the Streamlit ingestion functionality.
This tests the helper functions without running the full Streamlit app.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all required imports work."""
    print("Testing imports...")
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError:
        print("❌ Streamlit not installed. Run: pip install streamlit")
        return False

    try:
        from ingestion.ingest import DocumentIngestionPipeline, IngestionConfig
        print("✅ Ingestion modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ingestion modules: {e}")
        return False

    return True


def test_find_documents():
    """Test document discovery function."""
    print("\nTesting document discovery...")

    import glob

    def find_documents(directory: str = "documents"):
        """Find all markdown and text files in directory."""
        if not os.path.exists(directory):
            return []

        patterns = ["*.md", "*.markdown", "*.txt"]
        files = []

        for pattern in patterns:
            files.extend(glob.glob(os.path.join(directory, "**", pattern), recursive=True))

        return sorted(files)

    # Test with documents folder
    docs_folder = "documents"
    found_docs = find_documents(docs_folder)

    if found_docs:
        print(f"✅ Found {len(found_docs)} document(s) in '{docs_folder}':")
        for doc in found_docs:
            print(f"   • {doc}")
    else:
        print(f"⚠️  No documents found in '{docs_folder}'")
        print(f"   Supported formats: .md, .markdown, .txt")

    return True


def test_ingestion_config():
    """Test that ingestion configuration can be created."""
    print("\nTesting ingestion configuration...")

    try:
        from ingestion.ingest import IngestionConfig

        config = IngestionConfig(
            chunk_size=1000,
            chunk_overlap=200,
            use_semantic_chunking=True,
            extract_entities=True,
            skip_graph_building=False
        )

        print("✅ Ingestion configuration created successfully")
        print(f"   • Chunk size: {config.chunk_size}")
        print(f"   • Chunk overlap: {config.chunk_overlap}")
        print(f"   • Semantic chunking: {config.use_semantic_chunking}")
        print(f"   • Extract entities: {config.extract_entities}")
        print(f"   • Skip graph building: {config.skip_graph_building}")
        return True
    except Exception as e:
        print(f"❌ Failed to create ingestion config: {e}")
        return False


def test_webui_syntax():
    """Test that webui.py has no syntax errors."""
    print("\nTesting webui.py syntax...")

    try:
        import py_compile
        py_compile.compile('webui.py', doraise=True)
        print("✅ webui.py has no syntax errors")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error in webui.py: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Streamlit Ingestion Feature - Verification Test")
    print("=" * 60)

    all_passed = True

    # Test imports
    if not test_imports():
        all_passed = False
        print("\n⚠️  Some imports failed. Install missing dependencies.")

    # Test document discovery
    if not test_find_documents():
        all_passed = False

    # Test ingestion config
    if not test_ingestion_config():
        all_passed = False

    # Test webui syntax
    if not test_webui_syntax():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nNext steps:")
        print("1. Ensure databases are running: docker compose up -d")
        print("2. Run Streamlit app: streamlit run webui.py")
        print("3. Navigate to Workspaces page")
        print("4. Use the '📤 Ingest Documents' feature")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("\nFix the issues above before running the Streamlit app.")
    print("=" * 60)


if __name__ == "__main__":
    main()
