#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Validate skill directories against the Agent Skills format rules.

Run with `uv run`, which resolves the pinned dependency above. YAML parsing is
delegated to PyYAML rather than hand-rolled, because a parser that is more
permissive than a real one would pass skills that agents then reject.

Usage:
    uv run validate_skill.py PATH [PATH ...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from skillspec import (
    BODY_MAX_LINES,
    COMPATIBILITY_MAX,
    check_description,
    check_name,
)

KNOWN_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def split_frontmatter(text: str) -> tuple[str | None, str, list[str]]:
    """Return (frontmatter, body, errors)."""
    if not text.startswith("---\n"):
        return None, "", ["SKILL.md must begin with a --- frontmatter delimiter"]
    rest = text[4:]
    end = rest.find("\n---\n")
    if end == -1:
        if rest.endswith("\n---"):
            return rest[: -len("\n---")], "", []
        return None, "", ["frontmatter is not closed by a --- delimiter"]
    return rest[:end], rest[end + len("\n---\n") :], []


def validate(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one skill directory."""
    errors: list[str] = []
    warnings: list[str] = []

    if not path.is_dir():
        return [f"{path} is not a directory"], []

    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        # Catches skill.md and SKILL.MD on case-insensitive filesystems.
        actual = [p.name for p in path.iterdir() if p.name.lower() == "skill.md"]
        if actual:
            return [f"file must be named exactly SKILL.md, found {actual[0]}"], []
        return ["no SKILL.md found"], []
    if skill_file.name not in {p.name for p in path.iterdir()}:
        errors.append("file must be named exactly SKILL.md")

    front, body, split_errors = split_frontmatter(skill_file.read_text())
    if split_errors:
        return split_errors, []

    try:
        data = yaml.safe_load(front)
    except yaml.YAMLError as exc:
        return [f"invalid YAML in frontmatter: {exc}"], []

    if not isinstance(data, dict):
        return ["frontmatter must be a YAML mapping"], []

    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append("field 'name' is required and must be a non-empty string")
    else:
        errors.extend(check_name("skill", name))
        if name != path.name:
            errors.append(
                f"directory name {path.name!r} must match skill name {name!r}"
            )

    if "description" not in data:
        errors.append("field 'description' is required")
    else:
        errors.extend(check_description(data["description"]))

    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append("field 'compatibility' must be a non-empty string")
        elif len(compatibility) > COMPATIBILITY_MAX:
            errors.append(
                f"field 'compatibility' must be at most {COMPATIBILITY_MAX} "
                f"characters, got {len(compatibility)}"
            )

    metadata = data.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            errors.append("field 'metadata' must be a mapping")
        else:
            for key, value in metadata.items():
                if not isinstance(value, str):
                    errors.append(
                        f"metadata.{key} must be a string, got "
                        f"{type(value).__name__}; quote it"
                    )

    for field in ("license", "allowed-tools"):
        if field in data and not isinstance(data[field], str):
            errors.append(f"field {field!r} must be a string")

    for key in data:
        if key not in KNOWN_FIELDS:
            warnings.append(f"unrecognised frontmatter field {key!r}")

    if "<" in front or ">" in front:
        errors.append("frontmatter must not contain angle brackets (Claude)")

    lines = len(body.splitlines())
    if lines > BODY_MAX_LINES:
        warnings.append(
            f"body is {lines} lines, over the {BODY_MAX_LINES}-line guideline; "
            "move detail into references/"
        )

    return errors, warnings


def main() -> int:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        print(__doc__, file=sys.stderr)
        return 2

    failed = False
    for path in paths:
        errors, warnings = validate(path)
        for warning in warnings:
            print(f"warning: {path}: {warning}")
        if errors:
            failed = True
            print(f"FAIL {path}", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
        else:
            print(f"ok   {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
