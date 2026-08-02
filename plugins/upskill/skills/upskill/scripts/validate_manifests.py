#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1", "rfc3986-validator==0.1.1"]
# ///
"""Validate marketplace and plugin manifests against the published schemas.

Checks the JSON Schemas from schemastore.org, the ones editors use, and the
cross-file rules no schema can express: registered sources exist, names match
their directories and marketplace entries, and no plugin directory is left
unregistered. `claude plugin validate` walks only the plugins the marketplace
lists, so an unregistered directory is invisible to it.

The schemas are vendored under assets/schemas/ rather than fetched, because
the schemastore URLs are unversioned and would make each run depend on
whatever is published that day. Refresh them by running, from the skill root:

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

from jsonschema import Draft7Validator, FormatChecker

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "assets" / "schemas"
MARKETPLACE_SCHEMA = SCHEMA_DIR / "claude-code-marketplace.json"
PLUGIN_SCHEMA = SCHEMA_DIR / "claude-code-plugin-manifest.json"

# The published URLs, which manifests should declare so editors validate them
# as they are written.
MARKETPLACE_SCHEMA_URL = "https://www.schemastore.org/claude-code-marketplace.json"
PLUGIN_SCHEMA_URL = "https://www.schemastore.org/claude-code-plugin-manifest.json"

# Both schemas constrain URLs with `format: uri`, which jsonschema treats as an
# annotation unless a checker is supplied, and whose checker in turn only
# registers when rfc3986-validator is installed. Hence the second dependency:
# without it this asserts nothing and the format rules are silently skipped.
FORMAT_CHECKER = FormatChecker()


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
    validator = Draft7Validator(schema, format_checker=FORMAT_CHECKER)
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
    if not isinstance(marketplace, dict):
        # Valid JSON that is not an object parses fine and then breaks every
        # lookup below, so stop here rather than raising out of the validator.
        return [
            f".claude-plugin/marketplace.json: root must be an object, got "
            f"{type(marketplace).__name__}"
        ], []

    marketplace_schema = json.loads(MARKETPLACE_SCHEMA.read_text())
    for error in schema_errors(marketplace, marketplace_schema):
        errors.append(f".claude-plugin/marketplace.json: {error}")

    if marketplace.get("$schema") != MARKETPLACE_SCHEMA_URL:
        warnings.append(
            f".claude-plugin/marketplace.json: $schema should be "
            f"{MARKETPLACE_SCHEMA_URL}"
        )

    # Sources resolve against the marketplace root unless metadata.pluginRoot
    # moves the base.
    metadata = marketplace.get("metadata")
    plugin_root = metadata.get("pluginRoot") if isinstance(metadata, dict) else None
    base = (repo / plugin_root).resolve() if isinstance(plugin_root, str) else repo

    plugin_schema = json.loads(PLUGIN_SCHEMA.read_text())
    seen: set[str] = set()
    registered_dirs: set[Path] = set()
    for entry in marketplace.get("plugins") or []:
        if not isinstance(entry, dict):
            continue  # Already reported by the schema check.
        name, source = entry.get("name"), entry.get("source")
        if not isinstance(name, str):
            continue
        if name in seen:
            errors.append(f"marketplace entry {name!r} is registered more than once")
            continue
        seen.add(name)
        if not isinstance(source, str):
            # An npm or git source has no directory in this repository.
            continue

        plugin_dir = (base / source).resolve()
        if not plugin_dir.is_relative_to(repo):
            errors.append(
                f"marketplace entry {name!r}: source {source} resolves outside "
                "the repository"
            )
            continue
        registered_dirs.add(plugin_dir)
        if not plugin_dir.is_dir():
            errors.append(f"marketplace entry {name!r}: source {source} does not exist")
            continue
        if plugin_dir.name != name:
            errors.append(
                f"marketplace entry {name!r}: directory {plugin_dir.name!r} does "
                "not match"
            )

        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        if not manifest_path.is_file():
            # strict: false means the marketplace entry carries the manifest,
            # which the marketplace schema has already checked.
            if entry.get("strict", True):
                errors.append(f"{source}: no .claude-plugin/plugin.json")
            continue

        rel = manifest_path.relative_to(repo)
        manifest, load_errors = load_json(manifest_path)
        if load_errors:
            errors.extend(f"{rel}: {e}" for e in load_errors)
            continue
        if not isinstance(manifest, dict):
            errors.append(
                f"{rel}: root must be an object, got {type(manifest).__name__}"
            )
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
        if "version" not in manifest:
            warnings.append(f"{rel}: no version, so the plugin cannot be tagged")

    # Compare directories rather than names, so a marketplace that moves its
    # base or sources a plugin remotely is judged on what it actually points at.
    scan_dir = base if base != repo else repo / "plugins"
    if scan_dir.is_dir():
        for child in sorted(scan_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if child.resolve() not in registered_dirs:
                errors.append(
                    f"{child.relative_to(repo)} is not registered in marketplace.json"
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
