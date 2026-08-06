#!/usr/bin/env python3
"""Scaffold a skill into a marketplace repository.

Name and description rules are enforced here rather than left to the model, so
a malformed skill fails before any files are written. Standard library only,
so it runs without provisioning a Python environment first.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from skillspec import check_description, check_name

SKELETON = """\
# {title}

One sentence on what this does.

## Steps

1. First step, phrased as an instruction. State what success looks like.
2. Second step.

## Example

User says: "..."

Actions:
1. ...

Result: ...

## Failure modes

**Error: ...**
Cause: ...
Fix: ...
"""


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def fail_all(errors: list[str]) -> None:
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        sys.exit(1)


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".claude-plugin" / "marketplace.json").is_file():
            return candidate
    fail(f"no .claude-plugin/marketplace.json found at or above {start}")
    raise AssertionError("unreachable")


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
        raise AssertionError("unreachable")


def write_json(path: Path, data: dict) -> None:
    """Two-space indent and a trailing newline, matching the existing manifests."""
    path.write_text(json.dumps(data, indent=2) + "\n")


def yaml_string(value: str) -> str:
    """Quote a value for YAML.

    YAML 1.2 is a superset of JSON, so a JSON string is a valid double-quoted
    YAML scalar with the escaping already handled.
    """
    return json.dumps(value)


def ensure_plugin(repo: Path, plugin_dir: Path, plugin: str, marketplace: dict) -> bool:
    """Write the plugin manifest if it is missing. Returns True if it wrote one."""
    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if manifest_path.exists():
        return False

    owner = marketplace.get("owner")
    owner = owner if isinstance(owner, dict) else {}
    manifest = {
        "$schema": "https://www.schemastore.org/claude-code-plugin-manifest.json",
        "name": plugin,
        "version": "0.1.0",
        "description": f"TODO: describe the {plugin} plugin.",
    }
    if owner.get("name"):
        author = {"name": owner["name"]}
        if owner.get("url"):
            author["url"] = owner["url"]
        manifest["author"] = author

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    print(f"created {manifest_path.relative_to(repo)}")
    return True


def marketplace_entry(marketplace: dict, plugin: str) -> dict | None:
    return next(
        (
            entry
            for entry in marketplace.get("plugins") or []
            if isinstance(entry, dict) and entry.get("name") == plugin
        ),
        None,
    )


def register_plugin(repo: Path, plugin: str, marketplace: dict, path: Path) -> None:
    plugins = marketplace.setdefault("plugins", [])
    if marketplace_entry(marketplace, plugin) is not None:
        return
    plugins.append({"name": plugin, "source": f"./plugins/{plugin}"})
    plugins.sort(key=lambda entry: entry.get("name", "") if isinstance(entry, dict) else "")
    write_json(path, marketplace)
    print(f"registered {plugin} in {path.relative_to(repo)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plugin", required=True, help="plugin name, kebab-case")
    parser.add_argument("--skill", required=True, help="skill name, kebab-case")
    parser.add_argument(
        "--description",
        required=True,
        help="what the skill does and when to use it, including trigger phrases",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help="path inside the target repository (default: current directory)",
    )
    args = parser.parse_args()

    # Everything that can refuse the run happens before the first write, so a
    # refusal leaves the repository untouched.
    fail_all(
        check_name("plugin", args.plugin)
        + check_name("skill", args.skill)
        + check_description(args.description)
    )

    repo = find_repo_root(args.repo.resolve())
    marketplace_path = repo / ".claude-plugin" / "marketplace.json"
    marketplace = read_json(marketplace_path)

    plugin_dir = repo / "plugins" / args.plugin
    skill_dir = plugin_dir / "skills" / args.skill
    if skill_dir.exists():
        fail(f"{skill_dir.relative_to(repo)} already exists; refusing to overwrite")
    entry = marketplace_entry(marketplace, args.plugin)
    source = f"./plugins/{args.plugin}"
    if entry is not None and entry.get("source") != source:
        # The marketplace fetches this plugin elsewhere, so a skill written
        # under plugins/ would be unreachable.
        fail(
            f"{args.plugin} is registered with source {entry.get('source')!r}, "
            f"not {source!r}"
        )

    created_plugin = ensure_plugin(repo, plugin_dir, args.plugin, marketplace)
    skill_dir.mkdir(parents=True)
    title = args.skill.replace("-", " ").capitalize()
    frontmatter = (
        "---\n"
        f"name: {args.skill}\n"
        f"description: {yaml_string(args.description)}\n"
        "---\n\n"
    )
    (skill_dir / "SKILL.md").write_text(frontmatter + SKELETON.format(title=title))
    print(f"created {(skill_dir / 'SKILL.md').relative_to(repo)}")

    register_plugin(repo, args.plugin, marketplace, marketplace_path)

    if created_plugin:
        rel = (plugin_dir / ".claude-plugin" / "plugin.json").relative_to(repo)
        print(f"\nnext: replace the TODO description in {rel}")
        print("then write the body, then run")
    else:
        print("\nnext: write the body, then run")
    print("  mise run validate-skills")
    print("  mise run validate-manifests")
    print("  mise run validate")


if __name__ == "__main__":
    main()
