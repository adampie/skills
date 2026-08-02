#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1"]
# ///
"""Validate marketplace and plugin manifests against the published schemas.

`claude plugin validate` applies its own rules, which are not the schemas
editors use, so a manifest can satisfy one and not the other. This checks the
JSON Schemas from schemastore.org directly.

The schemas are vendored under assets/schemas/ rather than fetched, because
the schemastore URLs are unversioned and would make each run depend on
whatever is published that day. Refresh them with:

    curl -sSo assets/schemas/claude-code-marketplace.json \\
        https://www.schemastore.org/claude-code-marketplace.json
    curl -sSo assets/schemas/claude-code-plugin-manifest.json \\
        https://www.schemastore.org/claude-code-plugin-manifest.json

Usage:
    uv run validate_manifests.py [REPO_ROOT]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "assets" / "schemas"
MARKETPLACE_SCHEMA = SCHEMA_DIR / "claude-code-marketplace.json"
PLUGIN_SCHEMA = SCHEMA_DIR / "claude-code-plugin-manifest.json"

# The published URLs, which manifests should declare so editors validate them
# as they are written.
MARKETPLACE_SCHEMA_URL = "https://www.schemastore.org/claude-code-marketplace.json"
PLUGIN_SCHEMA_URL = "https://www.schemastore.org/claude-code-plugin-manifest.json"


def find_repo_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / ".claude-plugin" / "marketplace.json").is_file():
            return candidate
    return None


def load_json(path: Path) -> tuple[dict | None, list[str]]:
    try:
        return json.loads(path.read_text()), []
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON: {exc}"]


def schema_errors(instance: dict, schema: dict) -> list[str]:
    validator = Draft7Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        location = ".".join(str(part) for part in error.path) or "(root)"
        errors.append(f"{location}: {error.message}")
    return errors


def check(repo: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    marketplace_path = repo / ".claude-plugin" / "marketplace.json"
    marketplace, load_errors = load_json(marketplace_path)
    if load_errors:
        return [f".claude-plugin/marketplace.json: {e}" for e in load_errors], []

    marketplace_schema = json.loads(MARKETPLACE_SCHEMA.read_text())
    for error in schema_errors(marketplace, marketplace_schema):
        errors.append(f".claude-plugin/marketplace.json: {error}")

    if marketplace.get("$schema") != MARKETPLACE_SCHEMA_URL:
        warnings.append(
            f".claude-plugin/marketplace.json: $schema should be "
            f"{MARKETPLACE_SCHEMA_URL}"
        )

    plugin_schema = json.loads(PLUGIN_SCHEMA.read_text())
    registered = {}
    for entry in marketplace.get("plugins", []):
        name, source = entry.get("name"), entry.get("source")
        if not isinstance(name, str) or not isinstance(source, str):
            # Already reported by the schema check; nothing further to verify.
            continue
        registered[name] = source

        plugin_dir = (repo / source).resolve()
        if not plugin_dir.is_dir():
            errors.append(f"marketplace entry {name!r}: source {source} does not exist")
            continue

        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest_path.is_file():
            errors.append(f"{source}: no .claude-plugin/plugin.json")
            continue

        rel = manifest_path.relative_to(repo)
        manifest, load_errors = load_json(manifest_path)
        if load_errors:
            errors.extend(f"{rel}: {e}" for e in load_errors)
            continue

        for error in schema_errors(manifest, plugin_schema):
            errors.append(f"{rel}: {error}")

        if manifest.get("$schema") != PLUGIN_SCHEMA_URL:
            warnings.append(f"{rel}: $schema should be {PLUGIN_SCHEMA_URL}")

        # Cross-manifest consistency, which neither schema can express.
        if manifest.get("name") != name:
            errors.append(
                f"{rel}: name {manifest.get('name')!r} does not match marketplace "
                f"entry {name!r}"
            )
        if plugin_dir.name != name:
            errors.append(f"{rel}: directory {plugin_dir.name!r} does not match name {name!r}")
        if "version" not in manifest:
            warnings.append(f"{rel}: no version, so the plugin cannot be tagged")

    plugins_dir = repo / "plugins"
    if plugins_dir.is_dir():
        for child in sorted(plugins_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if child.name not in registered:
                errors.append(
                    f"plugins/{child.name} is not registered in marketplace.json"
                )

    return errors, warnings


def main() -> int:
    start = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    repo = find_repo_root(start)
    if repo is None:
        print(
            f"error: no .claude-plugin/marketplace.json found at or above {start}",
            file=sys.stderr,
        )
        return 2

    errors, warnings = check(repo)
    for warning in warnings:
        print(f"warning: {warning}")
    if errors:
        print(f"FAIL {repo}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    print(f"ok   manifests in {repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
