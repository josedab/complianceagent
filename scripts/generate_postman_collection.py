#!/usr/bin/env python3
"""Convert OpenAPI spec to Postman Collection v2.1 format.

Usage:
    python scripts/generate_postman_collection.py [--input path] [--output path]

Reads the OpenAPI spec (default: docs/api/openapi.json) and generates a Postman
collection JSON file suitable for import into Postman or compatible API clients.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def openapi_to_postman(spec: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAPI 3.x spec to Postman Collection v2.1 format."""
    info = spec.get("info", {})
    collection: dict[str, Any] = {
        "info": {
            "name": info.get("title", "API Collection"),
            "description": info.get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000", "type": "string"},
            {"key": "token", "value": "", "type": "string"},
        ],
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}],
        },
        "item": [],
    }

    # Group endpoints by tag
    tag_groups: dict[str, list[dict[str, Any]]] = {}

    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method in ("parameters", "summary", "description"):
                continue

            tags = operation.get("tags", ["Other"])
            tag = tags[0] if tags else "Other"

            item = _build_request_item(path, method, operation, spec)

            if tag not in tag_groups:
                tag_groups[tag] = []
            tag_groups[tag].append(item)

    # Build folder structure
    for tag_name in sorted(tag_groups.keys()):
        items = tag_groups[tag_name]
        folder: dict[str, Any] = {
            "name": tag_name,
            "item": items,
        }
        collection["item"].append(folder)

    return collection


def _build_request_item(
    path: str,
    method: str,
    operation: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any]:
    """Build a single Postman request item from an OpenAPI operation."""
    # Build URL path segments
    url_path = path.lstrip("/").split("/")

    # Build query parameters
    query_params = []
    for param in operation.get("parameters", []):
        if param.get("in") == "query":
            query_params.append({
                "key": param["name"],
                "value": "",
                "description": param.get("description", ""),
                "disabled": not param.get("required", False),
            })

    item: dict[str, Any] = {
        "name": operation.get("summary", f"{method.upper()} {path}"),
        "request": {
            "method": method.upper(),
            "header": [
                {"key": "Content-Type", "value": "application/json"},
            ],
            "url": {
                "raw": "{{baseUrl}}" + path,
                "host": ["{{baseUrl}}"],
                "path": url_path,
            },
        },
    }

    if query_params:
        item["request"]["url"]["query"] = query_params

    # Add request body if present
    request_body = operation.get("requestBody", {})
    if request_body:
        json_content = request_body.get("content", {}).get("application/json", {})
        schema = json_content.get("schema", {})
        example_body = _generate_example_from_schema(schema, spec)
        if example_body:
            item["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(example_body, indent=2),
                "options": {"raw": {"language": "json"}},
            }

    # Add description
    desc = operation.get("description", "")
    if desc:
        item["request"]["description"] = desc

    return item


def _generate_example_from_schema(
    schema: dict[str, Any],
    spec: dict[str, Any],
    depth: int = 0,
) -> Any:
    """Generate an example value from a JSON Schema."""
    if depth > 5:
        return {}

    # Resolve $ref
    if "$ref" in schema:
        ref_path = schema["$ref"].replace("#/", "").split("/")
        resolved = spec
        for part in ref_path:
            resolved = resolved.get(part, {})
        schema = resolved

    if "example" in schema:
        return schema["example"]

    schema_type = schema.get("type", "object")

    if schema_type == "object":
        result = {}
        for prop_name, prop_schema in schema.get("properties", {}).items():
            result[prop_name] = _generate_example_from_schema(prop_schema, spec, depth + 1)
        return result
    elif schema_type == "array":
        items = schema.get("items", {})
        return [_generate_example_from_schema(items, spec, depth + 1)]
    elif schema_type == "string":
        fmt = schema.get("format", "")
        if fmt == "email":
            return "user@example.com"
        if fmt == "uuid":
            return "00000000-0000-0000-0000-000000000000"
        if fmt in ("date-time", "date"):
            return "2024-01-01T00:00:00Z"
        if fmt == "uri":
            return "https://example.com"
        return schema.get("default", "string")
    elif schema_type == "integer":
        return schema.get("default", 0)
    elif schema_type == "number":
        return schema.get("default", 0.0)
    elif schema_type == "boolean":
        return schema.get("default", False)

    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Postman collection from OpenAPI spec")
    parser.add_argument(
        "--input",
        default="docs/api/openapi.json",
        help="Path to OpenAPI spec (default: docs/api/openapi.json)",
    )
    parser.add_argument(
        "--output",
        default="docs/api/postman_collection.json",
        help="Output Postman collection path (default: docs/api/postman_collection.json)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ OpenAPI spec not found: {input_path}", file=sys.stderr)
        return 1

    spec = json.loads(input_path.read_text())
    collection = openapi_to_postman(spec)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(collection, indent=2))

    # Summary
    total_requests = sum(len(folder.get("item", [])) for folder in collection["item"])
    print(f"✅ Postman collection generated: {output_path}")
    print(f"   Folders: {len(collection['item'])}")
    print(f"   Requests: {total_requests}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
