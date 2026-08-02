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

- **No XML tags in `name` or `description`.** Frontmatter is injected into the
  system prompt, so markup there is an injection vector. `validate_skill.py`
  goes further and rejects any `<` or `>` anywhere in frontmatter: a superset
  of the documented rule that needs no tag parser and costs nothing to honour.
- **Reserved names.** `name` may not contain `claude` or `anthropic`.

## Repository conventions

- `SKILL.md` must be spelled exactly that way, uppercase and all. `skill.md`
  and `SKILL.MD` are not recognised.
- No `README.md` inside a skill directory. The specification permits any extra
  files, but a second document competes with `SKILL.md` for the reader and
  neither is loaded by name. Documentation goes in `SKILL.md` or `references/`.
  The repository-level README for human readers is separate.

## Scale

Every enabled skill's metadata sits in the system prompt for the whole
conversation, and the model chooses between skills on `description` alone.
Anthropic's guidance assumes selection across 100+ skills, so the binding
constraint is descriptions that distinguish themselves rather than a count.
Group related skills into plugins users can enable selectively.

## Distribution

Beyond this repository's plugin marketplace, skills can be zipped and uploaded
through Claude.ai settings, deployed organisation-wide by an administrator, or
attached to API requests via `container.skills`, which requires the code
execution beta. The plugin marketplace this repository uses is the path that
needs no manual upload step.
