# Claude-specific behaviour

Rules that hold for Claude but are not in the Agent Skills specification. They
come from Anthropic's skill-authoring guidance rather than the standard, so
treat them as conventions of one implementation.

Where `scripts/validate_skill.py` enforces one of these, it labels the failure
`(Claude)` to distinguish it from a specification violation.

Quarantined in this file deliberately: when Claude changes, or when a skill is
targeted at another agent, this is the file to revisit. The rules in `spec.md`
are not affected.

## Frontmatter restrictions

- **No angle brackets** (`<` or `>`) anywhere in frontmatter. Frontmatter is
  injected into the system prompt, so markup there is an injection vector.
  This is an upload-time restriction, not a format rule, but honouring it costs
  nothing and keeps skills portable to Claude.ai.
- **Reserved names.** Skills named with `claude` or `anthropic` are refused.

## Repository conventions

- `SKILL.md` must be spelled exactly that way, uppercase and all. `skill.md`
  and `SKILL.MD` are not recognised.
- No `README.md` inside a skill directory. The specification permits it, but
  Anthropic's tooling expects documentation to live in `SKILL.md` or
  `references/`. A repository-level README for human readers is expected and
  separate.

## Scale

Response quality degrades somewhere past roughly 20 to 50 skills enabled at
once, because every installed skill's metadata sits in the system prompt. If a
marketplace grows past that, group related skills into plugins users can enable
selectively rather than shipping many independent ones.

## Distribution

Beyond this repository's plugin marketplace, skills can be zipped and uploaded
through Claude.ai settings, deployed organisation-wide by an administrator, or
attached to API requests via `container.skills`, which requires the code
execution beta. The plugin marketplace this repository uses is the path that
needs no manual upload step.
