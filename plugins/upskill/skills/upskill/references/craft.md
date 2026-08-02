# Writing skills models follow

Heuristics, not rules. They describe how current models behave and will drift
as models improve. If advice here contradicts what you observe in a trial run,
trust the trial run and correct this file.

## The description field

The single highest-leverage part of a skill. With `name`, it is all the model
sees when deciding whether to load anything else, so a good body behind a vague
description is wasted work.

Cover three things: what it does, when to use it, and the phrases a user would
say.

```yaml
# Good: names the artefacts, the triggers, and the file types
description: Analyses Figma design files and generates developer handoff
  documentation. Use when the user uploads .fig files or asks for design specs,
  component documentation, or design-to-code handoff.
---
# Bad: no trigger, no scope
description: Helps with projects.
---
# Bad: describes the implementation rather than the user's request
description: Implements the Project entity model with hierarchical
  relationships.
```

Write triggers in the user's vocabulary, not the domain's. Users ask to "clean
up this spreadsheet", not to "perform tabular normalisation".

## Fixing triggering

**Does not load when it should.** The description is too abstract or missing
vocabulary. Add the literal phrases users type, including technical terms and
product names, and name relevant file extensions.

**Loads when it should not.** Add explicit scope limits and point at the
alternative:

```yaml
description: Advanced statistical analysis of CSV files, including regression
  and clustering. Do not use for simple data exploration or charting, which the
  csv-summary skill covers.
```

**To see what the model thinks the skill is for,** ask it: "when would you use
the NAME skill?" It answers from the name and description, so whatever it fails
to mention is what they fail to say.

## Instructions

- **Concise beats complete.** Long instructions get skimmed. Detail belongs in
  `references/`, which costs nothing until read.
- **Critical constraints go near the top.** Content in the middle of a long
  body carries least weight.
- **Be specific about the checks.** Replace "validate the input properly" with
  the actual conditions: non-empty name, at least one assignee, start date not
  in the past.
- **Give observable results.** Each step should say what success looks like, so
  the model can tell whether it worked rather than assuming it did.
- **Prefer a script for anything that must be exact.** Validation, parsing, and
  format conversion belong in `scripts/`. Code produces the same answer every
  run; prose does not.

## Diminishing returns

Exhortations such as "take your time" or "do not skip steps" are weak inside
`SKILL.md`. They work better in the user's own prompt, and each model
generation needs them less. Reach for a script or a validation gate instead of
stronger wording.

Repeating a key instruction in two places is occasionally worth it for a
constraint that is genuinely load-bearing. It is a patch for a body that has
grown too long, so treat a second repetition as a signal to split the file.
