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
| [`stack`](plugins/stack) | [`stack:commit`](plugins/stack/skills/commit/SKILL.md) | Splits a working tree into an ordered chain of branches, one layer per branch. Does not push. |
| | [`stack:submit`](plugins/stack/skills/submit/SKILL.md) | Pushes the stack and opens or updates one draft pull request per layer, each based on the layer below. |
| | [`stack:sync`](plugins/stack/skills/sync/SKILL.md) | Rebases the stack as trunk moves, absorbs merged layers, and lands a change in a layer below the current one. |
| [`upskill`](plugins/upskill) | [`upskill:upskill`](plugins/upskill/skills/upskill/SKILL.md) | Scaffolds a plugin and its `SKILL.md`, registers it in `marketplace.json`, and checks the result against the Agent Skills specification. |

The `stack` skills wrap the [`github/gh-stack`](https://github.com/github/gh-stack)
CLI extension, which they expect to be installed.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository layout, how to add a
plugin, and the validation tasks.

## Licence

MIT, see [LICENSE](LICENSE).
