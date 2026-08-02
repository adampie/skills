# Format rules

From the Agent Skills specification at https://agentskills.io/specification.
These are mechanical and enforced by `mise run validate-skills`. Nothing here
is a matter of taste.

## Layout

```
skill-name/
├── SKILL.md          # required
├── scripts/          # optional, executable code
├── references/       # optional, documentation loaded on demand
└── assets/           # optional, templates and static resources
```

Any additional files are permitted. In this repository skills sit under
`plugins/PLUGIN/skills/SKILL/`.

## Frontmatter

| Field | Required | Constraint |
| --- | --- | --- |
| `name` | yes | 1-64 chars, lowercase `a-z0-9` and hyphens |
| `description` | yes | 1-1024 chars, non-empty |
| `license` | no | Licence name, or the name of a bundled licence file |
| `compatibility` | no | 1-500 chars, environment requirements |
| `metadata` | no | Map of string keys to **string** values |
| `allowed-tools` | no | Space-separated tool list. Experimental, support varies |

### name

Must also not start or end with a hyphen, not contain consecutive hyphens, and
**must match the parent directory name**. The directory match is the rule most
often broken when a skill is renamed by editing only the frontmatter.

### description

Must convey both what the skill does and when to use it, with keywords that
help a model recognise a relevant task. See `craft.md`.

### metadata

Values must be strings. A list is invalid YAML for this field:

```yaml
metadata:
  tags: [a, b]        # rejected
  tags: "a, b"        # fine
  version: "1.0"      # quote it, or YAML parses 1.0 as a float
```

## Size budget

Progressive disclosure means three loading stages, and the budget differs at
each:

1. **Metadata**, roughly 100 tokens, loaded at startup for every installed
   skill whether used or not.
2. **Instructions**, the `SKILL.md` body, loaded in full on activation. Keep
   under 5000 tokens and under 500 lines.
3. **Resources**, files under `scripts/`, `references/`, `assets/`, read only
   when the task calls for them.

Because stage 1 is always resident, an overlong `description` taxes every
conversation, including those where the skill is irrelevant.

## File references

Use paths relative to the skill root, one level deep:

```markdown
See [the reference guide](references/REFERENCE.md).
Run scripts/extract.py to pull the tables out.
```

Avoid a reference that points at another reference. Each hop is a decision the
model may get wrong.

## Validating

`scripts/validate_skill.py` enforces the rules on this page, plus the Claude
conventions in `platform.md`. It is what `mise run validate-skills` runs, and
it shares its rule definitions with `scripts/scaffold.py` via `skillspec.py`,
so a skill cannot be created in a state the validator rejects.

The specification publishes a reference validator, `skills-ref`, which its
authors describe as a demonstration not intended for production. It is useful
for cross-checking by hand, but is not a dependency here.

When the published specification changes, update `skillspec.py` and this page
together.
