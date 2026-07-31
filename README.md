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

Create `plugins/<name>/.claude-plugin/plugin.json` with `$schema`, `name`
matching the directory, `version`, and `description`, add the skills under
`skills/<skill>/SKILL.md`, then register the plugin in `marketplace.json`.

Release with `claude plugin tag`, which checks that `plugin.json` and the
marketplace entry agree before creating the tag.

## Validation

Tooling is pinned in `mise.toml`. Run `mise trust` once, then:

```sh
mise run validate    # marketplace manifest and every plugin it registers
mise run zizmor      # audit the GitHub Actions workflows
```

CI runs the same tasks, so a green local run means a green build. `validate`
runs on every push and pull request; `zizmor` runs only when a workflow or
`mise.toml` changes. `validate` fails on an empty marketplace, so the first
plugin has to be merged past it.

## Licence

MIT, see [LICENSE](LICENSE).
