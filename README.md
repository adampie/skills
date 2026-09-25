# skills

A public marketplace of [Claude Code](https://code.claude.com/docs/en/overview)
plugins and [Agent Skills](https://agentskills.io/specification).

```sh
claude plugin marketplace add adampie/skills
claude plugin install <plugin>@adampie
```

## Plugins

| Plugin | Skill | What it does |
| --- | --- | --- |
| [`fact-check`](plugins/fact-check) | [`fact-check:fact-check`](plugins/fact-check/skills/fact-check/SKILL.md) | Extracts the factual claims from a document, a statement, or Claude's own earlier output, verifies each by web search or by tracing the code that decides the behaviour, and reports a verdict, correction and citation per claim, worst first. |
| [`pr`](plugins/pr) | [`pr:commit`](plugins/pr/skills/commit/SKILL.md) | Commits a working tree onto one branch, or splits it into an ordered chain of branches when the change needs layers. Does not push. |
| | [`pr:submit`](plugins/pr/skills/submit/SKILL.md) | Pushes and opens or updates the draft pull requests: one for a branch, or one per layer, each based on the layer below. |
| | [`pr:sync`](plugins/pr/skills/sync/SKILL.md) | Rebases a branch or a stack as trunk moves, absorbs merged layers, and lands a change in a layer below the current one. |
| [`upskill`](plugins/upskill) | [`upskill:upskill`](plugins/upskill/skills/upskill/SKILL.md) | Scaffolds a plugin and its `SKILL.md`, registers it in `marketplace.json`, and checks the result against the Agent Skills specification. |

The `pr` skills work on a single branch with plain git and `gh`. Stacked pull
requests additionally need the [`github/gh-stack`](https://github.com/github/gh-stack)
CLI extension. Commit messages and pull request bodies follow the rules in
[`plugins/pr/references`](plugins/pr/references), which every skill in the
plugin reads, so the two flows read the same.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository layout, how to add a
plugin, and the validation tasks.

## Licence

MIT, see [LICENSE](LICENSE).
