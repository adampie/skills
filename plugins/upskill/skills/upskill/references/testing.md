# Testing a skill

Three checks, in order of how often they catch something. Like `craft.md`, this
is calibrated to current model behaviour and should be revised when that
changes.

## 1. Triggering

The most common failure by a wide margin. Write the cases before the skill, so
they describe intent rather than whatever was built.

```
Should trigger:
- "help me add a skill for release notes"     # direct
- "I want to package this workflow up"        # paraphrased, no keywords
- "scaffold a new plugin in this repo"        # adjacent vocabulary

Should not trigger:
- "what's the weather in San Francisco?"      # unrelated
- "write a Python script to parse this CSV"   # plausible but wrong
```

Include the near-misses. Unrelated queries are easy; the useful signal comes
from requests that sit next to the skill's territory without belonging to it.

Run each in a fresh conversation. A skill already loaded stays loaded, so
reusing a session tests nothing.

Target roughly nine out of ten on the should-trigger set, with no false
positives on the should-not set. Fixes are in `craft.md`.

## 2. Functional

Does the skill produce a correct result once loaded?

```
Given:  a new skill named release-notes in plugin publishing
When:   the skill runs end to end
Then:   plugins/publishing/skills/release-notes/SKILL.md exists
        the plugin is registered in marketplace.json
        mise run validate-skills passes
        mise run validate passes
```

Cover the edge cases the trial run exposed, plus at least one deliberate
failure, such as a name that violates the specification, to confirm the error
path is reachable and the message is intelligible.

## 3. Baseline comparison

Worth doing once, to establish the skill earns its context cost. Run the same
request with the skill disabled and enabled, and compare turns to completion,
corrections needed, and failed tool calls.

If the skill does not measurably beat the baseline, the problem is usually
that it encodes what the model already knew. Cut it back to the parts that
carry information the model lacks: your conventions, your repository layout,
your failure modes.

## Iterating

Skills are maintained, not finished. When one misbehaves in real use, bring
the transcript back rather than guessing at a fix, and add the case to the
triggering set so the same regression is caught next time.

Signals worth acting on:

- Users manually enabling the skill: the description is under-specified.
- Users disabling it: it is claiming work that is not its own.
- Repeated corrections mid-task: the instructions are ambiguous, or a step
  that needs determinism is still written as prose.
