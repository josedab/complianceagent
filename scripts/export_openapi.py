#!/usr/bin/env python3
"""Export the full OpenAPI specification from the FastAPI app.

Usage:
    python scripts/export_openapi.py [--output path]

Outputs:
    openapi.json — Full OpenAPI 3.1 specification for all endpoints.
    Can be used for SDK auto-generation, documentation, and conformance testing.
"""

import argparse
import json
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Export OpenAPI spec")
    parser.add_argument("--output", default="openapi.json", help="Output file path")
    args = parser.parse_args()

    # Import the FastAPI app
    from app.main import app

    # Generate the OpenAPI schema
    schema = app.openapi()

    # Write to file
    output_path = Path(args.output)
    output_path.write_text(json.dumps(schema, indent=2, default=str))

    # Print summary
    paths = schema.get("paths", {})
    tags = schema.get("tags", [])
    print(f"✅ OpenAPI spec exported to {output_path}")
    print(f"   Paths: {len(paths)}")
    print(f"   Tags: {len(tags)}")
    print(f"   Title: {schema.get('info', {}).get('title', 'N/A')}")
    print(f"   Version: {schema.get('info', {}).get('version', 'N/A')}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
