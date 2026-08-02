# skills

A public marketplace of [Claude Code](https://code.claude.com/docs/en/overview)
plugins and [Agent Skills](https://agentskills.io/specification).

```sh
claude plugin marketplace add adampie/skills
claude plugin install <plugin>@adampie
```

## Layout

```
.claude-plugin/marketplace.json    # every plugin is registered here
plugins/<plugin>/
  .claude-plugin/plugin.json       # plugin manifest
  skills/<skill>/SKILL.md          # one directory per skill
  agents/<agent>.md                # optional subagents
```

## Adding a plugin

The `upskill` skill does this for you: ask Claude to create a skill and it
scaffolds the plugin, writes the `SKILL.md`, and registers the plugin here.

By hand, create `plugins/<name>/.claude-plugin/plugin.json` with `$schema`,
`name` matching the directory, `version`, and `description`, add the skills
under `skills/<skill>/SKILL.md`, then register the plugin in
`marketplace.json`.

Release with `claude plugin tag`, which checks that `plugin.json` and the
marketplace entry agree before creating the tag.

## Validation

Tooling is pinned in `mise.toml`. Run `mise trust` once, then:

```sh
mise run validate            # marketplace manifest and every plugin it registers
mise run validate-manifests  # the same manifests against the published schemas
mise run validate-skills     # every SKILL.md against the Agent Skills spec
mise run zizmor              # audit the GitHub Actions workflows
```

The three validate tasks check different things:

- `validate` runs `claude plugin validate`, which applies its own rules and
  never opens `SKILL.md`.
- `validate-manifests` checks the manifests against the
  [marketplace](https://www.schemastore.org/claude-code-marketplace.json) and
  [plugin](https://www.schemastore.org/claude-code-plugin-manifest.json)
  JSON Schemas, which are what editors use and are not the same rules. It also
  catches a plugin directory that was never registered, which nothing else
  looks for.
- `validate-skills` checks each skill against the Agent Skills format rules.

The last two run the checkers bundled with the `upskill` skill. Skill rules are
shared with the scaffolder, so a generated skill cannot fail validation on
creation. The schemas are vendored under the skill's `assets/schemas/` because
the schemastore URLs are unversioned; refresh them with the commands in
`scripts/validate_manifests.py`.

CI runs the same tasks, so a green local run means a green build. Both
validate tasks run on every push and pull request; `zizmor` runs only when a
workflow or `mise.toml` changes. `validate` fails on an empty marketplace, so
the first plugin has to be merged past it.

## Licence

MIT, see [LICENSE](LICENSE).
