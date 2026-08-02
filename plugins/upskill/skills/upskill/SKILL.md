---
name: upskill
description: Creates, validates, and reviews Agent Skills inside a marketplace repository. Scaffolds the plugin and SKILL.md, registers the plugin in marketplace.json, and checks the result against the Agent Skills specification. Use when the user asks to create a skill, write a new skill, add a skill to the marketplace, scaffold a plugin, or review, improve, or fix an existing SKILL.md.
license: MIT
compatibility: Requires mise and a repository containing .claude-plugin/marketplace.json
metadata:
  author: adampie
  version: "0.1.0"
---

# Upskill

Authors Agent Skills in a marketplace repository: interview, scaffold, write,
validate, test.

Skills in this repository live at `plugins/PLUGIN/skills/SKILL/SKILL.md`. A
plugin may hold several related skills. The marketplace manifest at
`.claude-plugin/marketplace.json` registers every plugin.

## Step 0: do the task once by hand

**Do not skip this.** Before writing a skill, complete the target task in a
normal conversation until the result is good, then extract what worked.

Writing a skill first and testing it afterwards produces plausible instructions
that fail in practice. A transcript of one successful run tells you which steps
actually needed spelling out and which the model handled unaided.

If the user has not done a trial run, say so and offer to do it now. Proceed
without one only if they ask.

## Step 1: gather

Collect before writing anything:

- **Use cases.** Two or three concrete tasks, each with a trigger, the steps,
  and the finished result. One vague use case is not enough to write a usable
  description.
- **Trigger phrases.** The words a user would actually type. These go in the
  `description` field and determine whether the skill ever loads.
- **Anti-triggers.** Nearby tasks this skill should *not* claim.
- **Tools needed.** Built-in, MCP, or bundled scripts.
- **Plugin and skill names.** Both kebab-case. Reuse an existing plugin if the
  skill is a sibling of one already there; otherwise a new plugin is created.

Read `references/craft.md` before writing the description. It is the field that
decides whether the skill is ever used.

## Step 2: scaffold

```bash
python3 scripts/scaffold.py --plugin PLUGIN --skill SKILL --description "..."
```

The script finds the repository root, validates the names, writes the plugin
manifest and a SKILL.md skeleton, and registers the plugin in
`marketplace.json`. It refuses to overwrite an existing skill.

Run it from anywhere inside the target repository. It works unchanged in any
repo laid out this way, so it serves both the public and private marketplaces.

## Step 3: write the instructions

Replace the skeleton body. Structure that holds up:

1. **What this does** in a sentence.
2. **Steps**, numbered, imperative, each with an observable result.
3. **Examples**, at least one full input-to-output walkthrough.
4. **Failure modes**, the errors seen in the trial run and the fix for each.

Constraints worth respecting, in full in `references/spec.md`:

- Keep `SKILL.md` under 500 lines and roughly 5000 tokens. It loads in full.
- Move detail into `references/`, which loads only when needed.
- Keep references one level deep. Avoid chains of files pointing at files.
- Prefer a script over prose for anything that must happen exactly right. Code
  is deterministic; instructions are interpreted.

## Step 4: validate

```bash
mise run validate-skills     # every SKILL.md against the format rules
mise run validate-manifests  # manifests against the published JSON Schemas
mise run validate            # claude plugin validate
```

All three must pass before the skill is committed, and they do not overlap.
`claude plugin validate` never opens SKILL.md and applies its own rules rather
than the schemas, so the other two exist to cover what it does not.

To check one skill directly, without mise:

```bash
uv run scripts/validate_skill.py path/to/skill
```

## Step 5: test

Confirm the skill loads when it should and not otherwise. `references/testing.md`
has the procedure and the fixes for over- and under-triggering.

Triggering is the failure mode that matters most. A skill that never loads is
worth nothing regardless of how good its instructions are.

## Reviewing an existing skill

Given a skill to review, work in this order and stop at the first real problem:

1. Run `mise run validate-skills` for mechanical errors.
2. Judge the `description` against `references/craft.md`. Most complaints about
   a skill "not working" are triggering problems.
3. Check size and structure against Step 3.
4. Ask which instructions the model ignored in practice, then look for the
   causes in `references/craft.md`.

## Reference files

Read on demand, not upfront. Split by how quickly the content dates, so a
refresh touches one file rather than the whole skill.

| File | Contents | Ages |
| --- | --- | --- |
| `references/spec.md` | Format rules: fields, limits, naming, layout | Slowly, tracks the published specification |
| `references/platform.md` | Claude-specific behaviour beyond the specification | Moderately |
| `references/craft.md` | Writing descriptions and instructions models follow | Quickly, tuned to current models |
| `references/testing.md` | Triggering, functional, and baseline testing | Quickly |

When a new model makes advice here wrong, `craft.md` and `testing.md` are
where the damage is. Rewrite those; leave `spec.md` alone unless the published
specification itself changed.

## Scripts

| File | Purpose |
| --- | --- |
| `scripts/scaffold.py` | Creates the plugin and skill, registers the plugin |
| `scripts/validate_skill.py` | Checks skill directories against the format rules |
| `scripts/validate_manifests.py` | Checks manifests against the published JSON Schemas |
| `scripts/skillspec.py` | The skill rules, shared by the scaffolder and validator |
| `assets/schemas/` | Vendored copies of the two manifest schemas |

The skill rules live in one module so that creation and validation cannot
disagree. Changing a limit or a naming rule means editing `skillspec.py` and
`spec.md` together, and nothing else.

Manifests must declare `$schema` so editors validate them while they are being
written. `scaffold.py` emits it, and `validate_manifests.py` warns when it is
missing or wrong.
