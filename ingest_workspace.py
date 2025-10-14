#!/usr/bin/env python3
"""
Quick workspace-aware document ingestion script.

Usage:
    python ingest_workspace.py --workspace-id <uuid> --directory documents/
    python ingest_workspace.py --workspace-id <uuid> --file document.md
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ingestion.ingest import main as original_ingest_main


async def ingest_for_workspace(workspace_id: str, directory: str = None, file_path: str = None, clean: bool = False):
    """
    Ingest documents for a specific workspace.

    Args:
        workspace_id: UUID of the workspace
        directory: Path to directory containing documents
        file_path: Path to a single file to ingest
        clean: Whether to clean existing data first
    """
    print(f"\n🚀 Starting ingestion for workspace: {workspace_id}")
    print(f"{'=' * 60}\n")

    # Prepare arguments
    if directory:
        source = directory
        print(f"📁 Source directory: {directory}")
    elif file_path:
        source = file_path
        print(f"📄 Source file: {file_path}")
    else:
        source = "documents"
        print("📁 Using default directory: documents/")

    if clean:
        print("🧹 Clean mode: Will remove existing workspace data first")

    print()

    # Call the original ingestion main function with workspace_id argument
    try:
        # Build command-line arguments for the original main function
        import sys
        original_argv = sys.argv.copy()

        sys.argv = ['ingest']
        sys.argv.extend(['--documents', source])
        sys.argv.extend(['--workspace-id', workspace_id])
        if clean:
            sys.argv.append('--clean')

        await original_ingest_main()

        sys.argv = original_argv  # Restore original argv

        print(f"\n✅ Ingestion completed successfully for workspace {workspace_id}!")
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Ingest documents into a specific workspace",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest all files from a directory
  python ingest_workspace.py --workspace-id 518341a0-ae02-4e28-b161-11ea84a392c1 --directory documents/support/

  # Ingest a single file
  python ingest_workspace.py --workspace-id 518341a0-ae02-4e28-b161-11ea84a392c1 --file document.md

  # Clean and re-ingest
  python ingest_workspace.py --workspace-id 518341a0-ae02-4e28-b161-11ea84a392c1 --directory documents/ --clean
        """
    )

    parser.add_argument(
        "--workspace-id",
        required=True,
        help="UUID of the workspace to ingest data into"
    )

    parser.add_argument(
        "--directory",
        help="Directory containing documents to ingest (e.g., documents/support/)"
    )

    parser.add_argument(
        "--file",
        help="Single file to ingest"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean existing workspace data before ingesting"
    )

    args = parser.parse_args()

    # Validate that either directory or file is provided
    if not args.directory and not args.file:
        parser.error("Either --directory or --file must be specified")

    # Run the ingestion
    asyncio.run(ingest_for_workspace(
        workspace_id=args.workspace_id,
        directory=args.directory,
        file_path=args.file,
        clean=args.clean
    ))


if __name__ == "__main__":
    main()
