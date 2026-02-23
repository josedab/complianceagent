#!/usr/bin/env python3
"""Validate that every service's __init__.py exports match its models and service class.

Usage:
    python scripts/validate_service_exports.py

Checks:
1. Every service directory has __init__.py
2. Every __init__.py has __all__
3. All model classes/enums from models.py are in __all__
4. The service class from service.py is in __all__
"""

import ast
import sys
from pathlib import Path


def get_public_names(filepath: Path) -> set[str]:
    """Extract public class/enum names from a Python file."""
    if not filepath.exists():
        return set()
    try:
        tree = ast.parse(filepath.read_text())
    except SyntaxError:
        return set()
    
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            names.add(node.name)
    return names


def get_all_exports(filepath: Path) -> set[str] | None:
    """Extract __all__ list from __init__.py."""
    if not filepath.exists():
        return None
    try:
        tree = ast.parse(filepath.read_text())
    except SyntaxError:
        return None
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, ast.List):
                        return {
                            elt.value for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        }
    return None


def validate_services(services_dir: Path) -> tuple[int, int, list[str]]:
    """Validate all service directories. Returns (ok_count, error_count, messages)."""
    ok = 0
    errors = 0
    messages = []
    
    for service_dir in sorted(services_dir.iterdir()):
        if not service_dir.is_dir() or service_dir.name.startswith("_"):
            continue
        
        init_file = service_dir / "__init__.py"
        models_file = service_dir / "models.py"
        service_file = service_dir / "service.py"
        
        # Check __init__.py exists
        if not init_file.exists():
            errors += 1
            messages.append(f"❌ {service_dir.name}: missing __init__.py")
            continue
        
        # Check __all__ exists
        exports = get_all_exports(init_file)
        if exports is None:
            errors += 1
            messages.append(f"❌ {service_dir.name}: no __all__ in __init__.py")
            continue
        
        # Check model classes are exported
        model_names = get_public_names(models_file)
        service_names = get_public_names(service_file)
        all_names = model_names | service_names
        
        missing = all_names - exports
        extra = exports - all_names
        
        if missing:
            errors += 1
            messages.append(f"⚠️  {service_dir.name}: not exported: {', '.join(sorted(missing))}")
        elif extra:
            # Extra exports are a warning, not error
            messages.append(f"ℹ️  {service_dir.name}: extra exports: {', '.join(sorted(extra))}")
            ok += 1
        else:
            ok += 1
    
    return ok, errors, messages


def main() -> int:
    services_dir = Path(__file__).parent.parent / "backend" / "app" / "services"
    if not services_dir.exists():
        print(f"Services directory not found: {services_dir}")
        return 1
    
    print(f"Validating services in {services_dir}...\n")
    ok, errors, messages = validate_services(services_dir)
    
    for msg in messages:
        print(msg)
    
    print(f"\n✅ {ok} services OK")
    if errors:
        print(f"❌ {errors} services with issues")
    
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
