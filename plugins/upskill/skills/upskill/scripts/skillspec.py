"""Agent Skills format rules, shared by the scaffolder and the validator.

Kept in one module so a rule cannot be enforced at creation but not at
validation, or the reverse. Standard library only: these are string and length
checks, and the scaffolder must run without provisioning an environment.

Rules marked CLAUDE are Anthropic's rather than the specification's. They are
enforced because skills here target Claude, and are separated so they can be
dropped if that stops being true. See references/platform.md.
"""

from __future__ import annotations

import re

# Lowercase alphanumerics with single interior hyphens. Rejects leading,
# trailing, and consecutive hyphens by construction.
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500

# CLAUDE: reserved, refused at upload time.
RESERVED_SUBSTRINGS = ("claude", "anthropic")

# Recommended ceiling for the body, which loads in full on activation.
BODY_MAX_LINES = 500


def check_name(kind: str, value: str) -> list[str]:
    errors = []
    if not 1 <= len(value) <= NAME_MAX:
        errors.append(f"{kind} name must be 1-{NAME_MAX} characters, got {len(value)}")
    elif not NAME_PATTERN.match(value):
        errors.append(
            f"{kind} name {value!r} must be lowercase letters, digits, and single "
            "hyphens, with no leading or trailing hyphen"
        )
    for reserved in RESERVED_SUBSTRINGS:
        if reserved in value:
            errors.append(
                f"{kind} name {value!r} contains the reserved word {reserved!r} (Claude)"
            )
    return errors


def check_description(value: str) -> list[str]:
    errors = []
    if not isinstance(value, str) or not value.strip():
        return ["description must be a non-empty string"]
    if len(value) > DESCRIPTION_MAX:
        errors.append(
            f"description must be at most {DESCRIPTION_MAX} characters, got {len(value)}"
        )
    if "<" in value or ">" in value:
        # Frontmatter is injected into the system prompt, so markup is refused.
        errors.append("description must not contain angle brackets (Claude)")
    return errors
